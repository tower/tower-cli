use std::path::{Path, PathBuf};
use std::env::{self, current_dir};
use std::process::Stdio;
use std::sync::Arc;
use std::collections::HashMap;

#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;

use crate::{
    Status,
    StartOptions,
    errors::Error,
};

use tokio::{
    sync::oneshot,
    sync::oneshot::error::TryRecvError,
    sync::mpsc::channel,
    process::Command,
};

use tokio::{
    fs,
    io::{AsyncRead, BufReader, AsyncBufReadExt},
    time::{timeout, Duration},
    sync::Mutex,
    sync::mpsc::Sender,
    process::Child, 
};

use tower_package::Package;

use crate::{
    FD,
    App,
    Output,
    OutputChannel,
};

pub struct LocalApp {
    // LocalApp needs to take ownership of the package as a way of taking responsibility for it's
    // lifetime and, most importantly, it's contents. The compiler complains that we never actually
    // use this struct member, so we allow the dead_code attribute to silence the warning.
    #[allow(dead_code)]
    package: Option<Package>,

    child: Option<Arc<Mutex<Child>>>,
    status: Option<Status>,
    waiter: Option<oneshot::Receiver<i32>>,
}

impl Default for LocalApp {
    fn default() -> Self {
        Self {
            package: None,
            child: None,
            status: None,
            waiter: None,
        }
    }
}

// Helper function to check if a file is executable
async fn is_executable(path: &PathBuf) -> bool {
    let metadata = match fs::metadata(path).await {
        Ok(metadata) => metadata,
        Err(_) => return false,
    };

    #[cfg(unix)]
    {
        metadata.permissions().mode() & 0o111 != 0
    }

    #[cfg(not(unix))]
    {
        // We don't have a good way of sorting out if a file is executable or not on Windows or
        // other platforms so for now we just assume if it is indeed a file, we're good to go.
        metadata.is_file()
    }
}

async fn find_executable_in_path(executable_name: &str) -> Option<PathBuf> {
    // Get the PATH environment variable and split it into directories
    if let Ok(paths) = env::var("PATH") {
        for path in env::split_paths(&paths) {
            let executable_path = path.join(executable_name);

            // Check if the path is a file and is executable
            if executable_path.is_file() && is_executable(&executable_path).await {
                return Some(executable_path);
            }
        }
    }
    None
}

async fn find_pip() -> Result<PathBuf, Error> {
    if let Some(path) = find_executable_in_path("pip").await {
        Ok(path)
    } else {
        Err(Error::MissingPip)
    }
}

async fn find_python() -> Result<PathBuf, Error> {
    if let Some(path) = find_executable_in_path("python").await {
        Ok(path)
    } else {
        Err(Error::MissingPython)
    }
}

impl App for LocalApp {
    async fn start(opts: StartOptions) -> Result<Self, Error> {
        let package = opts.package;
        let package_path = package.unpacked_path
            .clone()
            .unwrap()
            .to_path_buf();

        let pip_path = find_pip().await?;
        log::debug!("using pip at {:?}", pip_path);

        let python_path = find_python().await?;
        log::debug!("using python at {:?}", python_path);

        // set for later on.
        let working_dir = if let Some(dir) = opts.cwd {
            dir 
        } else {
            current_dir().unwrap()
        };

        if Path::new(&package_path.join("requirements.txt")).exists() {
            log::debug!("requirements.txt file found. installing dependencies");

            let res = Command::new(pip_path)
                .current_dir(&working_dir)
                .arg("install")
                .arg("-r")
                .arg(package_path.join("requirements.txt"))
                .kill_on_drop(true)
                .spawn();

            if let Ok(mut child) = res {
                // Wait for the child to complete entirely.
                child.wait().await.expect("child failed to exit");
            }
        } else {
            log::debug!("missing requirements.txt file found. no dependencies to install");
        }

        log::debug!(" - working directory: {:?}", &working_dir);
        log::debug!(" - python script {}", package.manifest.invoke);

        let res = Command::new(python_path)
            .current_dir(&working_dir)
            .arg("-u")
            .arg(package_path.join(package.manifest.invoke.clone()))
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .envs(make_env_vars(&opts.secrets))
            .kill_on_drop(true)
            .spawn();

        if let Ok(child) = res {
            let child = Arc::new(Mutex::new(child));
            let (sx, rx) = oneshot::channel::<i32>();

            tokio::spawn(wait_for_process(sx, Arc::clone(&child)));

            Ok(Self {
                package: Some(package),
                child: Some(child),
                waiter: Some(rx),
                status: None,
            })
        } else {
            log::error!("failed to spawn process: {}", res.err().unwrap());
            Err(Error::SpawnFailed)
        }
    }

