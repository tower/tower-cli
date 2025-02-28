use anyhow::Result;
use log;
use reqwest;
use serde_json::Value;

pub fn current_version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

pub async fn check_latest_version() -> Result<Option<String>> {
    let client = reqwest::Client::new();
    let pypi_url = std::env::var("TOWER_PYPI_URL")
        .unwrap_or_else(|_| "https://pypi.org".to_string());
    let url = format!("{}/pypi/tower-cli/json", pypi_url);
    
    let resp = client
        .get(url)
        .send()
        .await?;
        
    let status = resp.status();
    log::debug!("PyPI returned status code: {}", status);
    
    if status.is_success() {
        let json: Value = resp.json().await?;
        if let Some(version) = json.get("info")
            .and_then(|info| info.get("version"))
            .and_then(|v| v.as_str()) {
            return Ok(Some(version.to_string()));
        }
    }
    Ok(None)
}
