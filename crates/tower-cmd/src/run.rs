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
            Arg::new("local")
                .long("local")
                .default_value("false")
                .action(clap::ArgAction::SetTrue)
        )
        .about("Run your code in Tower or locally")
}

/// do_run is the primary entrypoint into running apps both locally and remotely in Tower. It will
/// use the configuration to determine the requested way of running a Tower app.
pub async fn do_run(config: Config, client: Client, args: &ArgMatches, cmd: Option<(&str, &ArgMatches)>) {
    let res = get_run_parameters(args, cmd);

    match res {
        Ok((local, path)) => {
            log::debug!("Running app at {}, local: {}", path.to_str().unwrap(), local);

            if local {
                do_run_local(config, client, path).await;
            } else {
                do_run_remote(config, client, path).await;
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
async fn do_run_local(_config: Config, client: Client, path: PathBuf) {
    // Load all the secrets from the server
    let secrets = get_secrets(&client).await;

    // Load the Towerfile
    let towerfile_path = path.join("Towerfile");
    let towerfile = load_towerfile(&towerfile_path);

    // Build the package
    let mut package = build_package(&towerfile).await;

    // Unpack the package
    if let Err(err) = package.unpack().await {
        log::debug!("Failed to unpack package: {}", err);
        output::package_error(err);
        std::process::exit(1);
    }

    let mut launcher: AppLauncher<LocalApp> = AppLauncher::default();
    if let Err(err) = launcher.launch(package, secrets).await {
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
async fn do_run_remote(_config: Config, client: Client, path: PathBuf) {
    let spinner = output::spinner("Scheduling run...");

    // Load the Towerfile
    let towerfile_path = path.join("Towerfile");
    let towerfile = load_towerfile(&towerfile_path);

    let res = client.run_app(&towerfile.app.name).await;

    match res {
        Ok(run) => {
            spinner.success();

            let line = format!("Run #{} for app `{}` has been scheduled", run.number, towerfile.app.name);
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
fn get_run_parameters(args: &ArgMatches, cmd: Option<(&str, &ArgMatches)>) -> Result<(bool, PathBuf), config::Error> {
    let local = args.get_one::<bool>("local").unwrap();

    if let Some(cmd) = cmd {
        let path = cmd.0.to_string();

        if path.is_empty() {
            Ok((*local, PathBuf::from(".")))
        } else {
            Ok((*local, PathBuf::from(path)))
        }
    } else {
        Ok((*local, PathBuf::from(".")))
    }
}

/// get_secrets manages the process of getting secrets from the Tower server in a way that can be
/// used by the local runtime during local app execution.
async fn get_secrets(client: &Client) -> HashMap<String, String> {
    let spinner = output::spinner("Getting secrets...");
    match client.export_secrets().await {
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
    let spinner = output::spinner("Building package...");
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
            output::log_line(&line);
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