use crate::{output, util};
use reqwest::{Body, Client as ReqwestClient, Method};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tokio::fs::File;
use tokio_util::io::ReaderStream;
use tower_package::{compute_sha256_file, Package};
use tower_telemetry::debug;

use tower_api::apis::configuration::Configuration;
use tower_api::apis::default_api::DeployAppError;
use tower_api::apis::Error;
use tower_api::apis::ResponseContent;
use tower_api::models::DeployAppResponse;

pub async fn upload_file_with_progress(
    api_config: &Configuration,
    endpoint_url: String,
    file_path: PathBuf,
    content_type: &str,
    progress_cb: Box<dyn Fn(u64, u64) + Send + Sync>,
) -> Result<DeployAppResponse, Error<DeployAppError>> {
    let package_hash = match compute_sha256_file(&file_path).await {
        Ok(hash) => hash,
        Err(e) => {
            debug!("Failed to compute package hash: {}", e);
            output::die("Tower CLI failed to properly prepare your package for deployment. Check that you have permissions to read/write to your temporary directory, and if it keeps happening contact Tower support at https://tower.dev");
        }
    };

    // Get the file and its metadata
    let file = File::open(file_path).await?;
    let metadata = file.metadata().await?;
    let file_size = metadata.len();

    // Create a stream with progress tracking
    let reader_stream = ReaderStream::new(file);
    let progress_stream =
        util::progress::ProgressStream::new(reader_stream, file_size, progress_cb).await?;

    // Create the request with proper headers
    let client = ReqwestClient::new();
    let mut req = client
        .request(Method::POST, endpoint_url)
        .header("X-Tower-Checksum-SHA256", package_hash)
        .header("Content-Type", content_type)
        .header("Content-Encoding", "gzip")
        .body(Body::wrap_stream(progress_stream));

    // Add authorization if available
    if let Some(token) = &api_config.bearer_access_token {
        req = req.header("Authorization", format!("Bearer {}", token));
    }

    // Send the request
    let response = req.send().await?;

    // Handle the response
    if response.status().is_success() {
        let resp: DeployAppResponse = response.json().await?;
        Ok(resp)
    } else {
        // NOTE: I just kind of lifted this out of the generated client to figure out how to
        // deserialize this type into something that is useful and resembles the original/generated
        // stuff.
        let tower_trace_id = response
            .headers()
            .get("x-tower-trace-id")
            .and_then(|v| v.to_str().ok())
            .unwrap_or("")
            .to_string();

        let status = response.status();
        let content = response.text().await?;
        let entity: Option<DeployAppError> = serde_json::from_str(&content).ok();

        Err(Error::ResponseError(ResponseContent {
            tower_trace_id,
            status,
            content,
            entity,
        }))
    }
}

pub async fn deploy_app_package(
    api_config: &tower_api::apis::configuration::Configuration,
    app_name: &str,
    package: Package,
) -> Result<DeployAppResponse, Error<DeployAppError>> {
    let progress_bar = Arc::new(Mutex::new(output::progress_bar("Deploying to Tower...")));

    let progress_callback = Box::new({
        let progress_bar = Arc::clone(&progress_bar);
        move |progress, total| {
            let progress_bar = progress_bar.lock().unwrap();
            progress_bar.set_length(total);
            progress_bar.set_position(progress);
        }
    });

    // Get the package file path
    let package_path = package.package_file_path.unwrap_or_else(|| {
        debug!("No package file path found");
        output::die("An error happened in Tower CLI that it couldn't recover from.");
    });

    // Create the URL for the API endpoint
    let base_url = &api_config.base_path;
    let url = format!("{}/apps/{}/deploy", base_url, app_name);

    // Upload the package
    let response = upload_file_with_progress(
        api_config,
        url,
        package_path,
        "application/tar",
        progress_callback,
    )
    .await?;

    // Finish the progress bar
    let progress_bar = progress_bar.lock().unwrap();
    progress_bar.finish();
    output::newline();

    Ok(response)
}
