//! Simple backend for CLI --local runs
//!
//! This backend follows a simpler pattern than SubprocessBackend:
//! - The caller creates the output channel and passes the sender
//! - The caller keeps the receiver for direct consumption
//! - No need for complex handle.logs() method
//! - Single consumer model (perfect for CLI)

use crate::errors::Error;
use crate::local::LocalApp;
use crate::{App, OutputSender, StartOptions, Status};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;
use tower_package::Package;

/// CliBackend executes apps as local subprocesses for CLI --local runs
pub struct CliBackend {
    /// Optional default cache directory to use
    cache_dir: Option<PathBuf>,
}

impl CliBackend {
    pub fn new(cache_dir: Option<PathBuf>) -> Self {
        Self { cache_dir }
    }

    /// Launch an app with the given parameters
    ///
    /// Unlike SubprocessBackend.create(), this takes OutputSender directly
    /// so the caller can immediately start consuming output from their receiver.
    pub async fn launch(
        &self,
        ctx: tower_telemetry::Context,
        output_sender: OutputSender,
        package: Package,
        environment: String,
        secrets: HashMap<String, String>,
        parameters: HashMap<String, String>,
        env_vars: HashMap<String, String>,
    ) -> Result<CliHandle, Error> {
        let opts = StartOptions {
            ctx,
            package,
            cwd: None, // LocalApp determines cwd from package
            environment,
            secrets,
            parameters,
            env_vars,
            output_sender,
            cache_dir: self.cache_dir.clone(),
        };

        // Start the LocalApp
        let app = LocalApp::start(opts).await?;

        Ok(CliHandle {
            app: Arc::new(Mutex::new(Some(app))),
        })
    }
}

/// CliHandle provides lifecycle management for a CLI local subprocess execution
pub struct CliHandle {
    app: Arc<Mutex<Option<LocalApp>>>,
}

impl CliHandle {
    /// Get current execution status
    pub async fn status(&self) -> Result<Status, Error> {
        let guard = self.app.lock().await;
        if let Some(app) = guard.as_ref() {
            app.status().await
        } else {
            // App has already been terminated
            Ok(Status::Crashed { code: -1 })
        }
    }

    /// Terminate execution gracefully
    pub async fn terminate(&mut self) -> Result<(), Error> {
        let mut guard = self.app.lock().await;
        if let Some(mut app) = guard.take() {
            app.terminate().await
        } else {
            Ok(())
        }
    }
}
