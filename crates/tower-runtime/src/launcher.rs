use std::future::Future;

use tower_package::Package;
use crate::{Error, Output};

use tokio::sync::mpsc::UnboundedReceiver;

#[derive(Copy, Clone, PartialEq)]
pub enum AppState {
    Pending,
    Setup,
    Running,
    Exited { code: i32 },
}

pub struct AppStatus{
    pub exit_code: Option<i32>,
}

type Result<T> = std::result::Result<T, Error>;

pub trait AppLauncher {
    // Pid is the type that we use for identifying a running process.
    type Pid: Sized;

    fn setup(&self, package: &Package) -> impl Future<Output = Result<((), UnboundedReceiver<Output>)>> + Send;
    fn start(&self, package: &Package) -> impl Future<Output = Result<(Self::Pid, UnboundedReceiver<Output>)>> + Send;
    fn status(&self, pid: &Self::Pid) -> impl Future<Output = Result<AppStatus>> + Send;
    fn terminate(&self, pid: &Self::Pid) -> impl Future<Output = Result<()>> + Send;
}
