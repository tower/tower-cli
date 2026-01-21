//! Local subprocess execution backend

use crate::errors::Error;
use crate::execution::{Backend, BackendCapabilities, CacheBackend, ExecutionSpec};
use crate::local::LocalApp;
use crate::StartOptions;

use async_trait::async_trait;
use std::path::PathBuf;
use tokio::fs::File;
use tokio::io::AsyncWriteExt;
use tower_package::Package;

/// SubprocessBackend executes apps as local subprocesses
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
        let temp_dir = tmpdir::TmpDir::new("tower-package")
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
impl Backend for SubprocessBackend {
    type App = LocalApp;

    async fn create(&self, spec: ExecutionSpec) -> Result<Self::App, Error> {
        // Convert ExecutionSpec to StartOptions for LocalApp
        let (output_sender, output_receiver) = tokio::sync::mpsc::unbounded_channel();

        // Get cache_dir from spec or use backend default
        let cache_dir = match &spec.runtime.cache.backend {
            CacheBackend::Local { cache_dir } => Some(cache_dir.clone()),
            _ => self.cache_dir.clone(),
        };

        // Receive package stream and unpack it
        let package = self.receive_and_unpack_package(spec.package_stream).await?;

        let unpacked_path = package
            .unpacked_path
            .clone()
            .ok_or(Error::PackageUnpackFailed)?;

        let opts = StartOptions {
            ctx: spec.telemetry_ctx,
            package: Package::from_unpacked_path(unpacked_path).await?,
            cwd: None, // LocalApp determines cwd from package
            environment: spec.environment,
            secrets: spec.secrets,
            parameters: spec.parameters,
            env_vars: spec.env_vars,
            output_sender,
            cache_dir,
        };

        // Start the LocalApp with the execution ID, output receiver, and package
        // The package is kept alive so the temp dir doesn't get cleaned up
        LocalApp::new(spec.id, opts, Some(output_receiver), Some(package)).await
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
