use tower_api::apis::Error;
use config::Config;
use http::StatusCode;
use std::collections::HashMap;
use tower_api::apis::ResponseContent;
use tower_telemetry::debug;

/// Helper trait to extract the successful response data from API responses
pub trait ResponseEntity {
    /// The type of data contained in the successful response
    type Data;
    
    /// Extract the data from the response, returning None if it's not the expected type
    fn extract_data(self) -> Option<Self::Data>;
}

pub async fn describe_app(config: &Config, slug: &str) -> Result<tower_api::models::DescribeAppResponse, Error<tower_api::apis::default_api::DescribeAppError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DescribeAppParams {
        slug: slug.to_string(),
        runs: None,
    };

    unwrap_api_response(tower_api::apis::default_api::describe_app(api_config, params)).await
}

pub async fn list_apps(config: &Config) -> Result<tower_api::models::ListAppsResponse, Error<tower_api::apis::default_api::ListAppsError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::ListAppsParams {
        query: None,
        page: None,
        page_size: None,
        num_runs: Some(0),
        sort: None,
        filter: None,
    };

    unwrap_api_response(tower_api::apis::default_api::list_apps(api_config, params)).await
}

pub async fn create_app(config: &Config, name: &str, slug: &str, description: &str) -> Result<tower_api::models::CreateAppResponse, Error<tower_api::apis::default_api::CreateAppError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::CreateAppParams {
        create_app_params: tower_api::models::CreateAppParams{
            name: name.to_string(),
            slug: Some(slug.to_string()),
            short_description: Some(description.to_string()),
            schema: None,
        },
    };

    unwrap_api_response(tower_api::apis::default_api::create_app(api_config, params)).await 
}

pub async fn delete_app(config: &Config, slug: &str) -> Result<tower_api::models::DeleteAppResponse, Error<tower_api::apis::default_api::DeleteAppError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DeleteAppParams {
        slug: slug.to_string(),
    };

    unwrap_api_response(tower_api::apis::default_api::delete_app(api_config, params)).await
}

pub async fn describe_run_logs(config: &Config, slug: &str, seq: i64) -> Result<tower_api::models::DescribeRunLogsResponse, Error<tower_api::apis::default_api::DescribeRunLogsError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DescribeRunLogsParams {
        slug: slug.to_string(),
        seq,
    };

    unwrap_api_response(tower_api::apis::default_api::describe_run_logs(api_config, params)).await
}

pub async fn run_app(config: &Config, slug: &str, env: &str, params: HashMap<String, String>) -> Result<tower_api::models::RunAppResponse, Error<tower_api::apis::default_api::RunAppError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::RunAppParams {
        slug: slug.to_string(),
        run_app_params: tower_api::models::RunAppParams {
            schema: None,
            environment: env.to_string(),
            parameters: params,
            parent_run_id: None,
        },
    };

    unwrap_api_response(tower_api::apis::default_api::run_app(api_config, params)).await
}

pub async fn export_secrets(config: &Config, env: &str, all: bool, public_key: rsa::RsaPublicKey) -> Result<tower_api::models::ExportSecretsResponse, Error<tower_api::apis::default_api::ExportSecretsError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::ExportSecretsParams {
        export_secrets_params: tower_api::models::ExportSecretsParams {
            schema: None,
            all,
            public_key: crypto::serialize_public_key(public_key),
            environment: env.to_string(),
            page: 1,
            page_size: 100,
        },
    };

    unwrap_api_response(tower_api::apis::default_api::export_secrets(api_config, params)).await
} 

pub async fn export_catalogs(config: &Config, env: &str, all: bool, public_key: rsa::RsaPublicKey) -> Result<tower_api::models::ExportCatalogsResponse, Error<tower_api::apis::default_api::ExportCatalogsError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::ExportCatalogsParams {
        export_catalogs_params: tower_api::models::ExportCatalogsParams {
            schema: None,
            all,
            public_key: crypto::serialize_public_key(public_key),
            environment: env.to_string(),
            page: 1,
            page_size: 100,
        },
    };

    unwrap_api_response(tower_api::apis::default_api::export_catalogs(api_config, params)).await
} 


pub async fn list_secrets(config: &Config, env: &str, all: bool) -> Result<tower_api::models::ListSecretsResponse, Error<tower_api::apis::default_api::ListSecretsError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::ListSecretsParams {
        environment: Some(env.to_string()),
        all: Some(all),
        page: None,
        page_size: None,
    };

    unwrap_api_response(tower_api::apis::default_api::list_secrets(api_config, params)).await
}

pub async fn create_secret(config: &Config, name: &str, env: &str, encrypted_value: &str, preview: &str) -> Result<tower_api::models::CreateSecretResponse, Error<tower_api::apis::default_api::CreateSecretError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::CreateSecretParams {
        create_secret_params: tower_api::models::CreateSecretParams {
            name: name.to_string(),
            environment: env.to_string(),
            encrypted_value: encrypted_value.to_string(),
            preview: preview.to_string(),
            schema: None,
        },
    };

    unwrap_api_response(tower_api::apis::default_api::create_secret(api_config, params)).await
}