    async fn status(&mut self) -> Result<Status, Error> {
        if let Some(status) = self.status {
            Ok(status)
        } else {
            if let Some(waiter) = &mut self.waiter {
                let res = waiter.try_recv();
                let res = match res {
                    Err(TryRecvError::Empty) => Status::Running,
                    Err(TryRecvError::Closed) => Status::Crashed,
                    Ok(t) => {
                        // We save this for the next time this gets called.
                        if t == 0 {
                            self.status = Some(Status::Exited);
                            Status::Exited
                        } else {
                            self.status = Some(Status::Crashed);
                            Status::Crashed
                        }
                    }
                };
                Ok(res)
            } else {
                Ok(Status::None)
            }
        }
    }

    async fn terminate(&mut self) -> Result<(), Error> {
        if let Some(proc) = &mut self.child {
            let mut child = proc.lock().await;

            if let Err(err) = child.kill().await {
                log::warn!("failed to terminate app: {}", err);
                Err(Error::TerminateFailed)
            } else {
                Ok(())
            }
        } else {
            // Nothing to terminate. Should this be an error?
            Ok(())
        }
    }

    async fn output(&self) -> Result<OutputChannel, Error> {
        if let Some(proc) = &self.child {
            let mut child = proc.lock().await;

            let (sx, rx) = channel::<Output>(1);

            let stdout = child.stdout.take().expect("no stdout");
            tokio::spawn(drain_output(FD::Stdout, sx.clone(), BufReader::new(stdout)));

            let stderr = child.stderr.take().expect("no stderr");
            tokio::spawn(drain_output(FD::Stderr, sx.clone(), BufReader::new(stderr)));

            Ok(Arc::new(Mutex::new(rx)))
        } else {
            Err(Error::NoRunningApp)
        }
    }
}

fn make_env_var_key(src: &str) -> String {
    // TODO: We have this special case defined for dltHub, and I'm not sure that we want to...
    if src.starts_with("dlt.") {
        src.strip_prefix("dlt.").unwrap().to_uppercase().replace(".", "__")
    } else {
        src.to_string()
    }
}

fn make_env_vars(src: &HashMap<String, String>) -> HashMap<String, String> {
    let mut res = HashMap::new();

    log::debug!("converting {} env variables", src.len());

    for (key, value) in src.into_iter() {
        log::debug!("adding key {}", make_env_var_key(&key));
        res.insert(make_env_var_key(&key), value.to_string());
    }

    res
}

async fn wait_for_process(sx: oneshot::Sender<i32>, proc: Arc<Mutex<Child>>) {
    let code = loop {
        let mut child = proc.lock().await;
        let timeout = timeout(Duration::from_millis(250), child.wait()).await;

        if let Ok(res) = timeout {

            if let Ok(status) = res {
                break status.code().expect("no status code");
            } else {
                // something went wrong.
                log::error!("failed to get status due to some kind of IO error: {}" , res.err().expect("no error somehow"));
                break -1;
            }
        }
    };

    log::debug!("process exited with code {}", code);

    // this just shuts up the compiler about ignoring the results.
    let _ = sx.send(code);
}

async fn drain_output<R: AsyncRead + Unpin>(fd: FD, output: Sender<Output>, input: BufReader<R>) {
    let mut lines = input.lines();

    while let Some(line) = lines.next_line().await.expect("line iteration fialed") {
        let _ = output.send(Output{ 
            fd,
            line,
            time: chrono::Utc::now(),
        }).await;
    }
}

