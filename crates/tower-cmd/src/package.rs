use clap::{Arg, ArgMatches, Command};
use config::{Config, Towerfile};
use std::path::PathBuf;
use tokio::fs;

use crate::output;
use tower_package::{Package, PackageSpec};
use tower_telemetry::debug;

pub fn package_cmd() -> Command {
    Command::new("package")
        .hide(true)
        .arg(
            Arg::new("dir")
                .long("dir")
                .short('d')
                .help("The directory containing the app to package")
                .default_value("."),
        )
        .arg(
            Arg::new("output")
                .long("output")
                .short('o')
                .help("Output path for the package file")
                .value_name("PATH")
                .required(true),
        )
        .about("Create a package tar.gz file from your app without deploying")
}

pub async fn do_package(_config: Config, args: &ArgMatches) {
    // Determine the directory to build the package from
    let dir = PathBuf::from(
        args.get_one::<String>("dir")
            .expect("dir argument should have default value"),
    );
    debug!("Building package from directory: {:?}", dir);

    let path = dir.join("Towerfile");

    match Towerfile::from_path(path) {
        Ok(towerfile) => {
            let spec = PackageSpec::from_towerfile(&towerfile);
            let mut spinner = output::spinner("Building package...");

            match Package::build(spec).await {
                Ok(package) => {
                    spinner.success();

                    // Get the output path
                    let output_path = args
                        .get_one::<String>("output")
                        .expect("output path is required");

                    // Save the package
                    match save_package(&package, output_path).await {
                        Ok(_) => {
                            output::success(&format!(
                                "Package created successfully: {}",
                                output_path
                            ));
                        }
                        Err(err) => {
                            output::error(&format!("Failed to save package: {}", err));
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

async fn save_package(
    package: &Package,
    output_path: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let package_path = package
        .package_file_path
        .as_ref()
        .ok_or("No package file path found")?;

    let output_path = PathBuf::from(output_path);

    // Create parent directories if they don't exist
    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent).await?;
    }

    // Copy the package file to the specified location
    fs::copy(package_path, &output_path).await?;

    Ok(())
}
