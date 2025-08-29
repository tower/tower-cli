use anyhow::Result;
use clap::{Arg, ArgMatches, Command};
use config::{Config, Towerfile};
use std::collections::HashMap;
use std::path::PathBuf;
use tower_package::{Package, PackageSpec};
use tower_runtime::{local::LocalApp, App, AppLauncher, OutputReceiver};
use tower_telemetry::{Context, debug};
use tower_api::models::Run;

use tokio::sync::{
    oneshot::self,
    mpsc::unbounded_channel,
};

use crate::{
    util::dates,
    output,
    api,
    Error,
};

pub fn run_cmd() -> Command {
    Command::new("run")
        .allow_external_subcommands(true)
        .arg(
            Arg::new("dir")
                .long("dir")
                .help("The directory containing the Towerfile")
                .default_value("."),
        )
        .arg(
            Arg::new("local")
                .long("local")
                .default_value("false")
                .help("Run this app locally")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("environment")
                .long("environment")
                .short('e')
                .help("The environment to invoke the app in")
                .default_value("default"),
        )
        .arg(
            Arg::new("parameters")
                .short('p')
                .long("parameter")
                .help("Parameters (key=value) to pass to the app")
                .action(clap::ArgAction::Append),
        )
        .arg(
            Arg::new("detached")
                .long("detached")
                .short('d')
                .help("Don't follow the run output in your CLI")
                .action(clap::ArgAction::SetTrue),
        )
        .about("Run your code in Tower or locally")
}

pub async fn do_run(config: Config, args: &ArgMatches, cmd: Option<(&str, &ArgMatches)>) {
    if let Err(e) = do_run_inner(config, args, cmd).await {
        eprintln!("{}", e);
        std::process::exit(1);
    }
}

/// do_run is the primary entrypoint into running apps both locally and remotely in Tower. It will
/// use the configuration to determine the requested way of running a Tower app.
pub async fn do_run_inner(config: Config, args: &ArgMatches, cmd: Option<(&str, &ArgMatches)>) -> Result<()> {
    let res = get_run_parameters(args, cmd);

    // We always expect there to be an environment due to the fact that there is a
    // default value.
    let env = args.get_one::<String>("environment").unwrap();

    match res {
        Ok((local, path, params, app_name)) => {
            debug!(
                "Running app at {}, local: {}",
                path.to_str().unwrap(),
                local
            );

            if local {
                // For the time being, we should report that we can't run an app by name locally.
                if app_name.is_some() {
                    anyhow::bail!("Running apps by name locally is not supported yet.");
                } else {
                    do_run_local(config, path, env, params).await
                }
            } else {
                let follow = should_follow_run(args);
                do_run_remote(config, path, env, params, app_name, follow).await
            }
        }
        Err(err) => {
            Err(err.into())
        }
    }
}

/// Core implementation for running an app locally with configurable output handling
async fn do_run_local_impl<F, Fut, T>(
    config: Config,
    path: PathBuf,
    env: &str,
    mut params: HashMap<String, String>,
    output_handler: F,
) -> Result<T>
where
    F: FnOnce(OutputReceiver) -> Fut,
    Fut: std::future::Future<Output = T> + Send + 'static,
    T: Send + 'static,
{
    let mut spinner = output::spinner("Setting up runtime environment...");

    // Load all the secrets and catalogs from the server
    let secrets = get_secrets(&config, &env).await?;
    let catalogs = get_catalogs(&config, &env).await?;

    spinner.success();

    // We prepare all the other misc environment variables that we need to inject
    let mut env_vars = HashMap::new();
    env_vars.extend(catalogs);
    env_vars.insert("TOWER_URL".to_string(), config.tower_url.to_string());

    // There should always be a session, if there isn't one then I'm not sure how we got here?
    let session = config.session.ok_or_else(|| anyhow::anyhow!("No session found. Please log in to Tower first."))?;

    env_vars.insert("TOWER_JWT".to_string(), session.token.jwt.to_string());

    // Load the Towerfile
    let towerfile_path = path.join("Towerfile");
    let towerfile = load_towerfile(&towerfile_path)?;

    for param in &towerfile.parameters {
        if !params.contains_key(&param.name) {
            params.insert(param.name.clone(), param.default.clone());
        }
    }

    // Build the package
    let mut package = build_package(&towerfile).await?;

    // Unpack the package
    package.unpack().await?;

    let (sender, receiver) = unbounded_channel();

    output::success(&format!("Launching app `{}`", towerfile.app.name));
    let output_task = tokio::spawn(output_handler(receiver));

    let mut launcher: AppLauncher<LocalApp> = AppLauncher::default();
    launcher
        .launch(Context::new(), sender, package, env.to_string(), secrets, params, env_vars)
        .await?;

    // Monitor app output and status concurrently
    let app = launcher.app.unwrap();
    let status_task = tokio::spawn(monitor_status(app));

    // Wait for the output task to complete naturally
    let final_result = output_task.await.unwrap();
    
    // The status task can be aborted since we don't need to wait for it
    status_task.abort();
    
    Ok(final_result)
}

