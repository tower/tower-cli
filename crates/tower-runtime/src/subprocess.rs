//! Subprocess execution backend

use crate::errors::Error;
use crate::execution::{
    BackendCapabilities, CacheBackend, ExecutionBackend, ExecutionHandle, ExecutionSpec,
    ServiceEndpoint,
};
use crate::local::LocalApp;
use crate::{App, OutputReceiver, StartOptions, Status};

use async_trait::async_trait;
use std::path::PathBuf;
use std::sync::Arc;
use tmpdir::TmpDir;
use tokio::fs::File;
use tokio::io::AsyncWriteExt;
use tokio::sync::Mutex;
use tokio::time::Duration;
use tower_package::Package;

/// SubprocessBackend executes apps as a subprocess
pub struct SubprocessBackend {
    /// Optional default cache directory to use
    cache_dir: Option<PathBuf>,
}

impl SubprocessBackend {
    pub fn new(cache_dir: Option<PathBuf>) -> Self {
        Self { cache_dir }
    }

    /// Receive package stream and unpack it
    ///
    /// Takes a stream of tar.gz data, saves it to a temp file, and unpacks it
    /// Returns the Package (which keeps the temp directory alive)
    async fn receive_and_unpack_package(
        &self,
        mut package_stream: Box<dyn tokio::io::AsyncRead + Send + Unpin>,
    ) -> Result<Package, Error> {
        // Create temp directory for this package
        let temp_dir = TmpDir::new("tower-package")
            .await
            .map_err(|_| Error::PackageCreateFailed)?;

        // Save stream to tar.gz file
        let tar_gz_path = temp_dir.to_path_buf().join("package.tar.gz");
        let mut file = File::create(&tar_gz_path)
            .await
            .map_err(|_| Error::PackageCreateFailed)?;

        tokio::io::copy(&mut package_stream, &mut file)
            .await
            .map_err(|_| Error::PackageCreateFailed)?;

        file.flush().await.map_err(|_| Error::PackageCreateFailed)?;
        drop(file);

        // Unpack the package
        let mut package = Package::default();
        package.package_file_path = Some(tar_gz_path);
        package.tmp_dir = Some(temp_dir);
        package.unpack().await?;

        Ok(package)
    }
}

#[async_trait]
impl ExecutionBackend for SubprocessBackend {
    type Handle = SubprocessHandle;

    async fn create(&self, spec: ExecutionSpec) -> Result<Self::Handle, Error> {
        // Convert ExecutionSpec to StartOptions for LocalApp
        let (output_sender, output_receiver) = tokio::sync::mpsc::unbounded_channel();

        // Get cache_dir from spec or use backend default
        let cache_dir = match &spec.runtime.cache.backend {
            CacheBackend::Local { cache_dir } => Some(cache_dir.clone()),
            _ => self.cache_dir.clone(),
        };

        // Create a unique temp directory for uv if no cache directory is configured
        let (final_cache_dir, uv_temp_dir) = if cache_dir.is_none() {
            let temp_path = std::env::temp_dir().join(format!("tower-uv-{}", spec.id));
            tokio::fs::create_dir_all(&temp_path)
                .await
                .map_err(|_| Error::PackageCreateFailed)?;
            // Use the temp directory as cache_dir and track it for cleanup
            (Some(temp_path.clone()), Some(temp_path))
        } else {
            // Use provided cache_dir, no temp dir to clean up
            (cache_dir, None)
        };

        // Receive package stream and unpack it
        let mut package = self.receive_and_unpack_package(spec.package_stream).await?;

        let unpacked_path = package
            .unpacked_path
            .clone()
            .ok_or(Error::PackageUnpackFailed)?;

        // Extract tmp_dir from package for cleanup tracking
        // We need to keep this alive until execution completes
        let package_tmp_dir = package.tmp_dir.take();

        // Set TMPDIR to the same isolated directory to ensure lock files also go there
        let mut env_vars = spec.env_vars;
        if let Some(ref temp_dir) = uv_temp_dir {
            env_vars.insert("TMPDIR".to_string(), temp_dir.to_string_lossy().to_string());
            env_vars.insert("TEMP".to_string(), temp_dir.to_string_lossy().to_string());
            env_vars.insert("TMP".to_string(), temp_dir.to_string_lossy().to_string());
        }

        let opts = StartOptions {
            ctx: spec.telemetry_ctx,
            package: Package::from_unpacked_path(unpacked_path).await?,
            cwd: None, // LocalApp determines cwd from package
            environment: spec.environment,
            secrets: spec.secrets,
            parameters: spec.parameters,
            env_vars,
            output_sender: output_sender.clone(),
            cache_dir: final_cache_dir, // UV will use this via --cache-dir flag
        };

        // Start the LocalApp
        let app = LocalApp::start(opts).await?;

        Ok(SubprocessHandle {
            id: spec.id,
            app: Arc::new(Mutex::new(app)),
            output_receiver: Arc::new(Mutex::new(output_receiver)),
            package_tmp_dir,
            uv_temp_dir,
        })
    }

