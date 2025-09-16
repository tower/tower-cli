use anyhow::Result;
use chrono::{Duration, Utc};
use reqwest;
use serde_json::Value;
use tower_telemetry::debug;

pub fn current_version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

pub async fn should_check_latest_version() -> bool {
    let dt = config::get_last_version_check_timestamp();
    let window = Utc::now() - Duration::minutes(5);

    // If we haven't checked in the last 5 minutes, then we should check.
    dt < window
}

pub async fn check_latest_version() -> Result<Option<String>> {
    let client = reqwest::Client::new();
    let pypi_url =
        std::env::var("TOWER_PYPI_URL").unwrap_or_else(|_| "https://pypi.org".to_string());
    let url = format!("{}/pypi/tower/json", pypi_url);

    let resp = client.get(url).send().await?;

    let status = resp.status();
    debug!("PyPI returned status code: {}", status);

    if status.is_success() {
        // Update the config so we don't check more often.
        config::set_last_version_check_timestamp(Utc::now());

        let json: Value = resp.json().await?;
        if let Some(version) = json
            .get("info")
            .and_then(|info| info.get("version"))
            .and_then(|v| v.as_str())
        {
            return Ok(Some(version.to_string()));
        }
    }
    Ok(None)
}
