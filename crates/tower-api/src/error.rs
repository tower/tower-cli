use serde::{Deserialize, Serialize};
use reqwest::Error;

#[derive(Serialize, Deserialize)]
pub struct TowerError {
    pub code: String,
    pub domain: String,
    pub description: String,
}

impl From<Error> for TowerError {
    fn from(err: Error) -> Self {
        if err.is_redirect() {
            Self {
                code: "tower_cli_redirect_error".to_string(),
                domain: "tower_cli".to_string(),
                description: "The Tower API is redirecting your request in a way that Tower CLI cannot handle".to_string(),
            }
        } else if err.is_status() {
            Self {
                code: "tower_cli_status_error".to_string(),
                domain: "tower_cli".to_string(),
                description: format!("An unexpected status code (status code: {}) was returned from the Tower API", err.status().unwrap()),
            }
        } else if err.is_connect() {
            Self {
                code: "tower_cli_connect_error".to_string(),
                domain: "tower_cli".to_string(),
                description: "A connection to the Tower API could not be established".to_string(),
            }
        } else if err.is_body() {
            Self {
                code: "tower_cli_body_error".to_string(),
                domain: "tower_cli".to_string(),
                description: "There was something wrong with the body of the response from the Tower API".to_string(),
            }
        } else if err.is_decode() {
            log::debug!("failed to decode the body: {:?}", err);

            // TODO: This means there was something critically wrong with how we're using the API.
            // Perhaps this should be a more serious error?
            Self {
                code: "tower_cli_decode_error".to_string(),
                domain: "tower_cli".to_string(),
                description: "There was an error decoding the response from the Tower API".to_string(),
            }
        } else if err.is_builder() {
            Self {
                code: "tower_cli_builder_error".to_string(),
                domain: "tower_cli".to_string(),
                description: "There was an unexpected internal error in the Tower CLI request builder".to_string(),
            }
        } else if err.is_timeout() {
            Self {
                code: "tower_cli_timeout_error".to_string(),
                domain: "tower_cli".to_string(),
                description: "A request to the Tower API timed out".to_string(),
            }
        } else {
            log::debug!("Unexpected error: {:?}", err);

            Self {
                code: "tower_cli_error".to_string(),
                domain: "tower_cli".to_string(),
                description: "An unexpected or unknown error occured!".to_string(),
            }   
        }
    }
}
