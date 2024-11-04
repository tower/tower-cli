use std::path::Path;
use std::env::current_dir;
use std::process::Stdio;
use std::sync::Arc;
use std::collections::HashMap;

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
    io::{AsyncRead, BufReader, AsyncBufReadExt},
    time::{timeout, Duration},
    sync::Mutex,
    sync::mpsc::Sender,
    process::Child, 
};

use tower_package::Manifest;

use crate::{
    FD,
    App,
    Output,
    OutputChannel,
};

pub struct LocalApp {
    child: Option<Arc<Mutex<Child>>>,
    status: Option<Status>,
    waiter: Option<oneshot::Receiver<i32>>,
}

impl Default for LocalApp {
    fn default() -> Self {
        Self {
            child: None,
            status: None,
            waiter: None,
        }
    }
}

impl App for LocalApp {
    async fn start(opts: StartOptions) -> Result<Self, Error> {
        log::info!("LocalApp: starting application");
        let res = Manifest::from_file(&opts.path.join("MANIFEST")).await;

        // set for later on.
        let working_dir = if let Some(dir) = opts.cwd {
            dir 
        } else {
            current_dir().unwrap()
        };

        if let Ok(manifest) = res {
            if Path::new(&opts.path.join("requirements.txt")).exists() {
                log::info!("requirements.txt file found. installing dependencies");

                let res = Command::new("/usr/local/bin/pip")
                    .current_dir(&working_dir)
                    .arg("install")
                    .arg("-r")
                    .arg(opts.path.join("requirements.txt"))
                    .kill_on_drop(true)
                    .spawn();

                if let Ok(mut child) = res {
                    // Wait for the child to complete entirely.
                    child.wait().await.expect("child failed to exit");
                }
            } else {
                log::info!("missing requirements.txt file found. no dependencies to install");
            }

            let res = Command::new("/usr/local/bin/python")
                .current_dir(&working_dir)
                .arg("-u")
                .arg(opts.path.join(manifest.invoke))
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
                    child: Some(child),
                    waiter: Some(rx),
                    status: None,
                })
            } else {
                log::error!("failed to spawn process: {}", res.err().unwrap());
                Err(Error::SpawnFailed)
            }
        } else {
            log::error!("failed to get manifest: {:?}", res.err());
            Err(Error::MissingManifest)
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
        let _ = output.send(Output{ fd, line }).await;
    }
}

