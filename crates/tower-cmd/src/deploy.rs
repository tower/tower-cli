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
        .arg(
            Arg::new("environment")
                .long("environment")
                .short('e')
                .help("The environment to deploy to")
                .conflicts_with("all"),
        )
        .arg(
            Arg::new("all")
                .long("all")
                .help("Deploy to all environments")
                .action(clap::ArgAction::SetTrue)
                .conflicts_with("environment"),
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

/// Resolves the target environment from CLI args.
///
/// - `--all` → `DeployTarget::All`
/// - `--environment <name>` → `DeployTarget::Environment(name)`
/// - neither → `DeployTarget::Default`
#[derive(Debug, Clone)]
pub enum DeployTarget {
    Environment(String),
    All,
}

pub async fn do_deploy(config: Config, args: &ArgMatches) {
    let dir = resolve_path(args);
    let create_app = args.get_flag("create");

    let target = if args.get_flag("all") {
        DeployTarget::All
    } else if let Some(env) = args.get_one::<String>("environment") {
        DeployTarget::Environment(env.clone())
    } else {
        DeployTarget::Environment("default".to_string())
    };

    if let Err(err) = deploy_from_dir(config, dir, create_app, target).await {
        match err {
            crate::Error::ApiDeployError { source } => {
                output::tower_error_and_die(source, "Deploying app failed")
            }
            crate::Error::ApiCreateAppError { source } => {
                output::tower_error_and_die(source, "Creating app failed")
            }
            crate::Error::ApiDescribeAppError { source } => {
                output::tower_error_and_die(source, "Fetching app details failed")
            }
            crate::Error::PackageError { source } => {
                output::package_error(source);
                std::process::exit(1);
            }
            crate::Error::TowerfileLoadFailed { source, .. } => {
                output::config_error(source);
                std::process::exit(1);
            }
            _ => output::die(&err.to_string()),
        }
    }
}

pub async fn deploy_from_dir(
    config: Config,
    dir: PathBuf,
    create_app: bool,
    target: DeployTarget,
) -> Result<(), crate::Error> {
    debug!("Building package from directory: {:?}", dir);

    let path = dir.join("Towerfile");

    let towerfile = Towerfile::from_path(path)?;
    let api_config = config.into();

    // Add app existence check before proceeding
    util::apps::ensure_app_exists(
        &api_config,
        &towerfile.app.name,
        towerfile.app.description.as_deref(),
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
    do_deploy_package(api_config, package, &towerfile, target).await
}

async fn do_deploy_package(
    api_config: Configuration,
    package: Package,
    towerfile: &Towerfile,
    target: DeployTarget,
) -> Result<(), crate::Error> {
    let (environment, all_environments) = match &target {
        DeployTarget::All => (None, true),
        DeployTarget::Environment(env) => (Some(env.as_str()), false),
    };

    let res = util::deploy::deploy_app_package(
        &api_config,
        &towerfile.app.name,
        package,
        environment,
        all_environments,
    )
    .await;

    match res {
        Ok(resp) => {
            let version = resp.version;
            let line = match &target {
                DeployTarget::All => format!(
                    "Version `{}` has been deployed to all environments!",
                    version.version
                ),
                DeployTarget::Environment(env) => format!(
                    "Version `{}` has been deployed to environment '{}'!",
                    version.version, env
                ),
            };
            output::success(&line);
            Ok(())
        }
        Err(err) => Err(crate::Error::ApiDeployError { source: err }),
    }
}

#[cfg(test)]
mod tests {
    use super::deploy_cmd;

    fn parse(args: &[&str]) -> Result<clap::ArgMatches, clap::Error> {
        let mut full = vec!["deploy"];
        full.extend_from_slice(args);
        deploy_cmd().try_get_matches_from(full)
    }

    #[test]
    fn no_args_uses_defaults() {
        let m = parse(&[]).unwrap();
        assert_eq!(m.get_one::<String>("environment"), None);
        assert!(!m.get_flag("all"));
    }

    #[test]
    fn environment_flag_long() {
        let m = parse(&["--environment", "production"]).unwrap();
        assert_eq!(
            m.get_one::<String>("environment").map(|s| s.as_str()),
            Some("production")
        );
    }

    #[test]
    fn environment_flag_short() {
        let m = parse(&["-e", "staging"]).unwrap();
        assert_eq!(
            m.get_one::<String>("environment").map(|s| s.as_str()),
            Some("staging")
        );
    }

    #[test]
    fn environment_flag_equals_syntax() {
        let m = parse(&["--environment=production"]).unwrap();
        assert_eq!(
            m.get_one::<String>("environment").map(|s| s.as_str()),
            Some("production")
        );
    }

    #[test]
    fn all_flag() {
        let m = parse(&["--all"]).unwrap();
        assert!(m.get_flag("all"));
        assert_eq!(m.get_one::<String>("environment"), None);
    }

    #[test]
    fn environment_and_all_conflict() {
        let err = parse(&["--environment", "production", "--all"]).unwrap_err();
        assert_eq!(err.kind(), clap::error::ErrorKind::ArgumentConflict);
    }

    #[test]
    fn all_and_environment_conflict() {
        let err = parse(&["--all", "--environment", "staging"]).unwrap_err();
        assert_eq!(err.kind(), clap::error::ErrorKind::ArgumentConflict);
    }

    #[test]
    fn create_flag_with_environment() {
        let m = parse(&["--create", "--environment", "production"]).unwrap();
        assert!(m.get_flag("create"));
        assert_eq!(
            m.get_one::<String>("environment").map(|s| s.as_str()),
            Some("production")
        );
    }

    #[test]
    fn create_flag_with_all() {
        let m = parse(&["--create", "--all"]).unwrap();
        assert!(m.get_flag("create"));
        assert!(m.get_flag("all"));
    }

    #[test]
    fn dir_with_environment() {
        let m = parse(&["-d", "/tmp/myapp", "-e", "production"]).unwrap();
        assert_eq!(
            m.get_one::<String>("dir").map(|s| s.as_str()),
            Some("/tmp/myapp")
        );
        assert_eq!(
            m.get_one::<String>("environment").map(|s| s.as_str()),
            Some("production")
        );
    }

    #[test]
    fn help_flag_shows_help() {
        let err = parse(&["--help"]).unwrap_err();
        assert_eq!(err.kind(), clap::error::ErrorKind::DisplayHelp);
    }
}
