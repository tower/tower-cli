use clap::{Command, ArgMatches, Arg};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use config::{Config, Towerfile};
use tower_api::apis::{
    configuration::Configuration,
    default_api::{self, DeployAppParams},
};
use tower_package::{Package, PackageSpec};

use crate::{output, util};

pub fn deploy_cmd() -> Command {
    Command::new("deploy")
        .arg(
            Arg::new("dir")
                .long("dir")
                .short('d')
                .help("The directory containing the app to deploy")
                .default_value(".")
        )
        .about("Deploy your latest code to Tower")
}

fn resolve_path(args: &ArgMatches) -> PathBuf {
    if let Some(dir) = args.get_one::<String>("dir") {
        PathBuf::from(dir)
    } else {
        PathBuf::from(".")
    }
}

pub async fn do_deploy(_config: Config, configuration: Configuration, args: &ArgMatches) {
    // Determine the directory to build the package from
    let dir = resolve_path(args);
    log::debug!("Building package from directory: {:?}", dir);

    let path = dir.join("Towerfile");

    match Towerfile::from_path(path) {
        Ok(towerfile) => {
            // Add app existence check before proceeding
            if let Err(err) = util::ensure_app_exists(&configuration, &towerfile.app.name, &towerfile.app.description, &towerfile.app.schedule).await {
                output::tower_error(err);
                return;
            }

            let spec = PackageSpec::from_towerfile(&towerfile);
            let mut spinner = output::spinner("Building package...");

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
                    
                    match default_api::deploy_app(&configuration, DeployAppParams {
                        name: towerfile.app.name.clone(),
                        content_encoding: Some("gzip".to_string()),
                    }).await {
                        Ok(response) => {
                            let progress_bar = progress_bar.lock().unwrap();
                            progress_bar.finish();
                            output::newline();

                            if let tower_api::apis::default_api::DeployAppSuccess::Status200(deploy) = response.entity.unwrap() {
                                let line = format!("Version `{}` of your code has been deployed to Tower!", deploy.version.version);
                                output::success(&line);
                            }
                        },
                        Err(err) => {
                            let progress_bar = progress_bar.lock().unwrap();
                            progress_bar.finish();
                            output::newline();

                            if let tower_api::apis::Error::ResponseError(err) = err {
                                output::failure(&format!("{}: {}", err.status, err.content));
                            } else {
                                output::failure(&format!("Unexpected error: {}", err));
                            }
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

