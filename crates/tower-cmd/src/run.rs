use std::collections::HashMap;
use std::path::PathBuf;
use config::{Config, Towerfile};
use clap::{Arg, Command, ArgMatches};
use tower_api::Client;
use tower_package::{Package, PackageSpec};
use tower_runtime::{AppLauncher, App, local::LocalApp};

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

async fn do_run_local(_config: Config, client: Client, path: PathBuf) {
    let spinner = output::spinner("Getting secrets...");

    // Export all the secrets that will be used.
    let secrets = match client.export_secrets().await{
        Ok(secrets) => {
            spinner.success();

            // turn the secrets into something that's usable by the AppLauncher implementation that
            // we have around here
            secrets.into_iter().map(|sec| {
                (sec.name, sec.value)
            }).collect::<HashMap<_, _>>()
        },
        Err(err) => {
            spinner.failure();
            log::debug!("failed to export secrest for local execution: {}", err);

            output::tower_error(err);
            std::process::exit(1);
        }
    };

    // Get the local towerfile.
    let path = path.join("Towerfile");
    let towerfile = Towerfile::from_path(path.to_path_buf()).unwrap_or_else(|err| {
        log::debug!("failed to load Towerfile from path `{:?}`: {}", path.to_path_buf(), err);

        output::config_error(err);
        std::process::exit(1);
    });

    // Build the package for execution.
    let spinner = output::spinner("Building package...");
    let package_spec = PackageSpec::from_towerfile(&towerfile);
    let mut package = match Package::build(package_spec).await {
        Ok(package) => {
            spinner.success();
            package
        },
        Err(err) => {
            spinner.failure();
            log::debug!("failed to build package from path `{:?}`: {}", path.to_path_buf(), err);

            output::package_error(err);
            std::process::exit(1);
        }
    };

    // Now we should unpack the package.
    if let Err(err) = package.unpack().await {
        log::debug!("failed to unpack package: {}", err);

        output::package_error(err);
        std::process::exit(1);
    }

    let mut launcher: AppLauncher<LocalApp> = AppLauncher::default();
    match launcher.launch(package, secrets).await {
        Ok(_) => {
            let mut app = launcher.app.unwrap();
            log::debug!("app launched successfully");

            let line = format!("App `{}` has been launched", towerfile.app.name);
            output::success(&line);

            let output = app.output().await.unwrap();

            let p1 = tokio::spawn(async move {
                loop {
                    let res = output.lock().await.recv().await;

                    match res {
                        None => break,
                        Some(line) => {
                            // TODO: Theoretically, these lines could arrive out of order. We
                            // probably want to sequence them somehow?
                            output::log_line(&line);
                        },
                    }
                }
            });

            let p2 = tokio::spawn(async move {
                loop{
                    let res= app.status().await;

                    if let Ok(status) = res {
                        match status {
                            tower_runtime::Status::Exited => {
                                output::success("Your app exited cleanly.");
                                break;
                            },
                            tower_runtime::Status::Crashed => {
                                output::failure("Your app crashed!");
                                break;
                            },
                            _ => {
                                // continue
                            }
                        }
                    } else {
                        // continue
                    }
                }
            });

            log::debug!("launched apps, waiting for them to complete");

            // NOTE: We keep the result here and unwrap them to propgate any panics in the spawned
            // threads.
            let res = tokio::join!(p1, p2);
            res.0.unwrap();
            res.1.unwrap();

            // aaaand we're done.
            log::debug!("app terminated, shutting down");
        },
        Err(err) => {
            output::runtime_error(err);
        }
    }
}

async fn do_run_remote(_config: Config, client: Client, path: PathBuf) {
    let spinner = output::spinner("Scheduling run...");

    let path = path.join("Towerfile");
    let towerfile = Towerfile::from_path(path).unwrap_or_else(|err| {
        output::config_error(err);
        std::process::exit(1);
    });

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
