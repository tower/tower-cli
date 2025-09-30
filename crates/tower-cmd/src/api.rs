use config::Config;
use futures_util::StreamExt;
use http::StatusCode;
use reqwest_eventsource::{Event, EventSource};
use std::collections::HashMap;
use tokio::sync::mpsc;
use tower_api::apis::configuration;
use tower_api::apis::Error;
use tower_api::apis::ResponseContent;
use tower_api::models::RunParameter;
use tower_telemetry::debug;

/// Helper trait to extract the successful response data from API responses
pub trait ResponseEntity {
    /// The type of data contained in the successful response
    type Data;

    /// Extract the data from the response, returning None if it's not the expected type
    fn extract_data(self) -> Option<Self::Data>;
}

pub async fn describe_app(
    config: &Config,
    name: &str,
) -> Result<
    tower_api::models::DescribeAppResponse,
    Error<tower_api::apis::default_api::DescribeAppError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DescribeAppParams {
        name: name.to_string(),
        runs: None,
        start_at: None,
        end_at: None,
        timezone: None,
    };

    unwrap_api_response(tower_api::apis::default_api::describe_app(
        api_config, params,
    ))
    .await
}

pub async fn list_apps(
    config: &Config,
) -> Result<tower_api::models::ListAppsResponse, Error<tower_api::apis::default_api::ListAppsError>>
{
    let api_config = &config.into();

    let params = tower_api::apis::default_api::ListAppsParams {
        query: None,
        page: None,
        page_size: None,
        num_runs: Some(0),
        sort: None,
        filter: None,
        environment: None,
    };

    unwrap_api_response(tower_api::apis::default_api::list_apps(api_config, params)).await
}

pub async fn create_app(
    config: &Config,
    name: &str,
    description: &str,
) -> Result<tower_api::models::CreateAppResponse, Error<tower_api::apis::default_api::CreateAppError>>
{
    let api_config = &config.into();

    let params = tower_api::apis::default_api::CreateAppParams {
        create_app_params: tower_api::models::CreateAppParams {
            schema: None,
            name: name.to_string(),
            short_description: Some(description.to_string()),
            slug: None,
            is_externally_accessible: None,
        },
    };

    unwrap_api_response(tower_api::apis::default_api::create_app(api_config, params)).await
}

pub async fn delete_app(
    config: &Config,
    name: &str,
) -> Result<tower_api::models::DeleteAppResponse, Error<tower_api::apis::default_api::DeleteAppError>>
{
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DeleteAppParams {
        name: name.to_string(),
    };

    unwrap_api_response(tower_api::apis::default_api::delete_app(api_config, params)).await
}

pub async fn describe_run(
    config: &Config,
    app_name: &str,
    seq: i64,
) -> Result<
    tower_api::models::DescribeRunResponse,
    Error<tower_api::apis::default_api::DescribeRunError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DescribeRunParams {
        name: app_name.to_string(),
        seq,
    };

    unwrap_api_response(tower_api::apis::default_api::describe_run(
        api_config, params,
    ))
    .await
}

pub async fn describe_run_logs(
    config: &Config,
    name: &str,
    seq: i64,
) -> Result<
    tower_api::models::DescribeRunLogsResponse,
    Error<tower_api::apis::default_api::DescribeRunLogsError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DescribeRunLogsParams {
        name: name.to_string(),
        seq,
    };

    unwrap_api_response(tower_api::apis::default_api::describe_run_logs(
        api_config, params,
    ))
    .await
}

pub async fn run_app(
    config: &Config,
    name: &str,
    env: &str,
    params: HashMap<String, String>,
) -> Result<tower_api::models::RunAppResponse, Error<tower_api::apis::default_api::RunAppError>> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::RunAppParams {
        name: name.to_string(),
        run_app_params: tower_api::models::RunAppParams {
            schema: None,
            environment: env.to_string(),
            parameters: params,
            parent_run_id: None,
        },
    };

    unwrap_api_response(tower_api::apis::default_api::run_app(api_config, params)).await
}

pub async fn export_secrets(
    config: &Config,
    env: &str,
    all: bool,
    public_key: rsa::RsaPublicKey,
) -> Result<
    tower_api::models::ExportSecretsResponse,
    Error<tower_api::apis::default_api::ExportSecretsError>,
> {
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

    unwrap_api_response(tower_api::apis::default_api::export_secrets(
        api_config, params,
    ))
    .await
}

