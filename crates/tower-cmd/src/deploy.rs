use config::{Config, Towerfile};
use clap::{Command, ArgMatches};
use tower_api::Client;
use tower_package::{Package, PackageSpec};

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
                    
                    let res = client.upload_code(&towerfile.app.name, package).await;
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

