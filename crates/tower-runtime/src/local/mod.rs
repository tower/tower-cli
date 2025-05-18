use std::path::PathBuf;
use std::process::Stdio;
use std::collections::HashMap;

use tokio::{
    io::{
        AsyncRead,
        BufReader,
        AsyncBufReadExt,
    },
    sync::mpsc::{
        UnboundedReceiver,
        UnboundedSender,
    },
    process::{Command, Child},
};

use tower_package::Package;

use crate::{
    Output,
    Error,
    launcher::{
        AppLauncher,
        AppStatus
    }
};


pub struct LocalAppLauncher {
    // TODO: Something?
}

impl AppLauncher for LocalAppLauncher {
    type Pid = u32;

    async fn setup(&self, package: &Package) -> Result<((), UnboundedReceiver<Output>), Error> {
        let (sender, receiver) = tokio::sync::mpsc::unbounded_channel();

        // We wait for the process to finish synchronously for setup.
        wait_for_process(sender, proc).await;

        // Perform setup for the app
        Ok(((), receiver))
    }

    async fn start(&self, package: &Package) -> Result<(Self::Pid, UnboundedReceiver<Output>), Error> {
        let (sender, receiver) = tokio::sync::mpsc::unbounded_channel();

        // Start the app and return its pid
        Ok(0)
    }

    async fn status(&self, pid: &Self::Pid) -> Result<AppStatus, Error> {
        // Get the status of the app
        Ok(AppStatus { exit_code: None })
    }

    async fn terminate(&self, pid: &Self::Pid) -> Result<(), Error> {
        // Terminate the app
        Ok(())
    }
}

async fn drain_output<R: AsyncRead + Unpin>(fd: FD, channel: Channel, output: UnboundedSender<Output>, input: BufReader<R>) {
    let mut lines = input.lines();

    while let Some(line) = lines.next_line().await.expect("line iteration fialed") {
        let _ = output.send(Output{ 
            channel,
            fd,
            line,
            time: chrono::Utc::now(),
        });
    }
}

async fn wait_for_process(sx: oneshot::Sender<i32>, proc: Child) {
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

struct ProgramOptions {
    executable_path: String,
    environment: String,
    working_dir: String,
    
}


async fn execute_program(
    path: &str,
    working_dir: &PathBuf,
    args: &[&str],
    env_vars: HashMap<String, String>,
) -> Result<Child, Error> {
    let mut cmd = Command::new(path)
        .envs(env_vars)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true)
        .current_dir(&working_dir);

    for arg in args.iter() {
        cmd = cmd.arg(arg);
    } 

    Ok(cmd.spawn()?)
}
