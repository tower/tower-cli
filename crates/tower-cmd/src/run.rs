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

/// do_run is the primary entrypoint into running apps both locally and remotely in Tower. It will
/// use the configuration to determine the requested way of running a Tower app.
pub async fn do_run(config: Config, args: &ArgMatches, cmd: Option<(&str, &ArgMatches)>) {
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
                    output::die("Running apps by name locally is not supported yet.");
                } else {
                    do_run_local(config, path, env, params).await;
                }
            } else {
                let follow = should_follow_run(args);
                do_run_remote(config, path, env, params, app_name, follow).await;
            }
        }
        Err(err) => {
            output::config_error(err);
        }
    }
}

/// do_run_local is the entrypoint for running an app locally. It will load the Towerfile, build
/// the package, and launch the app. The relevant package is cleaned up after execution is
/// complete.
async fn do_run_local(config: Config, path: PathBuf, env: &str, mut params: HashMap<String, String>) {
    let mut spinner = output::spinner("Setting up runtime environment...");

    // Load all the secrets and catalogs from the server
    let secrets = if let Ok(secs) = get_secrets(&config, &env).await {
        secs
    } else {
        output::die("Something went wrong loading secrets into your environment");
    };

    let catalogs = if let Ok(cats) = get_catalogs(&config, &env).await {
        cats
    } else {
        output::die("Something went wrong loading catalogs into your environment");
    };

    spinner.success();

    // We prepare all the other misc environment variables that we need to inject
    let mut env_vars = HashMap::new();
    env_vars.extend(catalogs);
    env_vars.insert("TOWER_URL".to_string(), config.tower_url.to_string());

    // There should always be a session, if there isn't one then I'm not sure how we got here?
    let session = config.session.unwrap_or_else(|| {
        output::die("No session found. Please log in to Tower first.");
    });

    env_vars.insert("TOWER_JWT".to_string(), session.token.jwt.to_string());

    // Load the Towerfile
    let towerfile_path = path.join("Towerfile");
    let towerfile = load_towerfile(&towerfile_path);

    for param in &towerfile.parameters {
        if !params.contains_key(&param.name) {
            params.insert(param.name.clone(), param.default.clone());
        }
    }

    // Build the package
    let mut package = build_package(&towerfile).await;

    // Unpack the package
    if let Err(err) = package.unpack().await {
        debug!("Failed to unpack package: {}", err);
        output::package_error(err);
        std::process::exit(1);
    }

    let (sender, receiver) = unbounded_channel();

    output::success(&format!("Launching app `{}`", towerfile.app.name));
    let output_task = tokio::spawn(monitor_output(receiver));

    let mut launcher: AppLauncher<LocalApp> = AppLauncher::default();
    if let Err(err) = launcher
        .launch(Context::new(), sender, package, env.to_string(), secrets, params, env_vars)
        .await
    {
        output::runtime_error(err);
        return;
    }

    // Monitor app output and status concurrently
    let app = launcher.app.unwrap();
    let status_task = tokio::spawn(monitor_status(app));

    let (res1, res2) = tokio::join!(output_task, status_task);

    // We have to unwrap both of these as a method for propagating any panics that happened
    // internally.
    res1.unwrap();
    res2.unwrap();
}

/// do_run_remote is the entrypoint for running an app remotely. It uses the Towerfile in the
/// supplied directory (locally or remotely) to sort out what application to run exactly.
async fn do_run_remote(
    config: Config,
    path: PathBuf,
    env: &str,
    params: HashMap<String, String>,
    app_name: Option<String>,
    should_follow_run: bool,
) {
    let app_slug = app_name.unwrap_or_else(|| {
        // Load the Towerfile
        let towerfile_path = path.join("Towerfile");
        let towerfile = load_towerfile(&towerfile_path);
        towerfile.app.name
    });

    let mut spinner = output::spinner("Scheduling run...");

    match api::run_app(&config, &app_slug, env, params).await {
        Err(err) => {
            spinner.failure();
            debug!("Failed to schedule run: {}", err);
            output::tower_error(err);
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
        }
    }
}

