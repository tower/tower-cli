use std::collections::HashMap;
use std::env;
use std::path::PathBuf;
use std::process::Stdio;

#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;

use crate::{errors::Error, AppFailure, OutputSender, StartOptions, Status};

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

use crate::{App, Channel, Output, FD};

/// Result of running an app to completion. The spawned execution task always
/// sends one of these on its waiter channel before exiting, so `status()` can
/// distinguish a real platform failure from a closed channel.
///
/// `Failed(AppFailure)` preserves the structured `Error` (or panic payload)
/// so consumers can act on the variant directly — `error_code` / `error_message`
/// stringification is the consumer's responsibility.
#[derive(Clone, Debug)]
enum AppCompletion {
    /// Child process exited (0 = clean, non-zero = crashed).
    Exit(i32),
    /// The cancellation token fired — explicit termination, not a failure.
    /// Distinct from `Exit(non_zero)` so consumers can tell a deliberate stop
    /// apart from a real crash.
    Cancelled,
    /// Platform-level failure inside the spawned task before/around the child
    /// process (e.g. `tower_uv::Error`, env join failure, panic).
    Failed(AppFailure),
}

/// Best-effort extraction of a panic message from a `catch_unwind` payload.
fn panic_payload_message(payload: &Box<dyn std::any::Any + Send>) -> String {
    if let Some(s) = payload.downcast_ref::<&'static str>() {
        (*s).to_string()
    } else if let Some(s) = payload.downcast_ref::<String>() {
        s.clone()
    } else {
        "execute_local_app panicked with non-string payload".to_string()
    }
}

pub struct LocalApp {
    status: Mutex<Option<Status>>,

    // waiter is what we use to communicate that the overall process is finished by the execution
    // handle. The spawned task always sends an `AppCompletion` before it ends; if the channel
    // ever closes without a send, that's a real bug (task aborted, runtime dropped) and surfaces
    // as `Error::WaiterClosed`.
    waiter: Mutex<oneshot::Receiver<AppCompletion>>,

    // terminator is what we use to flag that we want to terminate the child process.
    terminator: CancellationToken,

