use clap::Command;
use config::Config;
use tower_api::apis::{
    configuration::Configuration,
    default_api::{
        self,
        CreateDeviceLoginTicketSuccess,
        ClaimDeviceLoginTicketSuccess,
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

pub async fn do_login(config: Config, configuration: &Configuration) {
    // Create anonymous configuration (no bearer token)
    let api_config = Configuration {
        base_path: config.tower_url.to_string(),
        ..configuration.clone()
    };

    output::banner();

    let mut spinner = output::spinner("Starting device login...");

    // Request device login code
    match default_api::create_device_login_ticket(&api_config).await {
        Ok(response) => {
            spinner.success();
            if let CreateDeviceLoginTicketSuccess::Status200(login_claim) = response.entity.unwrap() {
                // Now claim the ticket with the user_code from the login response
                match default_api::claim_device_login_ticket(
                    &api_config,
                    default_api::ClaimDeviceLoginTicketParams {
                        claim_device_login_ticket_params: tower_api::models::ClaimDeviceLoginTicketParams {
                            schema: None,
                            user_code: login_claim.user_code.clone(),
                        }
                    }
                ).await {
                    Ok(claim_response) => {
                        if let ClaimDeviceLoginTicketSuccess::Status200(_claim) = claim_response.entity.unwrap() {
                            handle_device_login(&config, &api_config, login_claim).await;
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
    _config: &Config,
    configuration: &Configuration,
    claim: tower_api::models::CreateDeviceLoginTicketResponse,
) {
    // Try to open the login URL in browser
    if let Err(_) = open::that(&claim.login_url) {
        let line = format!("Please open the following URL in your browser: {}", claim.login_url);
        output::write(&line);
    }

    let mut spinner = output::spinner("Waiting for login...");

    if !poll_for_login(configuration, &claim, &mut spinner).await {
        spinner.failure();
        output::failure("Login request expired. Please try again.");
    }
}

async fn poll_for_login(
    configuration: &Configuration,
    claim: &tower_api::models::CreateDeviceLoginTicketResponse,
    spinner: &mut output::Spinner,
) -> bool {
    let interval_duration = Duration::from_secs(claim.interval as u64);
    let mut ticker = time::interval(interval_duration);

    let expires_in = chrono::Duration::seconds(claim.expires_in as i64);
    let expires_at = chrono::Utc::now() + expires_in;

    while chrono::Utc::now() < expires_at {
        match default_api::describe_device_login_session(
            configuration,
            DescribeDeviceLoginSessionParams {
                device_code: claim.device_code.clone()
            }
        ).await {
            Ok(response) => {
                if let DescribeDeviceLoginSessionSuccess::Status200(session_response) = response.entity.unwrap() {
                    finalize_session(&session_response, configuration, spinner);
                    return true;
                }
            },
            Err(err) => {
                if let tower_api::apis::Error::ResponseError(err) = err {
                    // Only continue polling if we get an incomplete login error
                    if !err.content.contains("incomplete_device_login") {
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
    _configuration: &Configuration,
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
