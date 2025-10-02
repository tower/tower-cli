use crate::output;
use clap::Command;
use config::{Config, Session};
use tokio::{time, time::Duration};
use tower_api::models::CreateDeviceLoginTicketResponse;
use tower_telemetry::debug;

use crate::api;

pub fn login_cmd() -> Command {
    Command::new("login").about("Create a session with Tower")
}

pub async fn do_login(config: Config) {
    output::banner();

    let mut spinner = output::spinner("Starting device login...");

    match api::create_device_login_ticket(&config).await {
        Ok(resp) => {
            spinner.success();
            handle_device_login(config, resp).await;
        }
        Err(err) => {
            spinner.failure();
            output::error(&format!("Failed to create device login ticket: {}", err));
        }
    }
}

async fn handle_device_login(config: Config, claim: CreateDeviceLoginTicketResponse) {
    // Try to open the login URL in browser
    if let Err(err) = webbrowser::open(&claim.login_url) {
        debug!("failed to open web browser: {}", err);

        let line = format!(
            "Please open the following URL in your browser: {}\n",
            claim.login_url
        );
        output::write(&line);
    } else {
        debug!("opened browser to {}", claim.login_url);
    }

    let mut spinner = output::spinner("Waiting for login...");

    if !poll_for_login(&config, &claim, &mut spinner).await {
        spinner.failure();
        output::error("Login request expired. Please try again.");
    }
}

async fn poll_for_login(
    config: &Config,
    claim: &CreateDeviceLoginTicketResponse,
    spinner: &mut output::Spinner,
) -> bool {
    let interval_duration = Duration::from_secs(claim.interval as u64);
    let mut ticker = time::interval(interval_duration);

    let expires_in = chrono::Duration::seconds(claim.expires_in as i64);
    let expires_at = chrono::Utc::now() + expires_in;

    while chrono::Utc::now() < expires_at {
        match api::describe_device_login_session(&config, &claim.device_code).await {
            Ok(resp) => {
                finalize_session(config, &resp, spinner);
                return true;
            }
            Err(err) => {
                if let Some(api_err) = extract_api_error(&err) {
                    if api_err.status != 404 && !api_err.is_incomplete_device_login {
                        output::error(&format!("{}", api_err.content));
                        return false;
                    }
                } else {
                    output::error(&format!("An unexpected error happened! Error: {}", err));
                    return false;
                }
            }
        }

        // Keep waiting...
        ticker.tick().await;
    }
    false
}

fn finalize_session(
    config: &Config,
    session_response: &tower_api::models::DescribeDeviceLoginSessionResponse,
    spinner: &mut output::Spinner,
) {
    let mut session = Session::from_api_session(&session_response.session);

    // we have to copy in the tower URL so that we save it for later on!
    session.tower_url = config.tower_url.clone();

    if let Err(err) = session.save() {
        spinner.failure();
        output::error(&format!("Failed to save session: {}", err));
    } else {
        spinner.success();
        let message = format!("Hello, {}!", session_response.session.user.email.clone());
        output::success(&message);
    }
}

fn extract_api_error<T>(err: &tower_api::apis::Error<T>) -> Option<ApiErrorDetails> {
    if let tower_api::apis::Error::ResponseError(err) = err {
        if let Ok(error_model) = serde_json::from_str::<tower_api::models::ErrorModel>(&err.content)
        {
            let is_incomplete_device_login = error_model
                .errors
                .as_ref()
                .and_then(|errors| errors.first())
                .and_then(|error| error.location.as_ref())
                .map(|message| message.contains("incomplete_device_login"))
                .unwrap_or(false);

            return Some(ApiErrorDetails {
                status: u16::from(err.status),
                content: err.content.clone(),
                is_incomplete_device_login,
            });
        }
    }
    None
}

// Struct to store extracted error details
struct ApiErrorDetails {
    status: u16,
    content: String,
    is_incomplete_device_login: bool,
}
