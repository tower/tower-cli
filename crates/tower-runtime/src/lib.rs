use chrono::{DateTime, Utc};
use std::collections::HashMap;
use std::future::Future;
use std::path::PathBuf;
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender};

use tower_package::Package;
use tower_telemetry::debug;

pub mod errors;
pub mod local;

use errors::Error;

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

#[derive(Copy, Clone, PartialEq)]
pub enum Status {
    None,
    Running,
    Exited,
    Crashed { code: i32 },
}

pub type OutputReceiver = UnboundedReceiver<Output>;

pub type OutputSender = UnboundedSender<Output>;

pub trait App {
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
    pub app: Option<A>,
}

impl<A: App> std::default::Default for AppLauncher<A> {
    fn default() -> Self {
        Self { app: None }
    }
}

impl<A: App> AppLauncher<A> {
    pub async fn launch(
        &mut self,
        ctx: tower_telemetry::Context,
        output_sender: OutputSender,
        package: Package,
        environment: String,
        secrets: HashMap<String, String>,
        parameters: HashMap<String, String>,
        env_vars: HashMap<String, String>,
    ) -> Result<(), Error> {
        let cwd = package.unpacked_path.clone().unwrap().to_path_buf();

        let opts = StartOptions {
            ctx,
            output_sender,
            cwd: Some(cwd),
            environment,
            secrets,
            parameters,
            package,
            env_vars,
        };

        // NOTE: This is a really awful hack to force any existing app to drop itself. Not certain
        // this is exactly what we want to do...
        self.app = None;

        let res = A::start(opts).await;

        if let Ok(app) = res {
            self.app = Some(app);
            Ok(())
        } else {
            self.app = None;
            Err(res.err().unwrap())
        }
    }

    pub async fn terminate(&mut self) -> Result<(), Error> {
        if let Some(app) = &mut self.app {
            if let Err(err) = app.terminate().await {
                debug!("failed to terminate app: {}", err);
                Err(err)
            } else {
                self.app = None;
                Ok(())
            }
        } else {
            // There's no app, so nothing to terminate.
            Ok(())
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
}

pub struct ExecuteOptions {
    pub path: PathBuf,
    pub cwd: Option<PathBuf>,
}
