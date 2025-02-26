use clap::Command;
use config::Config;
use tower_api::apis::{
    configuration::Configuration,
    default_api::{
        self,
        CreateDeviceLoginTicketSuccess,
        DescribeDeviceLoginSessionParams,
        DescribeDeviceLoginSessionSuccess
    }
};
use crate::output;
use tokio::{time, time::Duration};

pub fn login_cmd() -> Command {
    Command::new("login")
        .about("Create a session with Tower")
}

pub async fn do_login(config: Config) {
    // Create anonymous configuration (no bearer token)
    let api_config = config.get_api_configuration().unwrap();

    output::banner();

    let mut spinner = output::spinner("Starting device login...");

    // Request device login code
    match default_api::create_device_login_ticket(&api_config).await {
        Ok(response) => {
            spinner.success();
            if let CreateDeviceLoginTicketSuccess::Status200(login_claim) = response.entity.unwrap() {
                handle_device_login(&api_config, login_claim).await;
            }
        },
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
    api_config: &Configuration,
    claim: tower_api::models::CreateDeviceLoginTicketResponse,
) {
    // Try to open the login URL in browser
    if let Err(_) = open::that(&claim.login_url) {
        let line = format!("Please open the following URL in your browser: {}", claim.login_url);
        output::write(&line);
    }

    let mut spinner = output::spinner("Waiting for login...");

    if !poll_for_login(api_config, &claim, &mut spinner).await {
        spinner.failure();
        output::failure("Login request expired. Please try again.");
    }
}

async fn poll_for_login(
    api_config: &Configuration,
    claim: &tower_api::models::CreateDeviceLoginTicketResponse,
    spinner: &mut output::Spinner,
) -> bool {
    let interval_duration = Duration::from_secs(claim.interval as u64);
    let mut ticker = time::interval(interval_duration);

    let expires_in = chrono::Duration::seconds(claim.expires_in as i64);
    let expires_at = chrono::Utc::now() + expires_in;

    while chrono::Utc::now() < expires_at {
        match default_api::describe_device_login_session(
            api_config,
            DescribeDeviceLoginSessionParams {
                device_code: claim.device_code.clone()
            }
        ).await {
            Ok(response) => {
                if let DescribeDeviceLoginSessionSuccess::Status200(session_response) = response.entity.unwrap() {
                    finalize_session(&session_response, spinner);
                    return true;
                }
            },
            Err(err) => {
                if let tower_api::apis::Error::ResponseError(err) = err {
                    // Try to parse the error content as an ErrorModel
                    if let Ok(error_model) = serde_json::from_str::<tower_api::models::ErrorModel>(&err.content) {
                        // Check if any error detail has "incomplete_device_login" in its location
                        // FIXME: Ugly, but I don't have a better option currently.
                        let is_incomplete_login = error_model.errors
                            .as_ref()
                            .and_then(|errors| errors.first())
                            .and_then(|error| error.location.as_ref())
                            .map(|message| message.contains("incomplete_device_login"))
                            .unwrap_or(false);

                        // Continue polling only if it's a 404 with incomplete_device_login as True
                        if err.status != 404 && !is_incomplete_login {
                            output::failure(&format!("{}: {}", err.status, err.content));
                            return false;
                        }
                    } else {
                        output::failure(&format!("{}: {}", err.status, err.content));
                        return false;
                    }
                } else {
                    output::failure(&format!("Unexpected error: {}", err));
                    return false;
                }
            }
        }
        ticker.tick().await;
    }
    false
}

fn finalize_session(
    session_response: &tower_api::models::DescribeDeviceLoginSessionResponse,
    spinner: &mut output::Spinner,
) {
    // Create and save the session
    let session = config::Session::new(
        config::User {
            email: session_response.session.user.email.clone(),
            created_at: session_response.session.user.created_at.clone(),
        },
        config::Token {
            jwt: session_response.session.token.jwt.clone(),
        }
    );

    if let Err(err) = session.save() {
        spinner.failure();
        output::failure(&format!("Failed to save session: {}", err));
    } else {
        spinner.success();
        let message = format!("Hello, {}!", session_response.session.user.email.clone());
        output::success(&message);
    }
}
