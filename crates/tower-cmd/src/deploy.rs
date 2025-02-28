use clap::{Arg, ArgMatches, Command};
use config::{Config, Towerfile};
use std::convert::From;
use std::path::PathBuf;

use crate::{output, util};
use tower_package::{Package, PackageSpec};

pub fn deploy_cmd() -> Command {
    Command::new("deploy")
        .arg(
            Arg::new("dir")
                .long("dir")
                .short('d')
                .help("The directory containing the app to deploy")
                .default_value("."),
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

pub async fn do_deploy(config: Config, args: &ArgMatches) {
    // Determine the directory to build the package from
    let dir = resolve_path(args);
    log::debug!("Building package from directory: {:?}", dir);

    let path = dir.join("Towerfile");

    match Towerfile::from_path(path) {
        Ok(towerfile) => {
            let api_config = &config.into();

            // Add app existence check before proceeding
            if let Err(err) = util::apps::ensure_app_exists(
                &api_config,
                &towerfile.app.name,
                &towerfile.app.description,
            )
            .await
            {
                output::tower_error(err);
                return;
            }

            let spec = PackageSpec::from_towerfile(&towerfile);
            let mut spinner = output::spinner("Building package...");

            match Package::build(spec).await {
                Ok(package) => {
                    spinner.success();

                    match util::deploy::deploy_app_package(
                        &api_config,
                        &towerfile.app.name,
                        package,
                    )
                    .await
                    {
                        Ok(version) => {
                            let line = format!(
                                "Version `{}` of your code has been deployed to Tower!",
                                version
                            );
                            output::success(&line);
                        }
                        Err(err) => {
                            output::failure(&format!("Failed to deploy: {}", err));
                        }
                    }
                }
                Err(err) => {
                    spinner.failure();
                    output::package_error(err);
                }
            }
        }
        Err(err) => {
            output::config_error(err);
        }
    }
}
