use async_trait::async_trait;
use std::collections::HashMap;
use std::env;
use std::path::PathBuf;
use std::process::Stdio;

#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;

use crate::{errors::Error, OutputSender, StartOptions, Status};

use tokio::{
    fs,
    io::{AsyncBufReadExt, AsyncRead, BufReader},
    process::{Child, Command},
    runtime::Handle,
    sync::{
        oneshot::{self, error::TryRecvError},
        Mutex,
    },
    task::JoinHandle,
    time::{timeout, Duration},
};

#[cfg(unix)]
use nix::{
    sys::signal::{killpg, Signal},
    unistd::Pid,
};

use tokio_util::sync::CancellationToken;

use tower_package::{Manifest, Package};
use tower_telemetry::debug;
use tower_uv::Uv;

use crate::execution::App;
use crate::{Channel, Output, OutputReceiver, FD};

type Completion = Result<Status, Error>;

pub struct LocalApp {
    id: String,
    status: Mutex<Option<Status>>,
    completion_receiver: Mutex<oneshot::Receiver<Completion>>,
    terminator: CancellationToken,
    task: Option<JoinHandle<Result<(), Error>>>,
    output_receiver: Mutex<Option<OutputReceiver>>,
    _package: Option<Package>,
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

async fn find_executable_in_path_buf(executable_name: &str, dir: PathBuf) -> Option<PathBuf> {
    let executable_path = dir.join(executable_name);

    // Check if the path is a file and is executable
    if executable_path.is_file() && is_executable(&executable_path).await {
        return Some(executable_path);
    }
    None
}

async fn find_executable_in_path(executable_name: &str) -> Option<PathBuf> {
    // Get the PATH environment variable and split it into directories
    if let Ok(paths) = env::var("PATH") {
        for path in env::split_paths(&paths) {
            if let Some(path) = find_executable_in_path_buf(executable_name, path).await {
                return Some(path);
            }
        }
    }
    None
}

async fn find_bash() -> Result<PathBuf, Error> {
    if let Some(path) = find_executable_in_path("bash").await {
        Ok(path)
    } else {
        Err(Error::MissingBash)
    }
}

async fn execute_local_app(
    opts: StartOptions,
    tx: oneshot::Sender<Completion>,
    cancel_token: CancellationToken,
) -> Result<(), Error> {
    let ctx = opts.ctx.clone();
    let package = opts.package;
    let environment = opts.environment;
    let package_path = package.unpacked_path.clone().unwrap().to_path_buf();

    // set for later on.
    let working_dir = if package.manifest.version == Some(1) {
        package_path.to_path_buf()
    } else {
        package_path.join(&package.manifest.app_dir_name)
    };

    debug!(ctx: &ctx, " - working directory: {:?}", &working_dir);

    let manifest = &package.manifest;
    let secrets = opts.secrets;
    let params = opts.parameters;
    let mut other_env_vars = opts.env_vars;

    if !package.manifest.import_paths.is_empty() {
        debug!(ctx: &ctx, "adding import paths to PYTHONPATH: {:?}", package.manifest.import_paths);

        let import_paths = package
            .manifest
            .import_paths
            .iter()
            .map(|p| package_path.join(p))
            .collect::<Vec<_>>();

        let import_paths = std::env::join_paths(import_paths)?
            .to_string_lossy()
            .to_string();

        if other_env_vars.contains_key("PYTHONPATH") {
            // If we already have a PYTHONPATH, we need to append to it.
            let existing = other_env_vars.get("PYTHONPATH").unwrap();
            let pythonpath = std::env::join_paths(vec![existing, &import_paths])?
                .to_string_lossy()
                .to_string();

            other_env_vars.insert("PYTHONPATH".to_string(), pythonpath);
        } else {
            // Otherwise, we just set it.
            other_env_vars.insert("PYTHONPATH".to_string(), import_paths);
        }
    }

    // We insert these checks for cancellation along the way to see if the process was
    // terminated by someone.
    //
    // We do this before instantiating `Uv` because that can be somewhat time consuming. Likewise
    // this stops us from instantiating a bash process.
    if cancel_token.is_cancelled() {
        // if there's a waiter, we want them to know that the process was cancelled so we have
        // to return something on the relevant channel.
        let _ = tx.send(Ok(Status::Cancelled));
        return Err(Error::Cancelled);
    }

    if is_bash_package(&package) {
        let child = execute_bash_program(
            &ctx,
            &environment,
            working_dir,
            package_path,
            &manifest,
            secrets,
            params,
            other_env_vars,
        )
        .await?;

        let _ = tx.send(wait_for_process(ctx.clone(), &cancel_token, child).await);
    } else {
        // we put Uv in to protected mode when there's no caching configured/enabled.
        let protected_mode = opts.cache_dir.is_none();

        let uv = Uv::new(opts.cache_dir, protected_mode).await?;
        let env_vars = make_env_vars(
            &ctx,
            &environment,
            &package_path,
            &secrets,
            &params,
            &other_env_vars,
        );

        // Now we also need to find the program to execute.
        let program_path = working_dir.join(&manifest.invoke);

        // Quickly do a check to see if there was a cancellation before we do a subprocess spawn to
        // ensure everything is in place.
        if cancel_token.is_cancelled() {
            // again tell any waiters that we cancelled.
            let _ = tx.send(Ok(Status::Cancelled));
            return Err(Error::Cancelled);
        }

        let mut child = uv.venv(&working_dir, &env_vars).await?;

        // Drain the logs to the output channel.
        let stdout = child.stdout.take().expect("no stdout");
        tokio::spawn(drain_output(
            FD::Stdout,
            Channel::Setup,
            opts.output_sender.clone(),
            BufReader::new(stdout),
        ));

        let stderr = child.stderr.take().expect("no stderr");
        tokio::spawn(drain_output(
            FD::Stderr,
            Channel::Setup,
            opts.output_sender.clone(),
            BufReader::new(stderr),
        ));

        // Wait for venv to finish up.
        match wait_for_process(ctx.clone(), &cancel_token, child).await {
            Ok(Status::Exited) => {}
            res => {
                let _ = tx.send(res);
                return Err(Error::VirtualEnvCreationFailed);
            }
        }

        // Check once more if the process was cancelled before we do a uv sync. The sync itself,
        // once started, will take a while and we have logic for checking for cancellation.
        if cancel_token.is_cancelled() {
            // again tell any waiters that we cancelled.
            let _ = tx.send(Ok(Status::Cancelled));
            return Err(Error::Cancelled);
        }

        match uv.sync(&working_dir, &env_vars).await {
            Err(e) => {
                // If we were missing a pyproject.toml, then that's fine for us--we'll just
                // continue execution.
                //
                // Note that we do a match here instead of an if. That's because of the way
                // tower_uv::Error is implemented. Namely, it doesn't implement PartialEq and can't
                // do so due to it's dependency on std::io::Error.
                match e {
                    tower_uv::Error::MissingPyprojectToml => {
                        debug!(ctx: &ctx, "no pyproject.toml found, continuing without sync");
                    }
                    _ => {
                        // If we got any other error, we want to return it.
                        return Err(e.into());
                    }
                }
            }
            Ok(mut child) => {
                // Drain the logs to the output channel.
                let stdout = child.stdout.take().expect("no stdout");
                tokio::spawn(drain_output(
                    FD::Stdout,
                    Channel::Setup,
                    opts.output_sender.clone(),
                    BufReader::new(stdout),
                ));

                let stderr = child.stderr.take().expect("no stderr");
                tokio::spawn(drain_output(
                    FD::Stderr,
                    Channel::Setup,
                    opts.output_sender.clone(),
                    BufReader::new(stderr),
                ));

                // Let's wait for the setup to finish. We don't care about the results.
                match wait_for_process(ctx.clone(), &cancel_token, child).await {
                    Ok(Status::Exited) => {}
                    // If the sync process failed, we want to return an error.
                    res => {
                        let _ = tx.send(res);
                        return Err(Error::DependencyInstallationFailed);
                    }
                }
            }
        }

        // Check once more to see if the process was cancelled, this will bail us out early.
        if cancel_token.is_cancelled() {
            // if there's a waiter, we want them to know that the process was cancelled so we have
            // to return something on the relevant channel.
            let _ = tx.send(Ok(Status::Cancelled));
            return Err(Error::Cancelled);
        }

        let mut child = uv.run(&working_dir, &program_path, &env_vars).await?;

        // Drain the logs to the output channel.
        let stdout = child.stdout.take().expect("no stdout");
        tokio::spawn(drain_output(
            FD::Stdout,
            Channel::Program,
            opts.output_sender.clone(),
            BufReader::new(stdout),
        ));

        let stderr = child.stderr.take().expect("no stderr");
        tokio::spawn(drain_output(
            FD::Stderr,
            Channel::Program,
            opts.output_sender.clone(),
            BufReader::new(stderr),
        ));

        let _ = tx.send(wait_for_process(ctx.clone(), &cancel_token, child).await);
    }

    // Everything was properly executed I suppose.
    return Ok(());
}

impl Drop for LocalApp {
    fn drop(&mut self) {
        // CancellationToken::cancel() is not async
        self.terminator.cancel();

        // Optionally spawn a task to wait for execution to complete
        if let Some(task) = self.task.take() {
            if let Ok(rt) = Handle::try_current() {
                rt.spawn(async move {
                    let _ = task.await;
                });
            }
        }
    }
}

impl LocalApp {
    /// Create a new LocalApp with the given ID and StartOptions.
    ///
    /// The `output_receiver` parameter is optional - when provided (via Backend interface),
    /// the `logs()` method will return this receiver. When None (legacy interface),
    /// logs are sent to the output_sender in StartOptions and `logs()` returns an empty stream.
    ///
    /// The `package` parameter keeps the package (and its temp directory) alive for the
    /// duration of the execution.
    pub async fn new(
        id: String,
        opts: StartOptions,
        output_receiver: Option<OutputReceiver>,
        package: Option<Package>,
    ) -> Result<Self, Error> {
        let terminator = CancellationToken::new();
        let (tx, rx) = oneshot::channel::<Completion>();
        let task = tokio::spawn(execute_local_app(opts, tx, terminator.clone()));

        Ok(Self {
            id,
            task: Some(task),
            terminator,
            completion_receiver: Mutex::new(rx),
            status: Mutex::new(None),
            output_receiver: Mutex::new(output_receiver),
            _package: package,
        })
    }

