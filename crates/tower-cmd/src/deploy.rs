use std::{convert::From, path::PathBuf};

use clap::{Arg, ArgMatches, Command};
use config::{Config, Towerfile};
use tower_api::apis::configuration::Configuration;
use tower_package::{Package, PackageSpec};
use tower_telemetry::debug;

use crate::{output, util};

pub fn deploy_cmd() -> Command {
    Command::new("deploy")
        .arg(
            Arg::new("dir")
                .long("dir")
                .short('d')
                .help("The directory containing the app to deploy")
                .default_value("."),
        )
        .arg(
            Arg::new("auto-create")
                .long("auto-create")
                .help("Automatically create app if it doesn't exist")
                .action(clap::ArgAction::SetTrue),
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
    let dir = resolve_path(args);
    let auto_create = args.get_flag("auto-create");
    if let Err(err) = deploy_from_dir(config, dir, auto_create).await {
        match err {
            crate::Error::ApiDeployError { source } => output::tower_error(source),
            crate::Error::ApiDescribeAppError { source } => output::tower_error(source),
            _ => eprintln!("Deploy error: {}", err),
        }
    }
}

pub async fn deploy_from_dir(
    config: Config,
    dir: PathBuf,
    auto_create: bool,
) -> Result<(), crate::Error> {
    debug!("Building package from directory: {:?}", dir);

    let path = dir.join("Towerfile");

    let towerfile = Towerfile::from_path(path)?;
    let api_config = config.into();

    // Add app existence check before proceeding
    util::apps::ensure_app_exists(
        &api_config,
        &towerfile.app.name,
        &towerfile.app.description,
        auto_create,
    )
    .await?;

    let spec = PackageSpec::from_towerfile(&towerfile);
    let mut spinner = output::spinner("Building package...");

    let package = match Package::build(spec).await {
        Ok(package) => package,
        Err(err) => {
            spinner.failure();
            let error = crate::Error::PackageError { source: err };
            eprintln!("Package build failed: {}", error);
            return Err(error);
        }
    };

    spinner.success();
    do_deploy_package(api_config, package, &towerfile).await?;
    Ok(())
}

async fn do_deploy_package(
    api_config: Configuration,
    package: Package,
    towerfile: &Towerfile,
) -> Result<tower_api::models::DeployAppResponse, crate::Error> {
    let res = util::deploy::deploy_app_package(&api_config, &towerfile.app.name, package).await;

    match res {
        Ok(resp) => {
            let version = &resp.version;

            let line = format!("Version `{}` has been deployed to Tower!", version.version);

            output::success(&line);
            Ok(resp)
        }
        Err(err) => {
            let error = crate::Error::from(err);
            eprintln!("Deploy failed: {}", error);
            Err(error)
        }
    }
}
