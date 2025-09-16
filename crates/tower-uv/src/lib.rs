use std::collections::HashMap;
use std::path::PathBuf;
use std::process::Stdio;
use tokio::process::{Child, Command};
use tower_telemetry::debug;

pub mod install;

// UV_VERSION is the version of UV to download and install when setting up a local UV deployment.
pub const UV_VERSION: &str = "0.7.13";

#[derive(Debug)]
pub enum Error {
    IoError(std::io::Error),
    NotFound(String),
    PermissionDenied(String),
    Other(String),
    MissingPyprojectToml,
    InvalidUv,
    UnsupportedPlatform,
}

impl From<std::io::Error> for Error {
    fn from(err: std::io::Error) -> Self {
        // Convert std::fs::Error to your custom Error type
        Error::IoError(err)
    }
}

impl From<install::Error> for Error {
    fn from(err: install::Error) -> Self {
        match err {
            install::Error::NotFound(msg) => Error::NotFound(msg),
            install::Error::UnsupportedPlatform => Error::UnsupportedPlatform,
            install::Error::IoError(e) => Error::IoError(e),
            install::Error::Other(msg) => Error::Other(msg),
        }
    }
}

async fn test_uv_path(path: &PathBuf) -> Result<(), Error> {
    let res = Command::new(&path)
        .arg("--color")
        .arg("never")
        .arg("--no-progress")
        .arg("--help")
        .output()
        .await;

    match res {
        Ok(_) => Ok(()),
        Err(e) => {
            debug!("Testing UV failed: {:?}", e);
            Err(Error::InvalidUv)
        }
    }
}

pub struct Uv {
    pub uv_path: PathBuf,
}

impl Uv {
    pub async fn new() -> Result<Self, Error> {
        match install::find_or_setup_uv().await {
            Ok(uv_path) => {
                test_uv_path(&uv_path).await?;
                Ok(Uv { uv_path })
            }
            Err(e) => {
                debug!("Error setting up UV: {:?}", e);
                Err(e.into())
            }
        }
    }

    pub async fn venv(
        &self,
        cwd: &PathBuf,
        env_vars: &HashMap<String, String>,
    ) -> Result<Child, Error> {
        debug!("Executing UV ({:?}) venv in {:?}", &self.uv_path, cwd);

        let child = Command::new(&self.uv_path)
            .kill_on_drop(true)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .current_dir(cwd)
            .arg("venv")
            .envs(env_vars)
            .spawn()?;

        Ok(child)
    }

    pub async fn sync(
        &self,
        cwd: &PathBuf,
        env_vars: &HashMap<String, String>,
    ) -> Result<Child, Error> {
        // We need to figure out which sync strategy to apply. If there is a pyproject.toml, then
        // that's easy.
        if cwd.join("pyproject.toml").exists() {
            debug!("Executing UV ({:?}) sync in {:?}", &self.uv_path, cwd);
            let mut cmd = Command::new(&self.uv_path);
            cmd.kill_on_drop(true)
                .stdin(Stdio::null())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .current_dir(cwd)
                .arg("--color")
                .arg("never")
                .arg("--no-progress")
                .arg("sync")
                .envs(env_vars);

            #[cfg(unix)]
            {
                cmd.process_group(0);
            }

            let child = cmd.spawn()?;

            Ok(child)
        } else if cwd.join("requirements.txt").exists() {
            debug!(
                "Executing UV ({:?}) sync with requirements in {:?}",
                &self.uv_path, cwd
            );

            // If there is a requirements.txt, then we can use that to sync.
            let mut cmd = Command::new(&self.uv_path);
            cmd.kill_on_drop(true)
                .stdin(Stdio::null())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .current_dir(cwd)
                .arg("--color")
                .arg("never")
                .arg("pip")
                .arg("install")
                .arg("-r")
                .arg(cwd.join("requirements.txt"))
                .envs(env_vars);

            #[cfg(unix)]
            {
                cmd.process_group(0);
            }

            let child = cmd.spawn()?;

            Ok(child)
        } else {
            // If there is no pyproject.toml or requirements.txt, then we can't sync.
            Err(Error::MissingPyprojectToml)
        }
    }

    pub async fn run(
        &self,
        cwd: &PathBuf,
        program: &PathBuf,
        env_vars: &HashMap<String, String>,
    ) -> Result<Child, Error> {
        debug!(
            "Executing UV ({:?}) run {:?} in {:?}",
            &self.uv_path, program, cwd
        );

        let mut cmd = Command::new(&self.uv_path);
        cmd.kill_on_drop(true)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .current_dir(cwd)
            .arg("--color")
            .arg("never")
            .arg("--no-progress")
            .arg("run")
            .arg(program)
            .envs(env_vars);

        #[cfg(unix)]
        {
            cmd.process_group(0);
        }

        let child = cmd.spawn()?;
        Ok(child)
    }

    pub async fn is_valid(&self) -> bool {
        test_uv_path(&self.uv_path).await.is_ok()
    }
}
