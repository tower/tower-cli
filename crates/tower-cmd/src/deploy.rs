use clap::{Arg, ArgMatches, Command};
use config::{Config, Towerfile};
use std::convert::From;
use std::path::PathBuf;

use crate::{output, util};
use tower_api::apis::configuration::Configuration;
use tower_package::{Package, PackageSpec};
use tower_telemetry::debug;

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
            Arg::new("create")
                .long("create")
                .short('f')
                .help("Automatically force creation of the app if it doesn't already exist")
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
    let create_app = args.get_flag("create");
    if let Err(err) = deploy_from_dir(config, dir, create_app).await {
        match err {
            crate::Error::ApiDeployError { source } => output::tower_error(source),
            crate::Error::ApiDescribeAppError { source } => output::tower_error(source),
            crate::Error::PackageError { source } => output::package_error(source),
            crate::Error::TowerfileLoadFailed { source, .. } => output::config_error(source),
            _ => output::error(&err.to_string()),
        }
    }
}

pub async fn deploy_from_dir(
    config: Config,
    dir: PathBuf,
    create_app: bool,
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
        create_app,
    )
    .await?;

    let spec = PackageSpec::from_towerfile(&towerfile);
    let mut spinner = output::spinner("Building package...");

    let package = match Package::build(spec).await {
        Ok(package) => package,
        Err(err) => {
            spinner.failure();
            let error = crate::Error::PackageError { source: err };
            return Err(error);
        }
    };

    spinner.success();
    do_deploy_package(api_config, package, &towerfile).await
}

async fn do_deploy_package(
    api_config: Configuration,
    package: Package,
    towerfile: &Towerfile,
) -> Result<(), crate::Error> {
    let res = util::deploy::deploy_app_package(&api_config, &towerfile.app.name, package).await;

    match res {
        Ok(resp) => {
            let version = resp.version;
            let line = format!("Version `{}` has been deployed to Tower!", version.version);
            output::success(&line);
            Ok(())
        }
        Err(err) => Err(crate::Error::ApiDeployError { source: err }),
    }
}