    /// Create a LocalApp using the legacy start() interface (for backward compatibility).
    ///
    /// Output is sent to the output_sender in StartOptions. The `logs()` method
    /// will return an empty stream (use the output_sender's receiver directly).
    pub async fn start(opts: StartOptions) -> Result<Self, Error> {
        Self::new("local".to_string(), opts, None, None).await
    }
}

#[async_trait]
impl App for LocalApp {
    fn id(&self) -> &str {
        &self.id
    }

    async fn status(&self) -> Result<Status, Error> {
        let mut status = self.status.lock().await;

        if let Some(status) = *status {
            return Ok(status);
        }

        match self.completion_receiver.lock().await.try_recv() {
            Err(TryRecvError::Empty) => Ok(Status::Running),
            Err(TryRecvError::Closed) => Err(Error::WaiterClosed),
            Ok(completion) => {
                let next_status = completion?;
                *status = Some(next_status);
                Ok(next_status)
            }
        }
    }

    async fn logs(&self) -> Result<OutputReceiver, Error> {
        // Take the receiver (can only be called once meaningfully)
        // Returns empty channel if already taken or using legacy interface
        let (_, empty) = tokio::sync::mpsc::unbounded_channel();
        Ok(self.output_receiver.lock().await.take().unwrap_or(empty))
    }

