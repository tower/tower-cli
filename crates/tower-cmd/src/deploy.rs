use clap::{Arg, ArgMatches, Command};
use config::{Config, Towerfile};
use futures_util::stream::Stream;
use reqwest::{Body, Client as ReqwestClient, Method};
use std::convert::From;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::{
    pin::Pin,
    task::{Context, Poll},
};
use tokio::fs::File;
use tokio_util::io::ReaderStream;
use tower_package::{Package, PackageSpec};

use crate::{output, util};

// Define the ProgressStream struct directly in deploy.rs
struct ProgressStream<R> {
    inner: R,
    progress: Arc<Mutex<u64>>,
    progress_cb: Box<dyn Fn(u64, u64) + Send + Sync>,
    total_size: u64,
}

impl<R> ProgressStream<R> {
    async fn new(
        inner: R,
        total_size: u64,
        progress_cb: Box<dyn Fn(u64, u64) + Send + Sync>,
    ) -> Result<Self, std::io::Error> {
        Ok(Self {
            inner,
            progress_cb,
            progress: Arc::new(Mutex::new(0)),
            total_size,
        })
    }
}

impl<R: Stream<Item = Result<bytes::Bytes, std::io::Error>> + Unpin> Stream for ProgressStream<R> {
    type Item = Result<bytes::Bytes, std::io::Error>;

    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        match Pin::new(&mut self.inner).poll_next(cx) {
            Poll::Ready(Some(Ok(chunk))) => {
                let chunk_size = chunk.len() as u64;
                let mut progress = self.progress.lock().unwrap();
                *progress += chunk_size;
                (self.progress_cb)(*progress, self.total_size);
                Poll::Ready(Some(Ok(chunk)))
            }
            other => other,
        }
    }
}

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
    let api_config = config.get_api_configuration().unwrap();
    // Determine the directory to build the package from
    let dir = resolve_path(args);
    log::debug!("Building package from directory: {:?}", dir);

    let path = dir.join("Towerfile");

    match Towerfile::from_path(path) {
        Ok(towerfile) => {
            // Add app existence check before proceeding
            if let Err(err) = util::ensure_app_exists(
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

                    let progress_bar =
                        Arc::new(Mutex::new(output::progress_bar("Deploying to Tower...")));

                    let progress_callback = Box::new({
                        let progress_bar = Arc::clone(&progress_bar);
                        move |progress, total| {
                            let progress_bar = progress_bar.lock().unwrap();
                            progress_bar.set_length(total);
                            progress_bar.set_position(progress);
                        }
                    });

                    // Custom implementation to upload the package
                    match upload_code(&api_config, &towerfile.app.name, package, progress_callback)
                        .await
                    {
                        Ok(version) => {
                            let progress_bar = progress_bar.lock().unwrap();
                            progress_bar.finish();
                            output::newline();

                            let line = format!(
                                "Version `{}` of your code has been deployed to Tower!",
                                version
                            );
                            output::success(&line);
                        }
                        Err(err) => {
                            let progress_bar = progress_bar.lock().unwrap();
                            progress_bar.finish();
                            output::newline();
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

// Add a custom function to handle the upload
async fn upload_code(
    api_config: &tower_api::apis::configuration::Configuration,
    app_name: &str,
    package: Package,
    progress_cb: Box<dyn Fn(u64, u64) + Send + Sync>,
) -> Result<String, Box<dyn std::error::Error>> {
    // Get the package file path
    let package_path = package.package_file_path.ok_or("No package file path")?;

    // Create the URL for the API endpoint
    let base_url = &api_config.base_path;
    let url = format!("{}/apps/{}/deploy", base_url, app_name);

    // Get the file and its metadata
    let file = File::open(package_path).await?;
    let metadata = file.metadata().await?;
    let file_size = metadata.len();

    // Create a stream with progress tracking
    let reader_stream = ReaderStream::new(file);
    let progress_stream = ProgressStream::new(reader_stream, file_size, progress_cb).await?;

    // Create the request with proper headers
    let client = ReqwestClient::new();
    let mut req = client
        .request(Method::POST, url)
        .header("Content-Type", "application/tar")
        .body(Body::wrap_stream(progress_stream));

    // Add authorization if available
    if let Some(token) = &api_config.bearer_access_token {
        req = req.header("Authorization", format!("Bearer {}", token));
    }

    // Send the request
    let response = req.send().await?;

    // Handle the response
    if response.status().is_success() {
        // Parse the response to get the version
        let json: serde_json::Value = response.json().await?;
        let version = json["code"]["version"]
            .as_str()
            .ok_or("Version not found in response")?
            .to_string();

        Ok(version)
    } else {
        Err(format!("Error: {}", response.status()).into())
    }
}
