use crate::{output, util};
use reqwest::{Body, Client as ReqwestClient, Method};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tokio::fs::File;
use tokio_util::io::ReaderStream;
use tower_package::Package;

pub async fn upload_file_with_progress(
    api_config: &tower_api::apis::configuration::Configuration,
    endpoint_url: String,
    file_path: PathBuf,
    content_type: &str,
    progress_cb: Box<dyn Fn(u64, u64) + Send + Sync>,
) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
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
        .header("Content-Type", content_type)
        .body(Body::wrap_stream(progress_stream));

    // Add authorization if available
    if let Some(token) = &api_config.bearer_access_token {
        req = req.header("Authorization", format!("Bearer {}", token));
    }

    // Send the request
    let response = req.send().await?;

    // Handle the response
    if response.status().is_success() {
        let json: serde_json::Value = response.json().await?;
        Ok(json)
    } else {
        Err(format!("Error: {}", response.status()).into())
    }
}

pub async fn deploy_app_package(
    api_config: &tower_api::apis::configuration::Configuration,
    app_name: &str,
    package: Package,
) -> Result<String, Box<dyn std::error::Error>> {
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
    let package_path = package.package_file_path.ok_or("No package file path")?;

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

    // Extract the version
    let version = response["version"]["version"]
        .as_str()
        .ok_or("Version not found in response")?
        .to_string();

    Ok(version)
}