pub async fn export_catalogs(
    config: &Config,
    env: &str,
    all: bool,
    public_key: rsa::RsaPublicKey,
) -> Result<
    tower_api::models::ExportCatalogsResponse,
    Error<tower_api::apis::default_api::ExportCatalogsError>,
> {
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

    unwrap_api_response(tower_api::apis::default_api::export_catalogs(
        api_config, params,
    ))
    .await
}

pub async fn list_secrets(
    config: &Config,
    env: &str,
    all: bool,
) -> Result<
    tower_api::models::ListSecretsResponse,
    Error<tower_api::apis::default_api::ListSecretsError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::ListSecretsParams {
        environment: Some(env.to_string()),
        all: Some(all),
        page: None,
        page_size: None,
    };

    unwrap_api_response(tower_api::apis::default_api::list_secrets(
        api_config, params,
    ))
    .await
}

pub async fn create_secret(
    config: &Config,
    name: &str,
    env: &str,
    encrypted_value: &str,
    preview: &str,
) -> Result<
    tower_api::models::CreateSecretResponse,
    Error<tower_api::apis::default_api::CreateSecretError>,
> {
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

    unwrap_api_response(tower_api::apis::default_api::create_secret(
        api_config, params,
    ))
    .await
}

pub async fn describe_secrets_key(
    config: &Config,
) -> Result<
    tower_api::models::DescribeSecretsKeyResponse,
    Error<tower_api::apis::default_api::DescribeSecretsKeyError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DescribeSecretsKeyParams { format: None };

    unwrap_api_response(tower_api::apis::default_api::describe_secrets_key(
        api_config, params,
    ))
    .await
}

pub async fn delete_secret(
    config: &Config,
    name: &str,
    env: &str,
) -> Result<
    tower_api::models::DeleteSecretResponse,
    Error<tower_api::apis::default_api::DeleteSecretError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DeleteSecretParams {
        name: name.to_string(),
        environment: Some(env.to_string()),
    };

    unwrap_api_response(tower_api::apis::default_api::delete_secret(
        api_config, params,
    ))
    .await
}

pub async fn create_device_login_ticket(
    config: &Config,
) -> Result<
    tower_api::models::CreateDeviceLoginTicketResponse,
    Error<tower_api::apis::default_api::CreateDeviceLoginTicketError>,
> {
    let api_config = &config.into();
    unwrap_api_response(tower_api::apis::default_api::create_device_login_ticket(
        api_config,
    ))
    .await
}

pub async fn describe_device_login_session(
    config: &Config,
    device_code: &str,
) -> Result<
    tower_api::models::DescribeDeviceLoginSessionResponse,
    Error<tower_api::apis::default_api::DescribeDeviceLoginSessionError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DescribeDeviceLoginSessionParams {
        device_code: device_code.to_string(),
    };

    unwrap_api_response(tower_api::apis::default_api::describe_device_login_session(
        api_config, params,
    ))
    .await
}

pub async fn refresh_session(
    config: &Config,
) -> Result<
    tower_api::models::RefreshSessionResponse,
    Error<tower_api::apis::default_api::RefreshSessionError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::RefreshSessionParams {
        refresh_session_params: tower_api::models::RefreshSessionParams::new(),
    };

    unwrap_api_response(tower_api::apis::default_api::refresh_session(
        api_config, params,
    ))
    .await
}

pub enum LogStreamEvent {
    EventLog(tower_api::models::RunLogLine),
    EventWarning(tower_api::models::EventWarning),
}

#[derive(Debug)]
pub enum LogStreamError {
    Reqwest(reqwest::Error),
    Unknown,
}

impl From<reqwest_eventsource::CannotCloneRequestError> for LogStreamError {
    fn from(err: reqwest_eventsource::CannotCloneRequestError) -> Self {
        debug!("Failed to clone request {:?}", err);
        LogStreamError::Unknown
    }
}

