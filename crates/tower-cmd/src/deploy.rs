use config::{Config, Towerfile};
use clap::{Command, ArgMatches};
use tower_api::Client;
use tower_package::{Package, PackageSpec};
use std::sync::{Arc, Mutex};

use crate::output;

pub fn deploy_cmd() -> Command {
    Command::new("deploy")
        .allow_external_subcommands(true)
        .about("Deploy your latest code to Tower")
}

pub async fn do_deploy(_config: Config, client: Client, cmd: Option<(&str, &ArgMatches)>) {
    // dir is the directory that we'll build this package from.
    let dir = if let Some(cmd) = cmd {
        if cmd.0.is_empty() {
            "."
        } else {
            cmd.0
        }
    } else {
        "."
    }; 

    match Towerfile::from_dir_str(dir) {
        Ok(towerfile) => {
            let spec = PackageSpec::from_towerfile(&towerfile);
            let spinner = output::spinner("Building package...");

            match Package::build(spec).await {
                Ok(package) => {
                    spinner.success();

                    let progress_bar = Arc::new(Mutex::new(output::progress_bar("Deploying to Tower...")));

                    let callback = Box::new({
                        let progress_bar = Arc::clone(&progress_bar);
                        move |progress, total| {
                            let progress_bar = progress_bar.lock().unwrap(); // Lock the Mutex to get mutable access
                            progress_bar.set_length(total);
                            progress_bar.set_position(progress);
                        }
                    });
                    
                    if let Err(err) = client.upload_code(&towerfile.app.name, package, Some(callback)).await {
                        let progress_bar = progress_bar.lock().unwrap(); // Lock the Mutex to get mutable access
                        progress_bar.finish();

                        output::newline();
                        output::tower_error(err);
                    } else {
                        let progress_bar = progress_bar.lock().unwrap(); // Lock the Mutex to get mutable access
                        progress_bar.finish();

                        output::newline();
                        output::success("Successfully deployed your code to Tower!");
                    }
                },
                Err(err) => {
                    spinner.failure();
                    output::package_error(err);
                }
            }
        },
        Err(err) => {
            output::config_error(err);
        }
    }
}