pub async fn describe_secrets_key(config: &Config) -> Result<tower_api::models::DescribeSecretsKeyResponse, Error<tower_api::apis::default_api::DescribeSecretsKeyError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DescribeSecretsKeyParams {
        format: None,
    };

    unwrap_api_response(tower_api::apis::default_api::describe_secrets_key(api_config, params)).await
}

pub async fn delete_secret(config: &Config, name: &str, env: &str) -> Result<tower_api::models::DeleteSecretResponse, Error<tower_api::apis::default_api::DeleteSecretError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DeleteSecretParams {
        name: name.to_string(),
        environment: Some(env.to_string()),
    };

    unwrap_api_response(tower_api::apis::default_api::delete_secret(api_config, params)).await
}

pub async fn create_device_login_ticket(config: &Config) -> Result<tower_api::models::CreateDeviceLoginTicketResponse, Error<tower_api::apis::default_api::CreateDeviceLoginTicketError>> {
    let api_config = &config.into();
    unwrap_api_response(tower_api::apis::default_api::create_device_login_ticket(api_config)).await
}

pub async fn describe_device_login_session(config: &Config, device_code: &str) -> Result<tower_api::models::DescribeDeviceLoginSessionResponse, Error<tower_api::apis::default_api::DescribeDeviceLoginSessionError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DescribeDeviceLoginSessionParams {
        device_code: device_code.to_string(),
    };

    unwrap_api_response(tower_api::apis::default_api::describe_device_login_session(api_config, params)).await
}

pub async fn refresh_session(config: &Config) -> Result<tower_api::models::RefreshSessionResponse, Error<tower_api::apis::default_api::RefreshSessionError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::RefreshSessionParams {
        refresh_session_params: tower_api::models::RefreshSessionParams::new(),
    };

    unwrap_api_response(tower_api::apis::default_api::refresh_session(api_config, params)).await
}

/// Helper function to handle Tower API responses and extract the relevant data
async fn unwrap_api_response<T, F, V>(api_call: F) -> Result<T::Data, Error<V>>
where
    F: std::future::Future<Output = Result<ResponseContent<T>, Error<V>>>,
    T: ResponseEntity,
{
    match api_call.await {
        Ok(response) => {
            debug!("tower trace ID: {}", response.tower_trace_id);
            debug!("Response from server: {}", response.content);

            if let Some(entity) = response.entity {
                if let Some(data) = entity.extract_data() {
                    Ok(data)
                } else {
                    let err = Error::ResponseError(
                        tower_api::apis::ResponseContent {
                            tower_trace_id: "".to_string(),
                            status: StatusCode::NO_CONTENT,
                            content: "Received a response from the server that the CLI wasn't able to understand".to_string(),
                            entity: None,
                        },
                    );
                    Err(err)
                }
            } else {
                let err = Error::ResponseError(
                    tower_api::apis::ResponseContent {
                        tower_trace_id: "".to_string(),
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

impl ResponseEntity for tower_api::apis::default_api::ExportCatalogsSuccess {
    type Data = tower_api::models::ExportCatalogsResponse;

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
            Self::UnknownValue(data) => {
                match serde_json::from_value(data) {
                    Ok(obj) => Some(obj),
                    Err(err) => {
                        debug!("Failed to deserialize ListAppsResponse from value: {}", err);
                        None
                    },
                }
            }
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

impl ResponseEntity for tower_api::apis::default_api::RunAppSuccess {
    type Data = tower_api::models::RunAppResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::Status201(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::DeleteAppSuccess {
    type Data = tower_api::models::DeleteAppResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(res) => Some(res),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::DeleteSecretSuccess {
    type Data = tower_api::models::DeleteSecretResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(res) => Some(res),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::DescribeRunLogsSuccess {
    type Data = tower_api::models::DescribeRunLogsResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(resp) => Some(resp),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::CreateAppSuccess {
    type Data = tower_api::models::CreateAppResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(resp) => Some(resp),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::CreateDeviceLoginTicketSuccess {
    type Data = tower_api::models::CreateDeviceLoginTicketResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(resp) => Some(resp),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::DescribeDeviceLoginSessionSuccess {
    type Data = tower_api::models::DescribeDeviceLoginSessionResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(resp) => Some(resp),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::RefreshSessionSuccess {
    type Data = tower_api::models::RefreshSessionResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(resp) => Some(resp),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::DescribeSessionSuccess {
    type Data = tower_api::models::DescribeSessionResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(resp) => Some(resp),
            Self::UnknownValue(_) => None,
        }
    }
}