/// do_run_local is the entrypoint for running an app locally. It will load the Towerfile, build
/// the package, and launch the app. The relevant package is cleaned up after execution is
/// complete.
pub async fn do_run_local(config: Config, path: PathBuf, env: &str, params: HashMap<String, String>) -> Result<()> {
    do_run_local_impl(config, path, env, params, |receiver| async {
        monitor_output(receiver).await;
        ()
    }).await
}

/// do_run_local_capture is like do_run_local but returns captured output lines instead of printing
pub async fn do_run_local_capture(config: Config, path: PathBuf, env: &str, params: HashMap<String, String>) -> Result<Vec<String>> {
    do_run_local_impl(config, path, env, params, monitor_output_capture).await
}

pub async fn do_run_remote_capture(
    config: Config,
    path: PathBuf,
    env: &str,
    params: HashMap<String, String>,
    app_name: Option<String>,
) -> Result<Vec<String>> {
    let app_slug = if let Some(name) = app_name {
        name
    } else {
        let towerfile_path = path.join("Towerfile");
        let towerfile = load_towerfile(&towerfile_path)?;
        towerfile.app.name
    };

    match api::run_app(&config, &app_slug, env, params).await {
        Err(err) => Err(err.into()),
        Ok(res) => {
            let run = res.run;
            do_follow_run_capture(config, &run).await
        }
    }
}

/// do_run_remote is the entrypoint for running an app remotely. It uses the Towerfile in the
/// supplied directory (locally or remotely) to sort out what application to run exactly.
pub async fn do_run_remote(
    config: Config,
    path: PathBuf,
    env: &str,
    params: HashMap<String, String>,
    app_name: Option<String>,
    should_follow_run: bool,
) -> Result<()> {
    let app_slug = if let Some(name) = app_name {
        name
    } else {
        // Load the Towerfile
        let towerfile_path = path.join("Towerfile");
        let towerfile = load_towerfile(&towerfile_path)?;
        towerfile.app.name
    };

    let mut spinner = output::spinner("Scheduling run...");

    match api::run_app(&config, &app_slug, env, params).await {
        Err(err) => {
            spinner.failure();
            debug!("Failed to schedule run: {}", err);
            Err(err.into())
        }, 
        Ok(res) => {
            spinner.success();

            let run = res.run;

            if should_follow_run {
                do_follow_run(config, &run).await;
            } else {
                let line = format!(
                    "Run #{} for app `{}` has been scheduled",
                    run.number, app_slug
                );
                output::success(&line);

                let link_line = format!("  See more: {}", run.dollar_link);
                output::write(&link_line);
                output::newline();
            }
            Ok(())
        }
    }
}

trait OutputSink: Send + Sync {
    fn send_line(&self, line: String);
    fn send_error(&self, error: String);
}

struct StdoutSink;
impl OutputSink for StdoutSink {
    fn send_line(&self, line: String) {
        output::write(&line);
    }
    fn send_error(&self, error: String) {
        output::failure(&error);
    }
}

struct ChannelSink(tokio::sync::mpsc::UnboundedSender<String>);
impl OutputSink for ChannelSink {
    fn send_line(&self, line: String) {
        let _ = self.0.send(line);
    }
    fn send_error(&self, error: String) {
        let _ = self.0.send(error);
    }
}

pub async fn do_follow_run_capture(
    config: Config,
    run: &Run,
) -> Result<Vec<String>> {
    let (tx, mut rx) = tokio::sync::mpsc::unbounded_channel();
    let sink = ChannelSink(tx);
    
    let result = do_follow_run_impl(config, run, &sink).await;
    
    let mut output_lines = Vec::new();
    while let Ok(line) = rx.try_recv() {
        output_lines.push(line);
    }
    
    result.map(|_| output_lines)
}

async fn do_follow_run(
    config: Config,
    run: &Run,
) {
    let sink = StdoutSink;
    let _ = do_follow_run_impl(config, run, &sink).await;
}

