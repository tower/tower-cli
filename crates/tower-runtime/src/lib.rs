use chrono::{DateTime, Utc};
use std::collections::HashMap;
use std::future::Future;
use std::path::PathBuf;
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender};

use tower_package::Package;

pub mod auto_cleanup;
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

#[derive(Clone, Debug, PartialEq)]
pub enum Status {
    None,
    Running,
    Exited,
    Crashed {
        code: i32,
    },
    /// The app was explicitly terminated via the `CancellationToken` — a
    /// deliberate stop, not a failure or a crash. Distinct from `Crashed`
    /// because there's no meaningful exit code to report.
    Cancelled,
    /// A platform-level failure (not the user's app). For example, pod scheduling
    /// failures, image pull errors, or other infrastructure issues.
    Failed(AppFailure),
}

/// A platform-level failure — distinct from a child-process crash
/// (`Status::Crashed`) because the user's app never ran to completion.
/// Consumers (currently `tower-runtime-entrypoint` and the runner-side k8s
/// backend) translate this into the `error_code` / `error_message` strings
/// that flow through the termination-log → control-plane log pipeline.
#[derive(Clone, Debug, PartialEq)]
pub enum AppFailure {
    /// A structured runtime error from `tower_runtime` (e.g.
    /// `UnsupportedPlatform`, `SpawnFailed`, `DependencyInstallationFailed`).
    Runtime(Error),
    /// A panic inside the spawned task. `catch_unwind` only returns
    /// `Box<dyn Any + Send>`, so we surface the best-effort textual payload.
    Panic(String),
    /// A platform failure surfaced from outside `tower_runtime` (e.g. the
    /// kubelet refusing to pull an image, an init container failing, or a
    /// parsed entrypoint termination message). The `error_code` is opaque
    /// to `tower_runtime` — the consumer that constructed this variant owns
    /// the vocabulary.
    Platform {
        error_code: String,
        error_message: String,
    },
}

impl Status {
    /// Returns true if this status represents a terminal state (run is finished)
    pub fn is_terminal(&self) -> bool {
        matches!(
            self,
            Status::Exited | Status::Crashed { .. } | Status::Cancelled | Status::Failed(_)
        )
    }
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
