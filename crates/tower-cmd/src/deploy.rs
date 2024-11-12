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
    // Determine the directory to build the package from
    let dir = cmd.map_or(".", |cmd| if cmd.0.is_empty() { "." } else { cmd.0 });

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
                    
                    match client.upload_code(&towerfile.app.name, package, Some(callback)).await {
                        Err(err) => {

                            let progress_bar = progress_bar.lock().unwrap(); // Lock the Mutex to get mutable access
                            progress_bar.finish();

                            output::newline();
                            output::tower_error(err);
                        }
                        Ok(code) => {
                            let progress_bar = progress_bar.lock().unwrap(); // Lock the Mutex to get mutable access
                            progress_bar.finish();

                            output::newline();

                            let line = format!("Version `{}` of your code has been deployed to Tower!", code.version);
                            output::success(&line);
                        }
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

