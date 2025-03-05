use crate::output;
use clap::Command;
use config::Config;
use tokio::{time, time::Duration};
use tower_api::{
    apis::default_api::{
        self as api, CreateDeviceLoginTicketSuccess, DescribeDeviceLoginSessionParams,
        DescribeDeviceLoginSessionSuccess,
    },
    models::CreateDeviceLoginTicketResponse,
};

pub fn login_cmd() -> Command {
    Command::new("login").about("Create a session with Tower")
}

pub async fn do_login(config: Config) {
    output::banner();

    let mut spinner = output::spinner("Starting device login...");
    let api_config = config.clone().into();

    // Request device login code
    match api::create_device_login_ticket(&api_config).await {
        Ok(response) => {
            let response = response.entity.unwrap();

            if let CreateDeviceLoginTicketSuccess::Status200(login_claim) = response {
                spinner.success();
                handle_device_login(config, login_claim).await;
            } else {
                spinner.failure();
                output::failure("The Tower API returned an unexpected response.");
            }
        }
        Err(err) => {
            spinner.failure();
            if let tower_api::apis::Error::ResponseError(err) = err {
                output::failure(&format!("{}: {}", err.status, err.content));
            } else {
                output::failure(&format!("Unexpected error: {}", err));
            }
        }
    }
}

async fn handle_device_login(
    config: Config,
    claim: tower_api::models::CreateDeviceLoginTicketResponse,
) {
    // Try to open the login URL in browser
    if let Err(_) = open::that(&claim.login_url) {
        let line = format!(
            "Please open the following URL in your browser: {}",
            claim.login_url
        );
        output::write(&line);
    }

    let mut spinner = output::spinner("Waiting for login...");

    if !poll_for_login(&config, &claim, &mut spinner).await {
        spinner.failure();
        output::failure("Login request expired. Please try again.");
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
        let resp = api::describe_device_login_session(
            &config.into(),
            DescribeDeviceLoginSessionParams {
                device_code: claim.device_code.clone(),
            },
        )
        .await;

        match resp {
            Ok(resp) => {
                if let Some(success) = resp.entity {
                    if let DescribeDeviceLoginSessionSuccess::Status200(response) = success {
                        finalize_session(config, &response, spinner);
                        return true;
                    }
                }

                spinner.failure();
                output::failure("The Tower API returned an unexpected response.");
                return false;
            }
            Err(err) => {
                if let Some(api_err) = extract_api_error(&err) {
                    if api_err.status != 404 && !api_err.is_incomplete_device_login {
                        output::failure(&format!("{}", api_err.content));
                        return false;
                    }
                } else {
                    output::failure(&format!("An unexpected error happened! Error: {}", err));
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
    let teams = session_response
        .session
        .teams
        .iter()
        .map(|t| config::Team {
            slug: t.slug.clone(),
            name: t.name.clone(),
            team_type: t.r#type.clone(),
            token: config::Token {
                jwt: t.token.clone().unwrap().jwt.clone(),
            },
        })
        .collect();

    // Create and save the session
    let mut session = config::Session::new(
        config::User {
            email: session_response.session.user.email.clone(),
            created_at: session_response.session.user.created_at.clone(),
            first_name: session_response.session.user.first_name.clone(),
            last_name: session_response.session.user.last_name.clone(),
        },
        config::Token {
            jwt: session_response.session.token.jwt.clone(),
        },
        teams,
    );

    // we have to copy in the tower URL so that we save it for later on!
    session.tower_url = config.tower_url.clone();

    // Set the active team to the one matching the main session JWT
    let _ = session.set_active_team_by_jwt(&session_response.session.token.jwt);

    if let Err(err) = session.save() {
        spinner.failure();
        output::failure(&format!("Failed to save session: {}", err));
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
