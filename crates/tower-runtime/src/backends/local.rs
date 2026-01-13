//! Local subprocess execution backend

use crate::errors::Error;
use crate::execution::{
    BackendCapabilities, BundleRef, CacheBackend, ExecutionBackend, ExecutionHandle, ExecutionSpec,
    ServiceEndpoint,
};
use crate::local::LocalApp;
use crate::{App, OutputReceiver, StartOptions, Status};

use async_trait::async_trait;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::Duration;
use tower_package::Package;

/// LocalBackend executes apps as local subprocesses
pub struct LocalBackend {
    /// Optional default cache directory to use
    cache_dir: Option<PathBuf>,
}

impl LocalBackend {
    pub fn new(cache_dir: Option<PathBuf>) -> Self {
        Self { cache_dir }
    }
}

#[async_trait]
impl ExecutionBackend for LocalBackend {
    type Handle = LocalHandle;

    async fn create(&self, spec: ExecutionSpec) -> Result<Self::Handle, Error> {
        // Convert ExecutionSpec to StartOptions for LocalApp
        let (output_sender, output_receiver) = tokio::sync::mpsc::unbounded_channel();

        // Get cache_dir from spec or use backend default
        let cache_dir = match &spec.runtime.cache.backend {
            CacheBackend::Local { cache_dir } => Some(cache_dir.clone()),
            _ => self.cache_dir.clone(),
        };

        let opts = StartOptions {
            ctx: spec.telemetry_ctx,
            package: match spec.bundle {
                BundleRef::Local { path } => Package::from_unpacked_path(path).await,
            },
            cwd: None, // LocalApp determines cwd from package
            environment: spec.environment,
            secrets: spec.secrets,
            parameters: spec.parameters,
            env_vars: spec.env_vars,
            output_sender: output_sender.clone(),
            cache_dir,
        };

        // Start the LocalApp
        let app = LocalApp::start(opts).await?;

        Ok(LocalHandle {
            id: spec.id,
            app: Arc::new(Mutex::new(app)),
            output_receiver: Arc::new(Mutex::new(output_receiver)),
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

/// LocalHandle provides lifecycle management for a local subprocess execution
pub struct LocalHandle {
    id: String,
    app: Arc<Mutex<LocalApp>>,
    output_receiver: Arc<Mutex<OutputReceiver>>,
}

#[async_trait]
impl ExecutionHandle for LocalHandle {
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
        Ok(())
    }
}
