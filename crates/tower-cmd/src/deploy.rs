use chrono::{DateTime, Duration, Utc};
use clap::{Arg, ArgMatches, Command};
use config::{Config, Towerfile};
use std::convert::From;
use std::path::{Path, PathBuf};

use crate::{output, util};
use tower_api::apis::configuration::Configuration;
use tower_package::{Package, PackageSpec};
use tower_telemetry::debug;

/// How far in the past a returned version's `created_at` must be before we treat
/// it as a reuse (rather than a fresh insert) for the stdout hint. A fresh
/// deploy stamps `created_at` at request time, so anything older than this was
/// created by an earlier deploy that shared the same idempotency key.
const REUSE_AGE_THRESHOLD: Duration = Duration::seconds(60);

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
        .arg(
            Arg::new("idempotency-key")
                .long("idempotency-key")
                .help(
                    "Reuse the existing version deployed with this key instead of creating a new one. \
                     Defaults to the current git commit SHA when the working tree is clean.",
                )
                .conflicts_with("no-idempotency-key"),
        )
        .arg(
            Arg::new("no-idempotency-key")
                .long("no-idempotency-key")
                .help("Never send an idempotency key, even on a clean git tree")
                .action(clap::ArgAction::SetTrue)
                .conflicts_with("idempotency-key"),
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
#[derive(Debug, Clone)]
pub enum DeployTarget {
    Environment(String),
    All,
}

/// Resolves the idempotency key to send with the deploy, in precedence order:
///
/// 1. `--no-idempotency-key` → never send a key.
/// 2. `--idempotency-key <value>` → send that exact value.
/// 3. Otherwise auto-detect the git `HEAD` SHA, but only when the working tree
///    is clean (a dirty tree gets no key, so every deploy creates a new version).
fn resolve_idempotency_key(args: &ArgMatches, dir: &Path) -> Option<String> {
    if args.get_flag("no-idempotency-key") {
        debug!("--no-idempotency-key set; suppressing idempotency key");
        return None;
    }

    if let Some(key) = args.get_one::<String>("idempotency-key") {
        return Some(key.clone());
    }

    util::git::clean_head_sha(dir)
}

pub async fn do_deploy(config: Config, args: &ArgMatches) {
    let dir = resolve_path(args);
    let create_app = args.get_flag("create");
    let idempotency_key = resolve_idempotency_key(args, &dir);

    let target = if args.get_flag("all") {
        DeployTarget::All
    } else if let Some(env) = args.get_one::<String>("environment") {
        DeployTarget::Environment(env.clone())
    } else {
        DeployTarget::Environment("default".to_string())
    };

    if let Err(err) = deploy_from_dir(config, dir, create_app, target, idempotency_key).await {
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
                output::package_error(source);
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
    idempotency_key: Option<String>,
) -> Result<(), crate::Error> {
    debug!("Building package from directory: {:?}", dir);

    let path = dir.join("Towerfile");

    let path_display = path.display().to_string();
    let towerfile =
        Towerfile::from_path(path).map_err(|source| crate::Error::TowerfileLoadFailed {
            path: path_display,
            source,
        })?;
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
    do_deploy_package(api_config, package, &towerfile, target, idempotency_key).await
}

async fn do_deploy_package(
    api_config: Configuration,
    package: Package,
    towerfile: &Towerfile,
    target: DeployTarget,
    idempotency_key: Option<String>,
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
        idempotency_key.as_deref(),
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

            // Only emit the informational hint in normal mode; in JSON mode a
            // bare line would corrupt the structured output.
            if output::get_output_mode().is_normal() {
                if let Some(hint) = reuse_hint(&version, idempotency_key.as_deref()) {
                    output::write(&hint);
                }
            }

            Ok(())
        }
        Err(err) => Err(crate::Error::ApiDeployError { source: err }),
    }
}

