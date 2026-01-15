use chrono::{DateTime, Utc};
use std::collections::HashMap;
use std::future::Future;
use std::path::PathBuf;
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender};

use tower_package::Package;

pub mod errors;
pub mod execution;
pub mod local;
pub mod subprocess;

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
    // start will start the process
    fn start(opts: StartOptions) -> impl Future<Output = Result<Self, Error>> + Send
    where
        Self: Sized;

    // terminate will terminate the subprocess
    fn terminate(&mut self) -> impl Future<Output = Result<(), Error>> + Send;

    // status checks the status of an app
    fn status(&self) -> impl Future<Output = Result<Status, Error>> + Send;
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
