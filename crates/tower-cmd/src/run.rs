use clap::{Arg, ArgMatches, Command};
use config::{Config, Towerfile};
use std::collections::HashMap;
use std::path::PathBuf;
use tower_package::{Package, PackageSpec};
use tower_runtime::{local::LocalApp, App, AppLauncher, OutputReceiver};
use tower_telemetry::{Context, debug};

use crate::{
    output,
    api,
    Error,
};

pub fn run_cmd() -> Command {
    Command::new("run")
        .allow_external_subcommands(true)
        .arg(
            Arg::new("dir")
                .long("dir")
                .short('d')
                .help("The directory containing the Towerfile")
                .default_value("."),
        )
        .arg(
            Arg::new("local")
                .long("local")
                .default_value("false")
                .help("Run this app locally")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("environment")
                .short('e')
                .long("environment")
                .help("The environment to invoke the app in")
                .default_value("default"),
        )
        .arg(
            Arg::new("parameters")
                .short('p')
                .long("parameter")
                .help("Parameters (key=value) to pass to the app")
                .action(clap::ArgAction::Append),
        )
        .about("Run your code in Tower or locally")
}

/// do_run is the primary entrypoint into running apps both locally and remotely in Tower. It will
/// use the configuration to determine the requested way of running a Tower app.
pub async fn do_run(config: Config, args: &ArgMatches, cmd: Option<(&str, &ArgMatches)>) {
    let res = get_run_parameters(args, cmd);

    // We always expect there to be an environment due to the fact that there is a
    // default value.
    let env = args.get_one::<String>("environment").unwrap();

    match res {
        Ok((local, path, params, app_name)) => {
            debug!(
                "Running app at {}, local: {}",
                path.to_str().unwrap(),
                local
            );

            if local {
                // For the time being, we should report that we can't run an app by name locally.
                if app_name.is_some() {
                    output::die("Running apps by name locally is not supported yet.");
                } else {
                    do_run_local(config, path, env, params).await;
                }
            } else {
                do_run_remote(config, path, env, params, app_name).await;
            }
        }
        Err(err) => {
            output::config_error(err);
        }
    }
}

/// do_run_local is the entrypoint for running an app locally. It will load the Towerfile, build
/// the package, and launch the app. The relevant package is cleaned up after execution is
/// complete.
async fn do_run_local(config: Config, path: PathBuf, env: &str, mut params: HashMap<String, String>) {
    let mut spinner = output::spinner("Setting up runtime environment...");

    // Load all the secrets and catalogs from the server
    let secrets = if let Ok(secs) = get_secrets(&config, &env).await {
        secs
    } else {
        output::die("Something went wrong loading secrets into your environment");
    };

    let catalogs = if let Ok(cats) = get_catalogs(&config, &env).await {
        cats
    } else {
        output::die("Something went wrong loading catalogs into your environment");
    };

    spinner.success();

    // We prepare all the other misc environment variables that we need to inject
    let mut env_vars = HashMap::new();
    env_vars.extend(catalogs);
    env_vars.insert("TOWER_URL".to_string(), config.tower_url.to_string());

    // There should always be a session, if there isn't one then I'm not sure how we got here?
    let session = config.session.unwrap_or_else(|| {
        output::die("No session found. Please log in to Tower first.");
    });

    env_vars.insert("TOWER_JWT".to_string(), session.token.jwt.to_string());

    // Load the Towerfile
    let towerfile_path = path.join("Towerfile");
    let towerfile = load_towerfile(&towerfile_path);

    for param in &towerfile.parameters {
        if !params.contains_key(&param.name) {
            params.insert(param.name.clone(), param.default.clone());
        }
    }

    // Build the package
    let mut package = build_package(&towerfile).await;

    // Unpack the package
    if let Err(err) = package.unpack().await {
        debug!("Failed to unpack package: {}", err);
        output::package_error(err);
        std::process::exit(1);
    }

    let (sender, receiver) = tower_runtime::create_output_stream();

    output::success(&format!("Launching app `{}`", towerfile.app.name));
    let output_task = tokio::spawn(monitor_output(receiver));

    let mut launcher: AppLauncher<LocalApp> = AppLauncher::default();
    if let Err(err) = launcher
        .launch(Context::new(), sender, package, env.to_string(), secrets, params, env_vars)
        .await
    {
        output::runtime_error(err);
        return;
    }

    // Monitor app output and status concurrently
    let app = launcher.app.unwrap();
    let status_task = tokio::spawn(monitor_status(app));

    let (res1, res2) = tokio::join!(output_task, status_task);

    // We have to unwrap both of these as a method for propagating any panics that happened
    // internally.
    res1.unwrap();
    res2.unwrap();
}