async fn drain_run_logs_stream(mut source: EventSource, tx: mpsc::Sender<LogStreamEvent>) {
    while let Some(event) = source.next().await {
        match event {
            Ok(reqwest_eventsource::Event::Open) => {
                panic!("Received unexpected open event in log stream. This shouldn't happen.");
            }
            Ok(Event::Message(message)) => {
                match message.event.as_str() {
                    "log" => {
                        let event_log = serde_json::from_str(&message.data);

                        match event_log {
                            Ok(event) => {
                                tx.send(LogStreamEvent::EventLog(event)).await.ok();
                            }
                            Err(err) => {
                                debug!(
                                    "Failed to parse log message: {}. Error: {}",
                                    message.data, err
                                );
                            }
                        };
                    }
                    "warning" => {
                        let event_warning = serde_json::from_str(&message.data);
                        if let Ok(event) = event_warning {
                            tx.send(LogStreamEvent::EventWarning(event)).await.ok();
                        } else {
                            debug!("Failed to parse warning message: {:?}", message.data);
                        }
                    }
                    _ => {
                        debug!("Unknown or unsupported log message: {:?}", message);
                    }
                };
            }
            Err(err) => {
                debug!("Error in log stream: {}", err);
                break; // Exit on error
            }
        }
    }
}

pub async fn stream_run_logs(
    config: &Config,
    app_name: &str,
    seq: i64,
) -> Result<mpsc::Receiver<LogStreamEvent>, LogStreamError> {
    let api_config: configuration::Configuration = config.into();

    // These represent the messages that we'll stream to the client.
    let (tx, rx) = mpsc::channel(1);

    // This code is copied from tower-api. Since that code is generated, there's not really a good
    // way to share this code between here and the rest of the app.
    let name = tower_api::apis::urlencode(app_name);
    let uri = format!(
        "{}/apps/{name}/runs/{seq}/logs/stream",
        api_config.base_path,
        name = name,
        seq = seq
    );
    let mut builder = api_config.client.request(reqwest::Method::GET, &uri);

    if let Some(ref user_agent) = api_config.user_agent {
        builder = builder.header(reqwest::header::USER_AGENT, user_agent.clone());
    }

    if let Some(ref token) = api_config.bearer_access_token {
        builder = builder.bearer_auth(token.to_owned());
    };

    // Now let's try to open the event source with the server.
    let mut source = EventSource::new(builder)?;

    if let Some(event) = source.next().await {
        match event {
            Ok(Event::Open) => {
                tokio::spawn(drain_run_logs_stream(source, tx));
                Ok(rx)
            }
            Ok(Event::Message(message)) => {
                // This is a bug in the program and should never happen.
                panic!(
                    "Received message when expected an open event. Message: {:?}",
                    message
                );
            }
            Err(err) => match err {
                reqwest_eventsource::Error::Transport(e) => Err(LogStreamError::Reqwest(e)),
                reqwest_eventsource::Error::StreamEnded => {
                    drop(tx);
                    Ok(rx)
                }
                _ => Err(LogStreamError::Unknown),
            },
        }
    } else {
        // If we didn't get an event, we can't stream logs.
        Err(LogStreamError::Unknown)
    }
}

/// Helper function to handle Tower API responses and extract the relevant data
async fn unwrap_api_response<T, F, V>(api_call: F) -> Result<T::Data, Error<V>>
where
    F: std::future::Future<Output = Result<ResponseContent<T>, Error<V>>>,
    T: ResponseEntity,
{
    match api_call.await {
        Ok(response) => {
            if response.status.is_client_error() || response.status.is_server_error() {
                return Err(Error::ResponseError(tower_api::apis::ResponseContent {
                    tower_trace_id: response.tower_trace_id,
                    status: response.status,
                    content: response.content,
                    entity: None,
                }));
            }

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
                let err = Error::ResponseError(tower_api::apis::ResponseContent {
                    tower_trace_id: "".to_string(),
                    status: StatusCode::NO_CONTENT,
                    content: "Empty response from server".to_string(),
                    entity: None,
                });
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
            Self::Status201(data) => Some(data),
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
            Self::UnknownValue(data) => match serde_json::from_value(data) {
                Ok(obj) => Some(obj),
                Err(err) => {
                    debug!("Failed to deserialize ListAppsResponse from value: {}", err);
                    None
                }
            },
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
            Self::Status201(resp) => Some(resp),
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

impl ResponseEntity for tower_api::apis::default_api::DescribeRunSuccess {
    type Data = tower_api::models::DescribeRunResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(resp) => Some(resp),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::ListEnvironmentsSuccess {
    type Data = tower_api::models::ListEnvironmentsResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(resp) => Some(resp),
            Self::UnknownValue(_) => None,
        }
    }
}

pub async fn list_environments(
    config: &Config,
) -> Result<
    tower_api::models::ListEnvironmentsResponse,
    Error<tower_api::apis::default_api::ListEnvironmentsError>,
> {
    let api_config = &config.into();
    unwrap_api_response(tower_api::apis::default_api::list_environments(api_config)).await
}

pub async fn create_environment(
    config: &Config,
    name: &str,
) -> Result<
    tower_api::models::CreateEnvironmentResponse,
    Error<tower_api::apis::default_api::CreateEnvironmentError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::CreateEnvironmentParams {
        create_environment_params: tower_api::models::CreateEnvironmentParams {
            schema: None,
            name: name.to_string(),
        },
    };

    unwrap_api_response(tower_api::apis::default_api::create_environment(
        api_config, params,
    ))
    .await
}

pub async fn list_schedules(
    config: &Config,
    _app_name: Option<&str>,
    environment: Option<&str>,
) -> Result<
    tower_api::models::ListSchedulesResponse,
    Error<tower_api::apis::default_api::ListSchedulesError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::ListSchedulesParams {
        environment: environment.map(String::from),
        page: None,
        page_size: None,
    };

    unwrap_api_response(tower_api::apis::default_api::list_schedules(
        api_config, params,
    ))
    .await
}

