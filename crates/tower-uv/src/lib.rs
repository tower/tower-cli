use std::path::PathBuf;
use std::collections::HashMap;
use tokio::process::{Command, Child};

mod install;

#[derive(Debug)]
pub enum Error {
    IoError(std::io::Error),
    NotFound(String),
    PermissionDenied(String),
    Other(String),
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
            install::Error::IoError(e) => Error::IoError(e),
            install::Error::Other(msg) => Error::Other(msg),
        }
    }
}

async fn find_uv_binary() -> Option<PathBuf> {
    if let Ok(default_path) = install::get_default_uv_bin_dir() {
        // Check if the default path exists
        if default_path.exists() {
            let uv_path = default_path.join("uv");
            if uv_path.exists() {
                return Some(uv_path);
            }
        } 
    }

    // First, check if uv is already in the PATH
    let output = Command::new("which")
        .arg("uv")
        .output()
        .await;

    if let Ok(output) = output {
        let path_str = String::from_utf8_lossy(&output.stdout);
        let path = PathBuf::from(path_str.trim());

        // If this is a path that actually exists, then we assume that it's `uv` and we can
        // continue.
        if path.exists() {
            Some(path)
        } else {
            None
        }
    } else{
        None
    }
} 

async fn find_or_setup_uv() -> Result<PathBuf, Error> {
    // If we get here, uv wasn't found in PATH, so let's download it
    if let Some(path) = find_uv_binary().await {
        Ok(path) 
    } else {
        let path = install::get_default_uv_bin_dir()?;

        // Create the directory if it doesn't exist
        std::fs::create_dir_all(&path).map_err(Error::IoError)?;

        let parent = path.parent()
            .ok_or_else(|| Error::NotFound("Parent directory not found".to_string()))?
            .to_path_buf();

        // We download this code to the UV directory
        let exe = install::download_uv_for_arch(&parent).await?;

        // Target is the UV binary we want.
        let target = path.join("uv");

        // Copy the `uv` binary into the default directory
        std::fs::copy(&exe, &target)
            .map_err(|e| Error::IoError(e))?;

        Ok(target)
    }
}

pub struct Uv {
    pub uv_path: PathBuf,
}

impl Uv {
    pub async fn new() -> Result<Self, Error> {
        let uv_path = find_or_setup_uv().await?;
        Ok(Uv { uv_path })
    }

    pub async fn execute(&self, cwd: &PathBuf, program: &PathBuf, env_vars: HashMap<String, String>) -> Result<Child, Error> {
        let child = Command::new(&self.uv_path)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .arg("run")
            .arg(program)
            .cwd(cwd)
            .env_vars(env_vars)
            .spawn();

        Ok(child)
    }
}