/// do_run_remote is the entrypoint for running an app remotely. It uses the Towerfile in the
/// supplied directory (locally or remotely) to sort out what application to run exactly.
async fn do_run_remote(
    config: Config,
    path: PathBuf,
    env: &str,
    params: HashMap<String, String>,
    app_name: Option<String>,
) {
    let app_slug = app_name.unwrap_or_else(|| {
        // Load the Towerfile
        let towerfile_path = path.join("Towerfile");
        let towerfile = load_towerfile(&towerfile_path);
        towerfile.app.name
    });

    let mut spinner = output::spinner("Scheduling run...");

    match api::run_app(&config, &app_slug, env, params).await {
        Err(err) => {
            spinner.failure();
            debug!("Failed to schedule run: {}", err);
            output::tower_error(err);
        }, 
        Ok(res) => {
            spinner.success();

            let line = format!(
                "Run #{} for app `{}` has been scheduled",
                res.run.number, app_slug
            );
            output::success(&line);
        }
    }
}

/// get_run_parameters takes care of all the hairy bits around digging about in the `clap`
/// internals to figure out what the user is requesting. In the end, it determines if we are meant
/// to do a local run or a remote run, and it determines the path to the relevant Towerfile that
/// should be loaded.
fn get_run_parameters(
    args: &ArgMatches,
    cmd: Option<(&str, &ArgMatches)>,
) -> Result<(bool, PathBuf, HashMap<String, String>, Option<String>), config::Error> {
    let local = *args.get_one::<bool>("local").unwrap();
    let path = resolve_path(args);
    let params = parse_parameters(args);
    let app_name = get_app_name(cmd);

    Ok((local, path, params, app_name))
}

/// Parses `--parameter` arguments into a HashMap of key-value pairs.
/// Handles format like "--parameter key=value"
fn parse_parameters(args: &ArgMatches) -> HashMap<String, String> {
    let mut param_map = HashMap::new();

    if let Some(parameters) = args.get_many::<String>("parameters") {
        for param in parameters {
            match param.split_once('=') {
                Some((key, value)) => {
                    if key.is_empty() {
                        output::failure(&format!(
                            "Invalid parameter format: '{}'. Key cannot be empty.",
                            param
                        ));
                        continue;
                    }
                    param_map.insert(key.to_string(), value.to_string());
                }
                None => {
                    output::failure(&format!(
                        "Invalid parameter format: '{}'. Expected 'key=value'.",
                        param
                    ));
                }
            }
        }
    }

    param_map
}

/// Resolves the path based on the `cmd` option.
fn resolve_path(args: &ArgMatches) -> PathBuf {
    if let Some(dir) = args.get_one::<String>("dir") {
        PathBuf::from(dir)
    } else {
        PathBuf::from(".")
    }
}

/// get_app_name is a helper function that will extract the app name from the `clap` arguments if
fn get_app_name(cmd: Option<(&str, &ArgMatches)>) -> Option<String> {
    match cmd {
        Some((name, _)) if !name.is_empty() => Some(name.to_string()),
        _ => None,
    }
}

