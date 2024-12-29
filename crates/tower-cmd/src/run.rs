use std::collections::HashMap;
use std::path::PathBuf;
use config::{Config, Towerfile};
use clap::{Arg, Command, ArgMatches};
use tower_api::Client;
use tower_package::{Package, PackageSpec};
use tower_runtime::{AppLauncher, App, OutputChannel, local::LocalApp};

use crate::output;

pub fn run_cmd() -> Command {
    Command::new("run")
        .allow_external_subcommands(true)
        .arg(
            Arg::new("dir")
                .long("dir")
                .short('d')
                .help("The directory containing the Towerfile")
                .default_value(".")
        )
        .arg(
            Arg::new("local")
                .long("local")
                .default_value("false")
                .help("Run this app locally")
                .action(clap::ArgAction::SetTrue)
        )
        .arg(
            Arg::new("environment")
                .short('e')
                .long("environment")
                .help("The environment to invoke the app in")
                .default_value("default")
        )
        .arg(
            Arg::new("parameters")
                .short('p')
                .long("parameter")
                .help("Parameters (key=value) to pass to the app")
                .action(clap::ArgAction::Append)
        )
        .about("Run your code in Tower or locally")
}

/// do_run is the primary entrypoint into running apps both locally and remotely in Tower. It will
/// use the configuration to determine the requested way of running a Tower app.
pub async fn do_run(config: Config, client: Client, args: &ArgMatches, cmd: Option<(&str, &ArgMatches)>) {
    let res = get_run_parameters(args, cmd);

    match res {
        Ok((local, path, params, app_name)) => {
            log::debug!("Running app at {}, local: {}", path.to_str().unwrap(), local);

            if local {
                // For the time being, we should report that we can't run an app by name locally.
                if app_name.is_some() {
                    output::die("Running apps by name locally is not supported yet.");
                } else {
                    do_run_local(config, client, path, params).await;
                }
            } else {
                // We always expect there to be an environmnt due to the fact that there is a
                // default value.
                let env = args.get_one::<String>("environment").unwrap();

                do_run_remote(config, client, path, env, params, app_name).await;
            }
        },
        Err(err) => {
            output::config_error(err);
        }
    }
}

/// do_run_local is the entrypoint for running an app locally. It will load the Towerfile, build
/// the package, and launch the app. The relevant package is cleaned up after execution is
/// complete.
async fn do_run_local(_config: Config, client: Client, path: PathBuf, mut params: HashMap<String, String>) {
    // There is always an implicit `local` environment when running in a local context.
    let env = "local".to_string();

    // Load all the secrets from the server
    let secrets = get_secrets(&client, &env).await;

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
        log::debug!("Failed to unpack package: {}", err);
        output::package_error(err);
        std::process::exit(1);
    }


    let mut launcher: AppLauncher<LocalApp> = AppLauncher::default();
    if let Err(err) = launcher.launch(package, env, secrets, params).await {
        output::runtime_error(err);
        return;
    }

    log::debug!("App launched successfully");
    output::success(&format!("App `{}` has been launched", towerfile.app.name));

    // Monitor app output and status concurrently
    let app = launcher.app.unwrap();
    let output = app.output().await.unwrap();

    let output_task = tokio::spawn(monitor_output(output));
    let status_task = tokio::spawn(monitor_status(app));

    log::debug!("Waiting for app tasks to complete");
    let (res1, res2) = tokio::join!(output_task, status_task);

    // We have to unwrap both of these as a method for propogating any panics htat happened
    // internally.
    res1.unwrap();
    res2.unwrap();

    log::debug!("App terminated, shutting down");
}

/// do_run_remote is the entrypoint for running an app remotely. It uses the Towerfile in the
/// supplied directory (locally or remotely) to sort out what application to run exactly.
async fn do_run_remote(_config: Config, client: Client, path: PathBuf, env: &str, params: HashMap<String, String>, app_name: Option<String>) {
    let mut spinner = output::spinner("Scheduling run...");

    let app_name = app_name.unwrap_or_else(|| {
        // Load the Towerfile
        let towerfile_path = path.join("Towerfile");
        let towerfile = load_towerfile(&towerfile_path);
        towerfile.app.name
    });

    let res = client.run_app(&app_name, env, params).await;

    match res {
        Ok(run) => {
            spinner.success();

            let line = format!("Run #{} for app `{}` has been scheduled", run.number, app_name);
            output::success(&line);
        },
        Err(err) => {
            spinner.failure();

            output::tower_error(err);
        }
    }
}

/// get_run_parameters takes care of all the hariy bits around digging about in the `clap`
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

/// Parses `--parameter` arguments into a HashMap of key-value pairs.
fn parse_parameters(args: &ArgMatches) -> HashMap<String, String> {
    let mut param_map = HashMap::new();

    if let Some(parameters) = args.get_many::<String>("parameters") {
        for param in parameters {
            if let Some((key, value)) = param.split_once('=') {
                param_map.insert(key.to_string(), value.to_string());
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
fn get_app_name(cmd: Option<(&str, &ArgMatches)>) -> Option<String>{ 
    match cmd {
        Some((name, _)) if !name.is_empty() => Some(name.to_string()),
        _ => None,
    }
}

/// get_secrets manages the process of getting secrets from the Tower server in a way that can be
/// used by the local runtime during local app execution.
async fn get_secrets(client: &Client, env: &str) -> HashMap<String, String> {
    let mut spinner = output::spinner("Getting secrets...");
    match client.export_secrets(false, Some(env.to_string())).await {
        Ok(secrets) => {
            spinner.success();
            secrets.into_iter().map(|sec| (sec.name, sec.value)).collect()
        },
        Err(err) => {
            spinner.failure();
            log::debug!("Failed to export secrets for local execution: {}", err);
            output::tower_error(err);
            std::process::exit(1);
        }
    }
}

/// load_towerfile manages the process of loading a Towerfile from a given path in an interactive
/// way. That means it will not return if the Towerfile can't be loaded and instead will publish an
/// error.
fn load_towerfile(path: &PathBuf) -> Towerfile {
    Towerfile::from_path(path.clone()).unwrap_or_else(|err| {
        log::debug!("Failed to load Towerfile from path `{:?}`: {}", path, err);
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
        },
        Err(err) => {
            spinner.failure();
            log::debug!("Failed to build package: {}", err);
            output::package_error(err);
            std::process::exit(1);
        }
    }
}

/// monitor_output is a helper function that will monitor the output of a given output channel and
/// plops it down on stdout.
async fn monitor_output(output: OutputChannel) {
    loop {
        if let Some(line) = output.lock().await.recv().await {
            let ts = &line.time;
            let msg = &line.line;
            output::log_line(ts, msg, output::LogLineType::Local);
        } else {
            break;
        }
    }
}

/// monitor_status is a helper function that will monitor the status of a given app and waits for
/// it to progress to a terminal state.
async fn monitor_status(mut app: LocalApp) {
    loop {
        if let Ok(status) = app.status().await {
            match status {
                tower_runtime::Status::Exited => {
                    output::success("Your app exited cleanly.");
                    break;
                }
                tower_runtime::Status::Crashed => {
                    output::failure("Your app crashed!");
                    break;
                }
                _ => continue,
            }
        }
    }
}
