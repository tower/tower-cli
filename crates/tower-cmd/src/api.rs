use tower_api::apis::Error;
use http::StatusCode;
use std::future::Future;

use crate::output;

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

/// Helper function to handle operations with spinner
pub async fn with_spinner<T, F, V>(
    message: &str, 
    operation: F,
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
            output::tower_error(err);
            std::process::exit(1);
        }
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

impl ResponseEntity for tower_api::apis::default_api::ListAppsSuccess {
    type Data = tower_api::models::ListAppsResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::DescribeAppSuccess {
    type Data = tower_api::models::DescribeAppResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}