/// get_secrets manages the process of getting secrets from the Tower server in a way that can be
/// used by the local runtime during local app execution.
async fn get_secrets(config: &Config, env: &str) -> Result<HashMap<String, String>, Error> {
    let (private_key, public_key) = crypto::generate_key_pair();

    match api::export_secrets(&config, env, false, public_key).await {
        Ok(res) => {
            let mut secrets = HashMap::new();

            for secret in res.secrets {
                // we will decrypt each property and inject it into the vals map.
                let decrypted_value = crypto::decrypt(private_key.clone(), secret.encrypted_value.to_string())?;
                secrets.insert(secret.name, decrypted_value);
            }

            Ok(secrets)
        },
        Err(err) => {
            output::tower_error(err);
            Err(Error::FetchingSecretsFailed)
        }
    }
}

/// get_catalogs manages the process of exporting catalogs, decrypting their properties, and
/// preparting them for injection into the environment during app execution
async fn get_catalogs(config: &Config, env: &str) -> Result<HashMap<String, String>, Error> {
    let (private_key, public_key) = crypto::generate_key_pair();

    match api::export_catalogs(&config, env, false, public_key).await {
        Ok(res) => {
            let mut vals = HashMap::new();

            for catalog in res.catalogs {
                // we will decrypt each property and inject it into the vals map.
                for property in catalog.properties {
                    let decrypted_value = crypto::decrypt(private_key.clone(), property.encrypted_value.to_string())?;
                    let name = create_pyiceberg_catalog_property_name(&catalog.name, &property.name);
                    vals.insert(name, decrypted_value);
                }
            }

            Ok(vals)
        },
        Err(err) => {
            output::tower_error(err);
            Err(Error::FetchingCatalogsFailed)
        }
    }
}

/// load_towerfile manages the process of loading a Towerfile from a given path in an interactive
/// way. That means it will not return if the Towerfile can't be loaded and instead will publish an
/// error.
fn load_towerfile(path: &PathBuf) -> Towerfile {
    Towerfile::from_path(path.clone()).unwrap_or_else(|err| {
        debug!("Failed to load Towerfile from path `{:?}`: {}", path, err);
        output::config_error(err);
        std::process::exit(1);
    })
}

/// build_package manages the process of building a package in an interactive way for local app
/// execution. If the pacakge fails to build for wahatever reason, the app will exit.
async fn build_package(towerfile: &Towerfile) -> Package {
    let mut spinner = output::spinner("Building package...");
    let package_spec = PackageSpec::from_towerfile(towerfile);
    match Package::build(package_spec).await {
        Ok(package) => {
            spinner.success();
            package
        }
        Err(err) => {
            spinner.failure();
            debug!("Failed to build package: {}", err);
            output::package_error(err);
            std::process::exit(1);
        }
    }
}

/// monitor_output is a helper function that will monitor the output of a given output channel and
/// plops it down on stdout.
async fn monitor_output(output: OutputReceiver) {
    loop {
        if let Some(line) = output.lock().await.recv().await {
            let ts = &line.time;
            let msg = &line.line;
            output::log_line(&ts.to_rfc3339(), msg, output::LogLineType::Local);
        } else {
            break;
        }
    }
}

/// monitor_status is a helper function that will monitor the status of a given app and waits for
/// it to progress to a terminal state.
async fn monitor_status(app: LocalApp) {
    loop {
        if let Ok(status) = app.status().await {
            match status {
                tower_runtime::Status::Exited => {
                    output::success("Your app exited cleanly.");
                    break;
                }
                tower_runtime::Status::Crashed { .. } => {
                    output::failure("Your app crashed!");
                    break;
                }
                _ => continue,
            }
        }
    }
}

fn create_pyiceberg_catalog_property_name(catalog_name: &str, property_name: &str) -> String {
    let catalog_name = catalog_name.replace('.', "_").replace(':', "_").to_uppercase();
    let property_name = property_name.replace('.', "_").replace(':', "_").to_uppercase();

    format!("PYICEBERG_CATALOG__{}__{}", catalog_name, property_name)
}

