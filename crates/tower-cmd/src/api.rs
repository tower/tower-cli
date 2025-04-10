use tower_api::apis::Error;

/// Helper trait to extract the successful response data from API responses
pub trait ResponseEntity {
    /// The type of data contained in the successful response
    type Data;
    
    /// Extract the data from the response, returning None if it's not the expected type
    fn extract_data(self) -> Option<Self::Data>;
}

/// Helper function to handle Tower API responses and extract the relevant data
pub async fn handle_api_response<T, F, V, Fut>(api_call: F) -> Result<T::Data, Error<V>>
where
    F: FnOnce() -> Fut,
    Fut: std::future::Future<Output = Result<tower_api::apis::ResponseContent<T>, Error<V>>>,
    T: ResponseEntity,
{
    match api_call().await {
        Ok(response) => {
            if let Some(entity) = response.entity {
                if let Some(data) = entity.extract_data() {
                    Ok(data)
                } else {
                    let err = Error::ResponseError(
                        tower_api::apis::ResponseContent {
                            status: StatusCode::NO_CONTENT,
                            content: "Received an unknown response from the server".to_string(),
                            entity: None,
                        },
                    );
                    Err(err)
                }
            } else {
                let err = Error::ResponseError(
                    tower_api::apis::ResponseContent {
                        status: StatusCode::NO_CONTENT,
                        content: "Empty response from server".to_string(),
                        entity: None,
                    },
                );
                Err(err)
            }
        }
        Err(err) => Err(err),
    }
}

// Implement ResponseEntity for the specific API response types
impl ResponseEntity for tower_api::apis::default_api::ListSecretsSuccess {
    type Data = tower_api::models::ListSecretsResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::ExportSecretsSuccess {
    type Data = tower_api::models::ExportSecretsResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::CreateSecretSuccess {
    type Data = tower_api::models::CreateSecretResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::DescribeSecretsKeySuccess {
    type Data = tower_api::models::DescribeSecretsKeyResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}
use http::StatusCode;
use tower_api::apis::Error as ApiError;
use std::future::Future;

use crate::output;

/// Helper function to handle operations with spinner
pub async fn with_spinner<T, F, V>(
    message: &str, 
    operation: F,
    resource_name: Option<&str>
) -> T 
where
    F: Future<Output = Result<T, tower_api::apis::Error<V>>>,
{
    let mut spinner = output::spinner(message);
    match operation.await {
        Ok(result) => {
            spinner.success();
            result
        }
        Err(err) => {
            spinner.failure();
            match err {
                ApiError::ResponseError(err) => {
                    match err.status {
                        StatusCode::NOT_FOUND => {
                            // Extract the resource type from the message
                            let resource_type = message
                                .trim_end_matches("...")
                                .trim_start_matches("Fetching ")
                                .trim_start_matches("Creating ")
                                .trim_start_matches("Updating ")
                                .trim_start_matches("Deleting ");
                            
                            if let Some(name) = resource_name {
                                output::failure(&format!("{} '{}' not found", resource_type, name));
                            } else {
                                output::failure(&format!("The {} was not found", resource_type));
                            }
                        },
                        StatusCode::BAD_REQUEST => {
                            output::failure("Something went wrong while talking to Tower. You might need to upgrade your Tower CLI.");
                        },
                        StatusCode::UNAUTHORIZED => {
                            output::failure("You need to login! Try running `tower login` and then trying again.");
                        },
                        StatusCode::FORBIDDEN => {
                            output::failure("You are not authorized to perform this action.");
                        },
                        StatusCode::INTERNAL_SERVER_ERROR => {
                            output::failure("It looks like Tower is having a problem. Try again later on.");
                        },
                        _ => {
                            log::debug!("Unexpected error: {}", err.content);
                            output::failure("Something went wrong while talking to Tower. Try again in a bit.");
                        }
                    }
                    std::process::exit(1);
                }
                _ => {
                    output::failure(&format!("Unexpected error: {}", err));
                    std::process::exit(1);
                }
            }
        }
    }
}
