use std::path::PathBuf;
use std::sync::Arc;
use std::collections::HashMap;
use tokio::sync::Mutex;
use tokio::sync::mpsc::Receiver;

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
    async fn start(opts: StartOptions) -> Result<Self, Error>
        where Self: Sized;

    // terminate will terminate the subprocess
    async fn terminate(&mut self) -> Result<(), Error>;

    // status checks the status of an app 
    async fn status(&mut self) -> Result<Status, Error>;

    // output returns a reader that contains a combination of the stdout and stderr messages from
    // the child process
    async fn output(&self) -> Result<OutputChannel, Error>;
}

pub struct Running<A: App> {
    // app is the actual underlying app that's currently running.
    app: A,

    pub run_id: String,
    pub package: Option<Package>,
}

impl<A: App> Running<A> {
    pub async fn output(&self) -> Result<OutputChannel, Error> {
        self.app.output().await
    }

    pub async fn status(&mut self) -> Result<Status, Error> {
        self.app.status().await
    }
}

#[derive(Default)]
pub struct AppLauncher<A: App> {
    pub app: Option<Running<A>>,
}

impl<A: App> AppLauncher<A> {
    pub async fn launch(
        &mut self,
        run_id: &str,
        package: Package,
        secrets: HashMap<String, String>,
    ) -> Result<(), Error> {
        let opts = StartOptions {
            secrets,
            path: package.path.to_path_buf(),
            cwd: Some(package.path.to_path_buf()),
        };

        // NOTE: This is a really awful hack to force any existing app to drop itself. Not certain
        // this is exactly what we want to do...
        self.app = None;

        let res = A::start(opts).await;

        if let Ok(app) = res {
            self.app = Some(Running {
                app,
                run_id: String::from(run_id),
                package: None,
            });

            Ok(())
        } else {
            self.app = None;
            Err(res.err().unwrap())
        }
    }

    pub async fn terminate(&mut self) -> Result<(), Error> {
        if let Some(app) = &mut self.app {
            let app = &mut app.app;

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
    pub path: PathBuf,
    pub cwd: Option<PathBuf>,
    pub secrets: HashMap<String, String>,
}

pub struct ExecuteOptions {
    pub path: PathBuf,
    pub cwd: Option<PathBuf>,
}