/// Builds the "reused an existing version" hint, or `None` when the deploy
/// created a fresh version.
///
/// We treat the returned version as a reuse when (a) we sent an idempotency key,
/// (b) the server echoed it back on the version, and (c) the version's
/// `created_at` is meaningfully older than now — i.e. it predates this deploy.
fn reuse_hint(version: &tower_api::models::AppVersion, sent_key: Option<&str>) -> Option<String> {
    let sent_key = sent_key?;

    if version.idempotency_key.as_deref() != Some(sent_key) {
        return None;
    }

    let created_at = DateTime::parse_from_rfc3339(&version.created_at)
        .ok()?
        .with_timezone(&Utc);

    if Utc::now().signed_duration_since(created_at) < REUSE_AGE_THRESHOLD {
        return None;
    }

    Some(format!(
        "Reusing version `{}` (deployed {}) — no source changes since key {}.",
        version.version,
        util::dates::format(created_at),
        sent_key
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use tower_api::models::AppVersion;

    fn parse(args: &[&str]) -> Result<clap::ArgMatches, clap::Error> {
        let mut full = vec!["deploy"];
        full.extend_from_slice(args);
        deploy_cmd().try_get_matches_from(full)
    }

    fn version_with(idempotency_key: Option<&str>, created_at: &str) -> AppVersion {
        AppVersion {
            created_at: created_at.to_string(),
            parameters: vec![],
            towerfile: String::new(),
            version: "v3".to_string(),
            idempotency_key: idempotency_key.map(|s| s.to_string()),
            content_checksum: None,
        }
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

    #[test]
    fn idempotency_key_flag() {
        let m = parse(&["--idempotency-key", "abc123"]).unwrap();
        assert_eq!(
            m.get_one::<String>("idempotency-key").map(|s| s.as_str()),
            Some("abc123")
        );
    }

    #[test]
    fn no_idempotency_key_flag() {
        let m = parse(&["--no-idempotency-key"]).unwrap();
        assert!(m.get_flag("no-idempotency-key"));
    }

    #[test]
    fn idempotency_key_and_no_idempotency_key_conflict() {
        let err = parse(&["--idempotency-key", "abc", "--no-idempotency-key"]).unwrap_err();
        assert_eq!(err.kind(), clap::error::ErrorKind::ArgumentConflict);
    }

    #[test]
    fn resolve_key_prefers_explicit_flag() {
        let m = parse(&["--idempotency-key", "explicit"]).unwrap();
        // A non-existent path guarantees git auto-detection can't interfere.
        let key = resolve_idempotency_key(&m, Path::new("/nonexistent/path"));
        assert_eq!(key.as_deref(), Some("explicit"));
    }

    #[test]
    fn resolve_key_opt_out_wins_over_git() {
        let m = parse(&["--no-idempotency-key"]).unwrap();
        // Even pointed at the (clean-or-dirty) repo we're in, opt-out yields None.
        let key = resolve_idempotency_key(&m, Path::new("."));
        assert_eq!(key, None);
    }

    #[test]
    fn resolve_key_none_outside_git() {
        let m = parse(&[]).unwrap();
        let key = resolve_idempotency_key(&m, Path::new("/nonexistent/path"));
        assert_eq!(key, None);
    }

    #[test]
    fn reuse_hint_none_without_sent_key() {
        let version = version_with(Some("abc"), "2020-01-01T00:00:00Z");
        assert_eq!(reuse_hint(&version, None), None);
    }

    #[test]
    fn reuse_hint_none_when_key_mismatch() {
        let version = version_with(Some("other"), "2020-01-01T00:00:00Z");
        assert_eq!(reuse_hint(&version, Some("abc")), None);
    }

    #[test]
    fn reuse_hint_none_for_freshly_created_version() {
        // created_at "now" → not a reuse, no hint.
        let now = Utc::now().to_rfc3339();
        let version = version_with(Some("abc"), &now);
        assert_eq!(reuse_hint(&version, Some("abc")), None);
    }

    #[test]
    fn reuse_hint_present_for_old_matching_version() {
        let version = version_with(Some("abc123"), "2020-01-01T00:00:00Z");
        let hint = reuse_hint(&version, Some("abc123")).expect("expected a reuse hint");
        assert!(hint.contains("Reusing version `v3`"));
        assert!(hint.contains("abc123"));
    }
}