    // execute_handle keeps track of the current state of the execution lifecycle.
    execute_handle: Option<JoinHandle<()>>,
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

/// Run the app to completion, returning the child's exit code on success or an
/// `Error` for any platform failure. Cancellation is reported as `Ok(-1)` to
/// preserve the historical `Status::Crashed { code: -1 }` semantic.
///
/// The caller is responsible for delivering the result on the waiter channel —
/// see `LocalApp::start`, which wraps this in `catch_unwind` and an unconditional
/// `sx.send(AppCompletion::...)` so that no failure path can silently close the
/// channel.
async fn inner_execute_local_app(
    opts: StartOptions,
    cancel_token: CancellationToken,
) -> Result<i32, Error> {
    let ctx = opts.ctx.clone();
    let package = opts.package;
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
    let other_env_vars = opts.env_vars;

    let import_paths: Vec<PathBuf> = package
        .manifest
        .import_paths
        .iter()
        .map(|p| package_path.join(p))
        .collect();

    if !import_paths.is_empty() {
        debug!(ctx: &ctx, "adding import paths to PYTHONPATH: {:?}", import_paths);
    }

    // We insert these checks for cancellation along the way to see if the process was
    // terminated by someone.
    //
    // We do this before instantiating `Uv` because that can be somewhat time consuming. Likewise
    // this stops us from instantiating a bash process.
    if cancel_token.is_cancelled() {
        return Err(Error::Cancelled);
    }

    if is_bash_package(&package) {
        let child = execute_bash_program(
            &ctx,
            working_dir,
            package_path,
            &manifest,
            secrets,
            params,
            other_env_vars,
            &import_paths,
        )
        .await?;

        let code = wait_for_process(ctx.clone(), &cancel_token, child).await;
        // `wait_for_process` returns -1 on both cancellation and IO error;
        // disambiguate so a cancellation surfaces as `Status::Cancelled`
        // rather than `Status::Crashed { code: -1 }`.
        if cancel_token.is_cancelled() {
            return Err(Error::Cancelled);
        }
        Ok(code)
    } else {
        // we put Uv in to protected mode when there's no caching configured/enabled.
        let protected_mode = opts.cache_dir.is_none();

        let uv = Uv::new(opts.cache_dir, protected_mode).await?;
        let env_vars = make_env_vars(
            &ctx,
            &package_path,
            &secrets,
            &params,
            &other_env_vars,
            &import_paths,
        );

        // Now we also need to find the program to execute.
        let program_path = working_dir.join(&manifest.invoke);

        // Quickly do a check to see if there was a cancellation before we do a subprocess spawn to
        // ensure everything is in place.
        if cancel_token.is_cancelled() {
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
        let res = wait_for_process(ctx.clone(), &cancel_token, child).await;

        // Distinguish cancellation from a real uv-venv non-zero exit.
        if cancel_token.is_cancelled() {
            return Err(Error::Cancelled);
        }

        if res != 0 {
            // `uv venv` exited non-zero — surface as a crash with the child's
            // exit code. `Status::Failed` is reserved for platform errors
            // where the child never ran at all.
            return Ok(res);
        }

        // Check once more if the process was cancelled before we do a uv sync. The sync itself,
        // once started, will take a while and we have logic for checking for cancellation.
        if cancel_token.is_cancelled() {
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
            Ok(child) => {
                let mut res =
                    run_setup_child(&ctx, &cancel_token, &opts.output_sender, child).await;

                // If sync was cancelled, don't bother retrying — bail out
                // cleanly so the receiver sees `Status::Cancelled` instead of
                // `Status::Crashed { code: -1 }`.
                if cancel_token.is_cancelled() {
                    return Err(Error::Cancelled);
                }

                // If the install failed, retry with the legacy setuptools<82
                // pin. Some apps (those whose transitive deps rely on
                // pkg_resources) need that pin to install successfully; we don't
                // apply it by default because it conflicts with apps whose deps
                // require setuptools>=82.
                if res != 0 {
                    let _ = opts.output_sender.send(Output {
                        channel: Channel::Setup,
                        fd: FD::Stdout,
                        line: "tower: dependency install failed; retrying with setuptools<82 pin for pkg_resources compatibility".to_string(),
                        time: chrono::Utc::now(),
                    });

                    let retry_child = uv
                        .sync_with_legacy_setuptools_pin(&working_dir, &env_vars)
                        .await?;
                    res = run_setup_child(&ctx, &cancel_token, &opts.output_sender, retry_child)
                        .await;
                    if cancel_token.is_cancelled() {
                        return Err(Error::Cancelled);
                    }
                }

                if res != 0 {
                    // `uv sync` exited non-zero — surface as a crash with the
                    // child's exit code. `Status::Failed` is reserved for
                    // platform errors where the child never ran at all.
                    return Ok(res);
                }
            }
        }

        // Check once more to see if the process was cancelled, this will bail us out early.
        if cancel_token.is_cancelled() {
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

        let code = wait_for_process(ctx.clone(), &cancel_token, child).await;
        if cancel_token.is_cancelled() {
            return Err(Error::Cancelled);
        }
        Ok(code)
    }
}

impl Drop for LocalApp {
    fn drop(&mut self) {
        // CancellationToken::cancel() is not async
        self.terminator.cancel();

        // Optionally spawn a task to wait for the handle
        if let Some(execute_handle) = self.execute_handle.take() {
            if let Ok(handle) = Handle::try_current() {
                handle.spawn(async move {
                    let _ = execute_handle.await;
                });
            }
        }
    }
}

impl App for LocalApp {
    async fn start(opts: StartOptions) -> Result<Self, Error> {
        use futures::FutureExt;
        use std::panic::AssertUnwindSafe;

        let terminator = CancellationToken::new();

        let (sx, rx) = oneshot::channel::<AppCompletion>();
        let waiter = Mutex::new(rx);

        let task_terminator = terminator.clone();
        let handle = tokio::spawn(async move {
            // `catch_unwind` turns a panic inside the spawned task into a normal
            // `Err(payload)` so we can still report it on the waiter channel
            // instead of leaving the receiver to observe a silently-closed
            // channel (the historical `WaiterClosed` bug).
            //
            // `Err(Error::Cancelled)` is special-cased: cancellation is a
            // deliberate stop, not a failure, so it surfaces as
            // `AppCompletion::Cancelled` → `Status::Cancelled` rather than
            // `AppCompletion::Failed(AppFailure::Runtime(Error::Cancelled))`.
            let completion = match AssertUnwindSafe(inner_execute_local_app(opts, task_terminator))
                .catch_unwind()
                .await
            {
                Ok(Ok(code)) => AppCompletion::Exit(code),
                Ok(Err(Error::Cancelled)) => AppCompletion::Cancelled,
                Ok(Err(e)) => AppCompletion::Failed(AppFailure::Runtime(e)),
                Err(panic) => {
                    AppCompletion::Failed(AppFailure::Panic(panic_payload_message(&panic)))
                }
            };
            let _ = sx.send(completion);
        });
        let execute_handle = Some(handle);

        Ok(Self {
            execute_handle,
            terminator,
            waiter,
            status: Mutex::new(None),
        })
    }

    async fn terminate(&mut self) -> Result<(), Error> {
        self.terminator.cancel();

        // Now we should wait for the join handle to finish.
        if let Some(execute_handle) = self.execute_handle.take() {
            let _ = execute_handle.await;
            self.execute_handle = None;
        }

        Ok(())
    }

    async fn status(&self) -> Result<Status, Error> {
        let mut status = self.status.lock().await;

        if let Some(status) = status.clone() {
            Ok(status)
        } else {
            let mut waiter = self.waiter.lock().await;
            let res = waiter.try_recv();

            match res {
                Err(TryRecvError::Empty) => Ok(Status::Running),
                // The spawned task always sends an `AppCompletion` before
                // exiting, so a closed channel here means the task was
                // aborted or the runtime dropped — a real bug worth
                // surfacing as-is.
                Err(TryRecvError::Closed) => Err(Error::WaiterClosed),
                Ok(AppCompletion::Exit(0)) => {
                    *status = Some(Status::Exited);
                    Ok(Status::Exited)
                }
                Ok(AppCompletion::Exit(code)) => {
                    let next_status = Status::Crashed { code };
                    *status = Some(next_status.clone());
                    Ok(next_status)
                }
                Ok(AppCompletion::Cancelled) => {
                    *status = Some(Status::Cancelled);
                    Ok(Status::Cancelled)
                }
                Ok(AppCompletion::Failed(failure)) => {
                    let next_status = Status::Failed(failure);
                    *status = Some(next_status.clone());
                    Ok(next_status)
                }
            }
        }
    }
}

async fn execute_bash_program(
    ctx: &tower_telemetry::Context,
    cwd: PathBuf,
    package_path: PathBuf,
    manifest: &Manifest,
    secrets: HashMap<String, String>,
    params: HashMap<String, String>,
    other_env_vars: HashMap<String, String>,
    import_paths: &[PathBuf],
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
            &cwd,
            &secrets,
            &params,
            &other_env_vars,
            import_paths,
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
    cwd: &PathBuf,
    secs: &HashMap<String, String>,
    params: &HashMap<String, String>,
    other_env_vars: &HashMap<String, String>,
    import_paths: &[PathBuf],
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

    let mut path_entries: Vec<PathBuf> = res
        .remove("PYTHONPATH")
        .as_deref()
        .map(env::split_paths)
        .into_iter()
        .flatten()
        .collect();
    path_entries.extend(import_paths.iter().cloned());
    path_entries.push(cwd.clone());

    let pythonpath = env::join_paths(&path_entries)
        .unwrap()
        .to_string_lossy()
        .to_string();
    res.insert("PYTHONPATH".to_string(), pythonpath);

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

async fn run_setup_child(
    ctx: &tower_telemetry::Context,
    cancel_token: &CancellationToken,
    output_sender: &OutputSender,
    mut child: Child,
) -> i32 {
    let stdout = child.stdout.take().expect("no stdout");
    tokio::spawn(drain_output(
        FD::Stdout,
        Channel::Setup,
        output_sender.clone(),
        BufReader::new(stdout),
    ));

    let stderr = child.stderr.take().expect("no stderr");
    tokio::spawn(drain_output(
        FD::Stderr,
        Channel::Setup,
        output_sender.clone(),
        BufReader::new(stderr),
    ));

    wait_for_process(ctx.clone(), cancel_token, child).await
}

async fn wait_for_process(
    ctx: tower_telemetry::Context,
    cancel_token: &CancellationToken,
    mut child: Child,
) -> i32 {
    let code = loop {
        if cancel_token.is_cancelled() {
            debug!(ctx: &ctx, "process cancelled, terminating child process");
            kill_child_process(&ctx, child).await;
            break -1; // return -1 to indicate that the process was cancelled.
        }

        let timeout = timeout(Duration::from_millis(25), child.wait()).await;

        if let Ok(res) = timeout {
            if let Ok(status) = res {
                break status.code().expect("no status code");
            } else {
                // something went wrong.
                debug!(ctx: &ctx, "failed to get status due to some kind of IO error: {}" , res.err().expect("no error somehow"));
                break -1;
            }
        }
    };

    debug!(ctx: &ctx, "process exited with code {}", code);

    // this just shuts up the compiler about ignoring the results.
    code
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
