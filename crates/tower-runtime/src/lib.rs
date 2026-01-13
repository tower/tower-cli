use chrono::{DateTime, Utc};
use std::collections::HashMap;
use std::future::Future;
use std::path::PathBuf;
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender};

use tower_package::Package;
use tower_telemetry::debug;

pub mod errors;
pub mod execution;
pub mod local;

use errors::Error;
use execution::{ExecutionBackend, ExecutionHandle};

#[derive(Copy, Clone)]
pub enum FD {
    Stdout,
    Stderr,
}

#[derive(Copy, Clone)]
pub enum Channel {
    // Setup channel is used for messages that pertain to environmental setup (e.g. installing
    // dependencies with pip)
    Setup,

    // Program channel is used for messages that pertain to the program's actual output.
    Program,
}

pub struct Output {
    pub channel: Channel,
    pub time: DateTime<Utc>,
    pub fd: FD,
    pub line: String,
}

#[derive(Copy, Clone, Debug, PartialEq)]
pub enum Status {
    None,
    Running,
    Exited,
    Crashed { code: i32 },
}

pub type OutputReceiver = UnboundedReceiver<Output>;

pub type OutputSender = UnboundedSender<Output>;

pub trait App: Send + Sync {
    type Backend: execution::ExecutionBackend;

    // start will start the process
    fn start(opts: StartOptions) -> impl Future<Output = Result<Self, Error>> + Send
    where
        Self: Sized;

    // terminate will terminate the subprocess
    fn terminate(&mut self) -> impl Future<Output = Result<(), Error>> + Send;

    // status checks the status of an app
    fn status(&self) -> impl Future<Output = Result<Status, Error>> + Send;
}

pub struct AppLauncher<A: App> {
    pub handle: Option<<A::Backend as execution::ExecutionBackend>::Handle>,
}

impl<A: App> std::default::Default for AppLauncher<A> {
    fn default() -> Self {
        Self { handle: None }
    }
}

impl<A: App> AppLauncher<A>
where
    A::Backend: execution::ExecutionBackend,
{
    pub async fn launch(
        &mut self,
        backend: A::Backend,
        ctx: tower_telemetry::Context,
        package: Package,
        environment: String,
        secrets: HashMap<String, String>,
        parameters: HashMap<String, String>,
        env_vars: HashMap<String, String>,
    ) -> Result<(), Error> {
        let package_path = package.unpacked_path.clone().unwrap().to_path_buf();

        // Build ExecutionSpec from parameters
        use std::time::{SystemTime, UNIX_EPOCH};
        let id = format!(
            "run-{}",
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        );

        let spec = execution::ExecutionSpec {
            id,
            bundle: execution::BundleRef::Local {
                path: package_path.clone(),
            },
            runtime: execution::RuntimeConfig {
                image: "local".to_string(),
                version: None,
                cache: execution::CacheConfig {
                    enable_bundle_cache: true,
                    enable_runtime_cache: true,
                    enable_dependency_cache: true,
                    backend: execution::CacheBackend::None,
                    isolation: execution::CacheIsolation::None,
                },
                entrypoint: None,
                command: None,
            },
            environment,
            secrets,
            parameters,
            env_vars,
            resources: execution::ResourceLimits {
                cpu_millicores: None,
                memory_mb: None,
                storage_mb: None,
                max_pids: None,
                gpu_count: 0,
                timeout_seconds: 3600,
            },
            networking: None,
            telemetry_ctx: ctx,
        };

        // Drop any existing handle
        self.handle = None;

        // Create execution using backend
        let handle = backend.create(spec).await?;
        self.handle = Some(handle);

        Ok(())
    }

    pub async fn terminate(&mut self) -> Result<(), Error> {
        if let Some(handle) = &mut self.handle {
            if let Err(err) = handle.terminate().await {
                debug!("failed to terminate app: {}", err);
                Err(err)
            } else {
                self.handle = None;
                Ok(())
            }
        } else {
            // There's no handle, so nothing to terminate.
            Ok(())
        }
    }

    pub async fn status(&self) -> Result<Status, Error> {
        if let Some(handle) = &self.handle {
            handle.status().await
        } else {
            Ok(Status::None)
        }
    }
}

pub struct StartOptions {
    pub ctx: tower_telemetry::Context,
    pub package: Package,
    pub cwd: Option<PathBuf>,
    pub environment: String,
    pub secrets: HashMap<String, String>,
    pub parameters: HashMap<String, String>,
    pub env_vars: HashMap<String, String>,
    pub output_sender: OutputSender,
    pub cache_dir: Option<PathBuf>,
}

pub struct ExecuteOptions {
    pub path: PathBuf,
    pub cwd: Option<PathBuf>,
}