    fn capabilities(&self) -> BackendCapabilities {
        BackendCapabilities {
            name: "local".to_string(),
            supports_persistent_cache: true,
            supports_prewarming: false,
            supports_network_isolation: false,
            supports_service_endpoints: false,
            typical_cold_start_ms: 1000,     // ~1s for venv + sync
            typical_warm_start_ms: 100,      // ~100ms with warm cache
            max_concurrent_executions: None, // Limited by system resources
        }
    }

    async fn cleanup(&self) -> Result<(), Error> {
        // Nothing to cleanup for local backend
        Ok(())
    }
}

/// SubprocessHandle provides lifecycle management for a subprocess execution
pub struct SubprocessHandle {
    id: String,
    app: Arc<Mutex<LocalApp>>,
    output_receiver: Arc<Mutex<OutputReceiver>>,
    package_tmp_dir: Option<TmpDir>, // Track package temp directory for cleanup
    uv_temp_dir: Option<PathBuf>,    // Track UV's temp directory for cleanup
}

impl Drop for SubprocessHandle {
    fn drop(&mut self) {
        // Best-effort cleanup of UV temp directory when handle is dropped
        if let Some(temp_dir) = self.uv_temp_dir.take() {
            let _ = std::fs::remove_dir_all(&temp_dir);
        }

        // Best-effort cleanup of package temp directory when handle is dropped
        if let Some(tmp_dir) = self.package_tmp_dir.take() {
            let _ = std::fs::remove_dir_all(tmp_dir.to_path_buf());
        }
    }
}

#[async_trait]
impl ExecutionHandle for SubprocessHandle {
    fn id(&self) -> &str {
        &self.id
    }

    async fn status(&self) -> Result<Status, Error> {
        let app = self.app.lock().await;
        app.status().await
    }

    async fn logs(&self) -> Result<OutputReceiver, Error> {
        // Create a new channel for log streaming
        let (tx, rx) = tokio::sync::mpsc::unbounded_channel();

        // Spawn a task to forward Output from the internal receiver
        let output_receiver = self.output_receiver.clone();
        tokio::spawn(async move {
            let mut receiver = output_receiver.lock().await;
            while let Some(output) = receiver.recv().await {
                if tx.send(output).is_err() {
                    break; // Receiver dropped
                }
            }
        });

        Ok(rx)
    }

    async fn terminate(&mut self) -> Result<(), Error> {
        let mut app = self.app.lock().await;
        app.terminate().await
    }

    async fn kill(&mut self) -> Result<(), Error> {
        // For local processes, kill is the same as terminate
        self.terminate().await
    }

    async fn wait_for_completion(&self) -> Result<Status, Error> {
        loop {
            let status = self.status().await?;
            match status {
                Status::None | Status::Running => {
                    tokio::time::sleep(Duration::from_millis(100)).await;
                }
                _ => return Ok(status),
            }
        }
    }

    async fn service_endpoint(&self) -> Result<Option<ServiceEndpoint>, Error> {
        // Local backend doesn't support service endpoints
        Ok(None)
    }

    async fn cleanup(&mut self) -> Result<(), Error> {
        // Ensure the app is terminated
        self.terminate().await?;

        // Clean up uv's temp directory if it was created
        if let Some(ref temp_dir) = self.uv_temp_dir {
            if let Err(e) = tokio::fs::remove_dir_all(temp_dir).await {
                // Log but don't fail - cleanup is best-effort
                tower_telemetry::debug!("Failed to clean up uv temp directory: {:?}", e);
            }
        }

        // Clean up package temp directory
        if let Some(tmp_dir) = self.package_tmp_dir.take() {
            let path = tmp_dir.to_path_buf();
            if let Err(e) = tokio::fs::remove_dir_all(&path).await {
                // Log but don't fail - cleanup is best-effort
                tower_telemetry::debug!("Failed to clean up package temp directory: {:?}", e);
            }
        }

        Ok(())
    }
}
