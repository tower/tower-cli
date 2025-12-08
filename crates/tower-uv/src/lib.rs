use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use tokio::process::{Child, Command};
use tower_telemetry::debug;

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
        Error::IoError(err)
    }
}

fn normalize_env_vars(env_vars: &HashMap<String, String>) -> HashMap<String, String> {
    // we copy this locally so we can mutate the results.
    let mut env_vars = env_vars.clone();

    // Copy the PATH across so that the child process can find tools/binaries already installed
    // on the host system.
    let path = std::env::var("PATH").unwrap_or_default();
    env_vars.insert("PATH".to_string(), path);

    // This special hack helps us support Sling. The user needs to specify exactly where the Sling
    // binary is installed using the SLING_BINARY environment variable such that we don't have to
    // download the Sling binary every single time.
    let sling_binary = std::env::var("SLING_BINARY").unwrap_or_default();
    env_vars.insert("SLING_BINARY".to_string(), sling_binary);

    #[cfg(windows)]
    {
        // If we are running on Windows, we need to retain the SYSTEMROOT env var because Python
        // needs it to initialize it's random number generator. Fun fact!
        let systemroot = std::env::var("SYSTEMROOT").unwrap_or_default();
        env_vars.insert("SYSTEMROOT".to_string(), systemroot);

        // We also need to bring along the TEMP environment variable because Python needs it for
        // things like creating temporary files, etc.
        let temp = std::env::var("TEMP").unwrap_or_default();
        env_vars.insert("TEMP".to_string(), temp);

        // Apparently, according to some random person on Stack Overflow, sometimes the var can be
        // TEMP and sometimes it can be TMP. So uh...let's just grab both just in case.
        let tmp = std::env::var("TMP").unwrap_or_default();
        env_vars.insert("TMP".to_string(), tmp);
    }

    env_vars
}

/// Find the uv-wrapper binary that was built alongside tower-cli
fn find_uv_wrapper() -> Result<PathBuf, Error> {
    let current_exe = std::env::current_exe()
        .map_err(|e| Error::Other(format!("Failed to get current executable path: {}", e)))?;

    let exe_dir = current_exe
        .parent()
        .ok_or_else(|| Error::Other("Failed to get executable directory".to_string()))?;

    let binary_name = if cfg!(windows) { "uv-wrapper.exe" } else { "uv-wrapper" };

    // Check exe dir (production) and parent dir (tests run from target/debug/deps/)
    let dirs: Vec<PathBuf> = [Some(exe_dir), exe_dir.parent()]
        .into_iter()
        .flatten()
        .map(Path::to_path_buf)
        .collect();

    dirs.iter()
        .map(|dir| dir.join(binary_name))
        .find(|p| p.exists())
        .ok_or_else(|| Error::NotFound(format!("uv-wrapper binary not found near {:?}", exe_dir)))
}

pub struct Uv {
    pub uv_path: PathBuf,

    // cache_dir is the directory that dependencies should be cached in.
    cache_dir: Option<PathBuf>,

    // protected_mode is a flag that indicates whether the UV instance is in protected mode.
    // In protected mode, the UV instance do things like clear the environment variables before
    // use, etc.
    protected_mode: bool,
}

impl Uv {
    pub async fn new(cache_dir: Option<PathBuf>, protected_mode: bool) -> Result<Self, Error> {
        let uv_path = find_uv_wrapper()?;
        debug!("Using uv-wrapper at: {:?}", uv_path);
        Ok(Uv {
            uv_path,
            cache_dir,
            protected_mode,
        })
    }

    pub async fn venv(
        &self,
        cwd: &PathBuf,
        env_vars: &HashMap<String, String>,
    ) -> Result<Child, Error> {
        debug!("Executing UV ({:?}) venv in {:?}", &self.uv_path, cwd);

        let mut cmd = Command::new(&self.uv_path);
        cmd.kill_on_drop(true)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .current_dir(cwd)
            .arg("venv")
            .envs(env_vars);

        if let Some(dir) = &self.cache_dir {
            cmd.arg("--cache-dir").arg(dir);
        }

        let child = cmd.spawn()?;

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

            if let Some(dir) = &self.cache_dir {
                cmd.arg("--cache-dir").arg(dir);
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

            if let Some(dir) = &self.cache_dir {
                cmd.arg("--cache-dir").arg(dir);
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

        // Sometimes, we need to copy some env vars out of the current environment and into the new
        // one!
        let env_vars = normalize_env_vars(env_vars);

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
            .arg(program);

        #[cfg(unix)]
        {
            cmd.process_group(0);
        }

        if self.protected_mode {
            cmd.env_clear();
        }

        // Need to do this after env_clear intentionally.
        cmd.envs(env_vars);

        if let Some(dir) = &self.cache_dir {
            cmd.arg("--cache-dir").arg(dir);
        }

        let child = cmd.spawn()?;
        Ok(child)
    }

    pub async fn is_valid(&self) -> bool {
        self.uv_path.exists()
    }
}