pub async fn create_schedule(
    config: &Config,
    app_name: &str,
    environment: &str,
    cron: &str,
    parameters: Option<HashMap<String, String>>,
) -> Result<
    tower_api::models::CreateScheduleResponse,
    Error<tower_api::apis::default_api::CreateScheduleError>,
> {
    let api_config = &config.into();

    let run_parameters = parameters.map(|params| {
        params
            .into_iter()
            .map(|(key, value)| RunParameter { name: key, value })
            .collect()
    });

    let params = tower_api::apis::default_api::CreateScheduleParams {
        create_schedule_params: tower_api::models::CreateScheduleParams {
            schema: None,
            app_name: app_name.to_string(),
            cron: cron.to_string(),
            environment: Some(environment.to_string()),
            app_version: None,
            parameters: run_parameters,
            status: None,
        },
    };

    unwrap_api_response(tower_api::apis::default_api::create_schedule(
        api_config, params,
    ))
    .await
}

pub async fn update_schedule(
    config: &Config,
    schedule_id: &str,
    cron: Option<&String>,
    parameters: Option<HashMap<String, String>>,
) -> Result<
    tower_api::models::UpdateScheduleResponse,
    Error<tower_api::apis::default_api::UpdateScheduleError>,
> {
    let api_config = &config.into();

    let run_parameters = parameters.map(|params| {
        params
            .into_iter()
            .map(|(key, value)| RunParameter { name: key, value })
            .collect()
    });

    let params = tower_api::apis::default_api::UpdateScheduleParams {
        id: schedule_id.to_string(),
        update_schedule_params: tower_api::models::UpdateScheduleParams {
            schema: None,
            cron: cron.map(|s| s.clone()),
            environment: None,
            app_version: None,
            parameters: run_parameters,
            status: None,
        },
    };

    unwrap_api_response(tower_api::apis::default_api::update_schedule(
        api_config, params,
    ))
    .await
}

pub async fn delete_schedule(
    config: &Config,
    schedule_id: &str,
) -> Result<
    tower_api::models::DeleteScheduleResponse,
    Error<tower_api::apis::default_api::DeleteScheduleError>,
> {
    let api_config = &config.into();

    let params = tower_api::apis::default_api::DeleteScheduleParams {
        delete_schedule_params: tower_api::models::DeleteScheduleParams {
            schema: None,
            ids: vec![schedule_id.to_string()],
        },
    };

    unwrap_api_response(tower_api::apis::default_api::delete_schedule(
        api_config, params,
    ))
    .await
}

impl ResponseEntity for tower_api::apis::default_api::ListSchedulesSuccess {
    type Data = tower_api::models::ListSchedulesResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::CreateEnvironmentSuccess {
    type Data = tower_api::models::CreateEnvironmentResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status201(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::CreateScheduleSuccess {
    type Data = tower_api::models::CreateScheduleResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status201(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::UpdateScheduleSuccess {
    type Data = tower_api::models::UpdateScheduleResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}

impl ResponseEntity for tower_api::apis::default_api::DeleteScheduleSuccess {
    type Data = tower_api::models::DeleteScheduleResponse;

    fn extract_data(self) -> Option<Self::Data> {
        match self {
            Self::Status200(data) => Some(data),
            Self::UnknownValue(_) => None,
        }
    }
}