async fn do_follow_run(
    config: Config,
    run: &Run,
) {
    let mut spinner = output::spinner("Waiting for run to start...");

    match wait_for_run_start(&config, &run).await {
        Err(err) => {
            spinner.failure();
            debug!("Failed to wait for run to start: {}", err);
            let msg = format!("An error occurred while waiting for the run to start. This shouldn't happen! You can get more details at {:?} or by contacting support.", run.dollar_link);
            output::failure(&msg);
        },
        Ok(()) => {
            spinner.success();

            // We do this here, explicitly, to not double-monitor our API via the
            // `wait_for_run_start` function above.
            let mut run_complete = monitor_run_completion(&config, run);

            // We set a Ctrl+C handler here, if invoked it will print a message that shows where
            // the user can follow the run.
            let run_copy = run.clone();

            ctrlc::set_handler(move || {
                output::newline();

                let msg = format!(
                    "Run #{} for app `{}` is still running.",
                    run_copy.number, run_copy.app_name
                );
                output::write(&msg);
                output::newline();

                let msg = format!(
                    "You can follow it at {}",
                    run_copy.dollar_link
                );
                output::write(&msg);
                output::newline();

                // According to
                // https://www.agileconnection.com/article/overview-linux-exit-codes...
                std::process::exit(130);
            }).expect("Failed to set Ctrl+C handler");

            // Now we follow the logs from the run. We can stream them from the cloud to here using
            // the stream_logs API endpoint.
            match api::stream_run_logs(&config, &run.app_name, run.number).await {
                Ok(mut output) => {
                    loop {
                        tokio::select! {
                            Some(event) = output.recv() => print_log_stream_event(event),
                            res = &mut run_complete => {
                                match res {
                                    Ok(run) => print_run_completion(&run),
                                    Err(err) => {
                                        debug!("Failed to monitor run completion: {:?}", err);
                                        let msg = format!("An error occurred while waiting for the run to complete. This shouldn't happen! You can get more details at {:?} or by contacting support.", run.dollar_link);
                                        output::failure(&msg);
                                    }
                                }

                                break;
                            },
                        };
                    }
                },
                Err(err) => {
                    debug!("Failed to stream run logs: {:?}", err);
                    let msg = format!("An error occurred while streaming logs from Tower to your console. You can get more details at {:?} or by contacting support.", run.dollar_link);
                    output::failure(&msg);
                }
            }
        }
    };
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

    match api::export_secrets(&config, env, false, public_key).await {
        Ok(res) => {
            let mut secrets = HashMap::new();

            for secret in res.secrets {
                // we will decrypt each property and inject it into the vals map.
                let decrypted_value = crypto::decrypt(private_key.clone(), secret.encrypted_value.to_string())?;
                secrets.insert(secret.name, decrypted_value);
            }

            Ok(secrets)
        },
        Err(err) => {
            output::tower_error(err);
            Err(Error::FetchingSecretsFailed)
        }
    }
}

/// get_catalogs manages the process of exporting catalogs, decrypting their properties, and
/// preparting them for injection into the environment during app execution
async fn get_catalogs(config: &Config, env: &str) -> Result<HashMap<String, String>, Error> {
    let (private_key, public_key) = crypto::generate_key_pair();

    match api::export_catalogs(&config, env, false, public_key).await {
        Ok(res) => {
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
        },
        Err(err) => {
            output::tower_error(err);
            Err(Error::FetchingCatalogsFailed)
        }
    }
}

/// load_towerfile manages the process of loading a Towerfile from a given path in an interactive
/// way. That means it will not return if the Towerfile can't be loaded and instead will publish an
/// error.
fn load_towerfile(path: &PathBuf) -> Towerfile {
    Towerfile::from_path(path.clone()).unwrap_or_else(|err| {
        debug!("Failed to load Towerfile from path `{:?}`: {}", path, err);
        output::config_error(err);
        std::process::exit(1);
    })
}

/// build_package manages the process of building a package in an interactive way for local app
/// execution. If the pacakge fails to build for wahatever reason, the app will exit.
async fn build_package(towerfile: &Towerfile) -> Package {
    let mut spinner = output::spinner("Building package...");
    let package_spec = PackageSpec::from_towerfile(towerfile);
    match Package::build(package_spec).await {
        Ok(package) => {
            spinner.success();
            package
        }
        Err(err) => {
            spinner.failure();
            debug!("Failed to build package: {}", err);
            output::package_error(err);
            std::process::exit(1);
        }
    }
}

/// monitor_output is a helper function that will monitor the output of a given output channel and
/// plops it down on stdout.
async fn monitor_output(mut output: OutputReceiver) {
    loop {
        if let Some(line) = output.recv().await {
            let ts = dates::format(line.time);
            let msg = &line.line;
            output::log_line(&ts, msg, output::LogLineType::Local);
        } else {
            break;
        }
    }
}

/// monitor_status is a helper function that will monitor the status of a given app and waits for
/// it to progress to a terminal state.
async fn monitor_status(app: LocalApp) {
    loop {
        if let Ok(status) = app.status().await {
            match status {
                tower_runtime::Status::Exited => {
                    output::success("Your app exited cleanly.");
                    break;
                }
                tower_runtime::Status::Crashed { .. } => {
                    output::failure("Your app crashed!");
                    break;
                }
                _ => continue,
            }
        }
    }
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