async fn do_follow_run_impl(
    config: Config,
    run: &Run,
    sink: &dyn OutputSink,
) -> Result<()> {
    match wait_for_run_start(&config, &run).await {
        Err(err) => {
            sink.send_error(format!("Failed to wait for run to start: {}", err));
            return Err(err.into());
        },
        Ok(()) => {
            sink.send_line("Run started, streaming logs...".to_string());

            // We do this here, explicitly, to not double-monitor our API via the
            // `wait_for_run_start` function above.
            let mut run_complete = monitor_run_completion(&config, run);

            // Skip Ctrl+C handler for capture mode

            // Now we follow the logs from the run. We can stream them from the cloud to here using
            // the stream_logs API endpoint.
            match api::stream_run_logs(&config, &run.app_name, run.number).await {
                Ok(mut output) => {
                    loop {
                        tokio::select! {
                            Some(event) = output.recv() => {
                                if let api::LogStreamEvent::EventLog(log) = &event {
                                    let ts = dates::format_str(&log.reported_at);
                                    sink.send_line(format!("{}: {}", ts, log.content));
                                }
                            },
                            res = &mut run_complete => {
                                match res {
                                    Ok(completed_run) => {
                                        match completed_run.status {
                                            tower_api::models::run::Status::Errored => {
                                                sink.send_error(format!("Run #{} for app '{}' had an error", completed_run.number, completed_run.app_name));
                                                return Err(anyhow::anyhow!("Run failed with error status"));
                                            },
                                            tower_api::models::run::Status::Crashed => {
                                                sink.send_error(format!("Run #{} for app '{}' crashed", completed_run.number, completed_run.app_name));
                                                return Err(anyhow::anyhow!("Run crashed"));
                                            },
                                            tower_api::models::run::Status::Cancelled => {
                                                sink.send_error(format!("Run #{} for app '{}' was cancelled", completed_run.number, completed_run.app_name));
                                                return Err(anyhow::anyhow!("Run was cancelled"));
                                            },
                                            _ => {
                                                sink.send_line(format!("Run #{} for app '{}' completed successfully", completed_run.number, completed_run.app_name));
                                            }
                                        }
                                    }
                                    Err(err) => {
                                        sink.send_error(format!("Failed to monitor run completion: {:?}", err));
                                        return Err(err.into());
                                    }
                                }
                                break;
                            },
                        };
                    }
                },
                Err(err) => {
                    sink.send_error(format!("Failed to stream run logs: {:?}", err));
                    return Err(anyhow::anyhow!("Failed to stream run logs: {:?}", err));
                }
            }
        }
    };
    
    Ok(())
}

/// get_run_parameters takes care of all the hairy bits around digging about in the `clap`
/// internals to figure out what the user is requesting. In the end, it determines if we are meant
/// to do a local run or a remote run, and it determines the path to the relevant Towerfile that
/// should be loaded.
fn get_run_parameters(
    args: &ArgMatches,
    cmd: Option<(&str, &ArgMatches)>,
) -> Result<(bool, PathBuf, HashMap<String, String>, Option<String>), config::Error> {
    let local = *args.get_one::<bool>("local").unwrap();
    let path = resolve_path(args);
    let params = parse_parameters(args);
    let app_name = get_app_name(cmd);

    Ok((local, path, params, app_name))
}

fn should_follow_run(
    args: &ArgMatches,
) -> bool {
    let local = *args.get_one::<bool>("detached").unwrap();
    !local
}

/// Parses `--parameter` arguments into a HashMap of key-value pairs.
/// Handles format like "--parameter key=value"
fn parse_parameters(args: &ArgMatches) -> HashMap<String, String> {
    let mut param_map = HashMap::new();

    if let Some(parameters) = args.get_many::<String>("parameters") {
        for param in parameters {
            match param.split_once('=') {
                Some((key, value)) => {
                    if key.is_empty() {
                        output::failure(&format!(
                            "Invalid parameter format: '{}'. Key cannot be empty.",
                            param
                        ));
                        continue;
                    }
                    param_map.insert(key.to_string(), value.to_string());
                }
                None => {
                    output::failure(&format!(
                        "Invalid parameter format: '{}'. Expected 'key=value'.",
                        param
                    ));
                }
            }
        }
    }

    param_map
}

/// Resolves the path based on the `cmd` option.
fn resolve_path(args: &ArgMatches) -> PathBuf {
    if let Some(dir) = args.get_one::<String>("dir") {
        PathBuf::from(dir)
    } else {
        PathBuf::from(".")
    }
}

/// get_app_name is a helper function that will extract the app name from the `clap` arguments if
fn get_app_name(cmd: Option<(&str, &ArgMatches)>) -> Option<String> {
    match cmd {
        Some((name, _)) if !name.is_empty() => Some(name.to_string()),
        _ => None,
    }
}