    async fn terminate(&mut self) -> Result<(), Error> {
        self.terminator.cancel();

        if let Some(task) = self.task.take() {
            let _ = task.await;
        }

        Ok(())
    }

    async fn wait_for_completion(&self) -> Result<Status, Error> {
        loop {
            let status = self.status().await?;
            match status {
                Status::None | Status::Running => {
                    tokio::time::sleep(Duration::from_millis(100)).await;
                }
                _ => return Ok(status),
            }
        }
    }
}

async fn execute_bash_program(
    ctx: &tower_telemetry::Context,
    env: &str,
    cwd: PathBuf,
    package_path: PathBuf,
    manifest: &Manifest,
    secrets: HashMap<String, String>,
    params: HashMap<String, String>,
    other_env_vars: HashMap<String, String>,
) -> Result<Child, Error> {
    let bash_path = find_bash().await?;
    debug!(ctx: &ctx, "using bash at {:?}", bash_path);

    debug!(ctx: &ctx, " - bash script {}", manifest.invoke);

    let child = Command::new(bash_path)
        .current_dir(&cwd)
        .arg(package_path.join(manifest.invoke.clone()))
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .envs(make_env_vars(
            &ctx,
            env,
            &cwd,
            &secrets,
            &params,
            &other_env_vars,
        ))
        .kill_on_drop(true)
        .spawn()?;

    Ok(child)
}

fn make_env_var_key(src: &str) -> String {
    // TODO: We have this special case defined for dltHub, and I'm not sure that we want to...
    if src.starts_with("dlt.") {
        src.strip_prefix("dlt.")
            .unwrap()
            .to_uppercase()
            .replace(".", "__")
    } else {
        src.to_string()
    }
}

fn make_env_vars(
    ctx: &tower_telemetry::Context,
    env: &str,
    cwd: &PathBuf,
    secs: &HashMap<String, String>,
    params: &HashMap<String, String>,
    other_env_vars: &HashMap<String, String>,
) -> HashMap<String, String> {
    let mut res = HashMap::new();

    debug!(ctx: &ctx, "converting {} env variables", (params.len() + secs.len()));

    for (key, value) in secs.into_iter() {
        res.insert(make_env_var_key(&key), value.to_string());
    }

    for (key, value) in params.into_iter() {
        res.insert(key.to_string(), value.to_string());
    }

    for (key, value) in other_env_vars.into_iter() {
        res.insert(key.to_string(), value.to_string());
    }

    let added_keys = res.keys().map(|s| &**s).collect::<Vec<&str>>().join(", ");
    debug!(ctx: &ctx, "added keys {}", &added_keys);

    // We also need a PYTHONPATH that is set to the current working directory to help with the
    // dependency resolution problem at runtime.
    let pythonpath = cwd.to_string_lossy().to_string();
    let pythonpath = if res.contains_key("PYTHONPATH") {
        // If we already have a PYTHONPATH, we need to append to it.
        let existing = res.get("PYTHONPATH").unwrap();
        let joined_paths = std::env::join_paths([existing, &pythonpath]).unwrap();
        joined_paths.to_string_lossy().to_string()
    } else {
        // There was no previously set PYTHONPATH, so we just include our current directory.
        pythonpath
    };

    res.insert("PYTHONPATH".to_string(), pythonpath);

    // Inject a TOWER_ENVIRONMENT parameter so you know what environment you're running in. Empty
    // environment is "default" by default.
    if env.is_empty() {
        res.insert("TOWER_ENVIRONMENT".to_string(), "default".to_string());
    } else {
        res.insert("TOWER_ENVIRONMENT".to_string(), env.to_string());
    }

    res.insert("PYTHONUNBUFFERED".to_string(), "x".to_string());

    res
}

#[cfg(unix)]
async fn kill_child_process(ctx: &tower_telemetry::Context, mut child: Child) {
    let pid = match child.id() {
        Some(pid) => pid,
        None => {
            // We didn't get anything, so we can't do anything. Let's just exit with a debug
            // message.
            tower_telemetry::error!(ctx: &ctx, "child process has no pid, cannot kill");
            return;
        }
    };

    // This is the actual converted pid.
    let pid = Pid::from_raw(pid as i32);

    // We first send a SIGTERM to ensure that the child processes are terminated. Using SIGKILL
    // (default behavior in Child::kill) can leave orphaned processes behind.
    killpg(pid, Signal::SIGTERM).ok();

    // If it doesn't die after 2 seconds then we'll forcefully kill it. This timeout should be less
    // than the overall timeout for the process (which should likely live on the context as a
    // deadline).
    let timeout = timeout(Duration::from_secs(2), child.wait()).await;

    if timeout.is_err() {
        killpg(pid, Signal::SIGKILL).ok();
    }
}

#[cfg(not(unix))]
async fn kill_child_process(ctx: &tower_telemetry::Context, mut child: Child) {
    match child.kill().await {
        Ok(_) => debug!(ctx: &ctx, "child process killed successfully"),
        Err(e) => debug!(ctx: &ctx, "failed to kill child process: {}", e),
    };
}

async fn wait_for_process(
    ctx: tower_telemetry::Context,
    cancel_token: &CancellationToken,
    mut child: Child,
) -> Completion {
    loop {
        if cancel_token.is_cancelled() {
            debug!(ctx: &ctx, "process cancelled, terminating child process");
            kill_child_process(&ctx, child).await;
            return Ok(Status::Cancelled);
        }

        match timeout(Duration::from_millis(25), child.wait()).await {
            Err(_) => continue, // timeout, check cancellation again
            Ok(Err(e)) => {
                debug!(ctx: &ctx, "IO error waiting on child process: {}", e);
                return Err(Error::ProcessWaitFailed {
                    message: e.to_string(),
                });
            }
            Ok(Ok(status)) => {
                let code = status.code().expect("process should have exit code");
                debug!(ctx: &ctx, "process exited with code {}", code);
                return Ok(match code {
                    0 => Status::Exited,
                    _ => Status::Crashed { code },
                });
            }
        }
    }
}

async fn drain_output<R: AsyncRead + Unpin>(
    fd: FD,
    channel: Channel,
    output: OutputSender,
    input: BufReader<R>,
) {
    let mut lines = input.lines();

    while let Some(line) = lines.next_line().await.expect("line iteration fialed") {
        let _ = output.send(Output {
            channel,
            fd,
            line,
            time: chrono::Utc::now(),
        });
    }
}

fn is_bash_package(package: &Package) -> bool {
    return package.manifest.invoke.ends_with(".sh");
}
