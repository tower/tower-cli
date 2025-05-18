use tower_package::Package;
use crate::{
    Error,
    launcher::{
        AppLauncher,
        AppStatus,
    }
};

pub struct App<L: AppLauncher> {
    launcher: L,
    package: Package,

    // pid is the running pid for this app
    pid: Option<L::Pid>,
}

impl<L: AppLauncher> App<L> {
    pub fn new(launcher: L, package: Package) -> Self{
       Self {
           launcher,
           package,
           pid: None,
       } 
    }

    pub async fn start(&mut self) -> Result<(), Error> {
        // Perform setup
        self.launcher.setup(&self.package)?;

        // Start the app
        let pid = self.launcher.start(&self.package)?;

        // We save the pid for later on.
        self.pid = Some(pid);

        Ok(())
    }

    pub async fn terminate(&mut self) -> Result<(), Error> {
        if let Some(pid) = &self.pid {
            self.launcher.terminate(pid)?;
            self.pid = None;
        }

        Ok(())
    }

    pub async fn status(&self) -> Result<AppStatus, Error> {
        if let Some(pid) = &self.pid {
            self.launcher.status(pid)
        } else {
            Err(Error::AppNotRunning)
        }
    }
}