/// get_secrets manages the process of getting secrets from the Tower server in a way that can be
/// used by the local runtime during local app execution.
async fn get_secrets(config: &Config, env: &str) -> Result<HashMap<String, String>, Error> {
    let (private_key, public_key) = crypto::generate_key_pair();

    let res = api::export_secrets(&config, env, false, public_key).await.map_err(|err| {
        debug!("API error fetching secrets: {:?}", err);
        Error::FetchingSecretsFailed
    })?;
    let mut secrets = HashMap::new();

    for secret in res.secrets {
        // we will decrypt each property and inject it into the vals map.
        let decrypted_value = crypto::decrypt(private_key.clone(), secret.encrypted_value.to_string())?;
        secrets.insert(secret.name, decrypted_value);
    }

    Ok(secrets)
}

/// get_catalogs manages the process of exporting catalogs, decrypting their properties, and
/// preparting them for injection into the environment during app execution
async fn get_catalogs(config: &Config, env: &str) -> Result<HashMap<String, String>, Error> {
    let (private_key, public_key) = crypto::generate_key_pair();

    let res = api::export_catalogs(&config, env, false, public_key).await.map_err(|err| {
        debug!("API error fetching catalogs: {:?}", err);
        Error::FetchingCatalogsFailed
    })?;
    let mut vals = HashMap::new();

    for catalog in res.catalogs {
        // we will decrypt each property and inject it into the vals map.
        for property in catalog.properties {
            let decrypted_value = crypto::decrypt(private_key.clone(), property.encrypted_value.to_string())?;
            let name = create_pyiceberg_catalog_property_name(&catalog.name, &property.name);
            vals.insert(name, decrypted_value);
        }
    }

    Ok(vals)
}

/// load_towerfile manages the process of loading a Towerfile from a given path in an interactive
/// way. That means it will not return if the Towerfile can't be loaded and instead will publish an
/// error.
fn load_towerfile(path: &PathBuf) -> Result<Towerfile> {
    Towerfile::from_path(path.clone()).map_err(|err| {
        debug!("Failed to load Towerfile from path `{:?}`: {}", path, err);
        anyhow::anyhow!("Failed to load Towerfile from {}: {}", path.display(), err)
    })
}

/// build_package manages the process of building a package in an interactive way for local app
/// execution. If the pacakge fails to build for wahatever reason, the app will exit.
async fn build_package(towerfile: &Towerfile) -> Result<Package> {
    let mut spinner = output::spinner("Building package...");
    let package_spec = PackageSpec::from_towerfile(towerfile);
    match Package::build(package_spec).await {
        Ok(package) => {
            spinner.success();
            Ok(package)
        }
        Err(err) => {
            spinner.failure();
            debug!("Failed to build package: {}", err);
            Err(err.into())
        }
    }
}

/// monitor_output_capture captures output lines and returns them as a Vec<String>
pub async fn monitor_output_capture(mut output: OutputReceiver) -> Vec<String> {
    let mut lines = Vec::new();
    loop {
        if let Some(line) = output.recv().await {
            let ts = dates::format(line.time);
            let formatted = format!("{}: {}", ts, line.line);
            lines.push(formatted);
        } else {
            break;
        }
    }
    lines
}

/// monitor_output is a helper function that will monitor the output of a given output channel and
/// plops it down on stdout. Refactored to use monitor_output_capture.
async fn monitor_output(output: OutputReceiver) {
    let lines = monitor_output_capture(output).await;
    for line in lines {
        // Extract timestamp and message from the formatted line
        if let Some((ts, msg)) = line.split_once(": ") {
            output::log_line(ts, msg, output::LogLineType::Local);
        }
    }
}

/// monitor_status is a helper function that will monitor the status of a given app and waits for
/// it to progress to a terminal state.
async fn monitor_status(app: LocalApp) {
    debug!("Starting status monitoring for LocalApp");
    let mut check_count = 0;
    let max_checks = 600; // 60 seconds with 100ms intervals
    
    loop {
        debug!("Status check #{}, attempting to get app status", check_count);
        
        match app.status().await {
            Ok(status) => {
                debug!("Got app status (some status)");
                match status {
                    tower_runtime::Status::Exited => {
                        debug!("App exited cleanly, stopping status monitoring");
                        output::success("Your app exited cleanly.");
                        break;
                    }
                    tower_runtime::Status::Crashed { .. } => {
                        debug!("App crashed, stopping status monitoring");
                        output::failure("Your app crashed!");
                        break;
                    }
                    _ => {
                        debug!("App status: other, continuing to monitor");
                        check_count += 1;
                        if check_count >= max_checks {
                            debug!("Status monitoring timed out after {} checks", max_checks);
                            output::error("App status monitoring timed out, but app may still be running");
                            break;
                        }
                        tokio::time::sleep(std::time::Duration::from_millis(100)).await;
                        continue;
                    }
                }
            }
            Err(e) => {
                debug!("Failed to get app status: {:?}", e);
                check_count += 1;
                if check_count >= max_checks {
                    debug!("Failed to get app status after {} attempts, giving up", max_checks);
                    output::error("Failed to get app status after timeout");
                    break;
                }
                tokio::time::sleep(std::time::Duration::from_millis(100)).await;
            }
        }
    }
    debug!("Status monitoring completed");
}

