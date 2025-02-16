use tower_api::{Client, TowerError};
use promptly::prompt_default;
use crate::output;

pub async fn ensure_app_exists(client: &Client, app_name: &str, description: &str) -> Result<(), TowerError> {
    match client.get_app(app_name).await {
        Ok(_) => Ok(()),
        Err(err) => {
            if matches!(err.code.as_str(), "tower_apps_not_found_error") {
                if prompt_default(format!("App '{}' does not exist. Would you like to create it?", app_name), false)
                    .unwrap_or(false) 
                {
                    match client.create_app(app_name, description).await {
                        Ok(_) => {
                            output::success(&format!("Created app '{}'", app_name));
                            Ok(())
                        },
                        Err(e) => Err(e)
                    }
                } else {
                    Err(err)
                }
            } else {
                Err(err)
            }
        }
    }
}
