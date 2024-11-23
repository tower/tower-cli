use std::path::PathBuf;
use std::future::Future;
use std::sync::Arc;
use std::collections::HashMap;
use tokio::sync::Mutex;
use tokio::sync::mpsc::Receiver;
use chrono::{DateTime, Utc};

use tower_package::Package;

pub mod local;
pub mod errors;

use errors::Error;

#[derive(Copy, Clone)]
pub enum FD {
    Stdout,
    Stderr,
}

pub struct Output {
    pub time: DateTime<Utc>,
    pub fd: FD,
    pub line: String,
}

#[derive(Copy, Clone)]
pub enum Status {
    None,
    Running,
    Exited,
    Crashed,
}

type SharedReceiver<T> = Arc<Mutex<Receiver<T>>>;

pub type OutputChannel = SharedReceiver<Output>;

pub trait App {
    // start will start the process
    fn start(opts: StartOptions) -> impl Future<Output = Result<Self, Error>> + Send
        where Self: Sized;

    // terminate will terminate the subprocess
    fn terminate(&mut self) -> impl Future<Output = Result<(), Error>> + Send;

    // status checks the status of an app 
    fn status(&mut self) -> impl Future<Output = Result<Status, Error>> + Send;

    // output returns a reader that contains a combination of the stdout and stderr messages from
    // the child process
    fn output(&self) -> impl Future<Output = Result<OutputChannel, Error>> + Send;
}

#[derive(Default)]
pub struct AppLauncher<A: App> {
    pub app: Option<A>,
}

impl<A: App> AppLauncher<A> {
    pub async fn launch(
        &mut self,
        package: Package,
        environment: String,
        secrets: HashMap<String, String>,
        parameters: HashMap<String, String>,
    ) -> Result<(), Error> {
        let cwd = package.unpacked_path.clone().unwrap().to_path_buf();

        let opts = StartOptions {
            cwd: Some(cwd),
            environment,
            secrets,
            parameters,
            package,
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
                log::debug!("failed to terminate app: {}", err);
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
    pub package: Package,
    pub cwd: Option<PathBuf>,
    pub environment: String,
    pub secrets: HashMap<String, String>,
    pub parameters: HashMap<String, String>,
}

pub struct ExecuteOptions {
    pub path: PathBuf,
    pub cwd: Option<PathBuf>,
}