fn create_pyiceberg_catalog_property_name(catalog_name: &str, property_name: &str) -> String {
    let catalog_name = catalog_name.replace('.', "_").replace(':', "_").to_uppercase();
    let property_name = property_name.replace('.', "_").replace(':', "_").to_uppercase();

    format!("PYICEBERG_CATALOG__{}__{}", catalog_name, property_name)
}

/// wait_for_run_start waits for the run to enter a "running" state. It polls the API every 500ms to see
/// if it's started yet.
async fn wait_for_run_start(config: &Config, run: &Run) -> Result<(), Error> {
    loop {
        let res = api::describe_run(config, &run.app_name, run.number).await?;

        if is_run_started(&res.run)? {
            break
        } else {
            // Wait half a second to to try again.
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
        }
    }  

    Ok(())
}

/// wait_for_run_completion waits for the run to enter an terminal state. It polls the API every
/// 500ms to see if it's started yet.
async fn wait_for_run_completion(config: &Config, run: &Run) -> Result<Run, Error> {
    loop {
        let res = api::describe_run(config, &run.app_name, run.number).await?;

        if is_run_finished(&res.run) {
            return Ok(res.run)
        } else {
            // Wait half a second to to try again.
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
        }
    }  
}

/// is_run_started checks if the run has started by looking at its status. 
fn is_run_started(run: &Run) -> Result<bool, Error> {
    match run.status {
        tower_api::models::run::Status::Scheduled => Ok(false),
        tower_api::models::run::Status::Pending => Ok(false),
        tower_api::models::run::Status::Running => Ok(true),
        _ => Err(Error::RunCompleted),
    }
}

/// is_run_finished checks if the run has finished by looking at its status.
fn is_run_finished(run: &Run) -> bool {
    match run.status {
        tower_api::models::run::Status::Scheduled => false,
        tower_api::models::run::Status::Pending => false,
        tower_api::models::run::Status::Running => false,
        _ => true,
    }
}

fn monitor_run_completion(config: &Config, run: &Run) -> oneshot::Receiver<Run> {
    // we'll use this as a way of monitoring for when the run has reached a terminal state.
    let (tx, rx) = oneshot::channel();

    // We need to spawn a task that will wait for run completion, and we need copies of these
    // objects in order for them to run elsewhere.
    let config_clone = config.clone();
    let run_clone = run.clone();

    tokio::spawn(async move {
       let run = wait_for_run_completion(&config_clone, &run_clone).
           await.
           unwrap();

       let _ = tx.send(run);
    });

    rx
}

fn print_log_stream_event(event: api::LogStreamEvent) {
    match event {
        api::LogStreamEvent::EventLog(log) => {
            let ts = dates::format_str(&log.reported_at);

            output::log_line(
                &ts,
                &log.content,
                output::LogLineType::Remote,
            );
        }
        api::LogStreamEvent::EventWarning(warning) => {
            debug!("warning: {:?}", warning);
        }
    }
}

fn print_run_completion(run: &Run) {
    let link_line = format!("  See more: {}", run.dollar_link);

    match run.status {
        tower_api::models::run::Status::Errored => {
            let line = format!(
                "Run #{} for app `{}` had an error",
                run.number, run.app_name
            );
            output::failure(&line);
        },
        tower_api::models::run::Status::Crashed => {
            let line = format!(
                "Run #{} for app `{}` crashed",
                run.number, run.app_name
            );
            output::failure(&line);
        },
        tower_api::models::run::Status::Cancelled => {
            let line = format!(
                "Run #{} for app `{}` was cancelled",
                run.number, run.app_name
            );
            output::failure(&line);
        },
        _ => {
            let line = format!(
                "Run #{} for app `{}` has exited successfully",
                run.number, run.app_name
            );
            output::success(&line);
        }
    }

    output::write(&link_line);
    output::newline();
}
