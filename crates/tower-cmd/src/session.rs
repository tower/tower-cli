use clap::Command;
use config::Config;
use tower_api::apis::{
    configuration::Configuration,
    default_api::{
        self,
        CreateDeviceLoginSuccess,
        DescribeDeviceLoginClaimParams,
        DescribeDeviceLoginClaimSuccess,
    }
};
use crate::output;
use tokio::{time, time::Duration};

pub fn login_cmd() -> Command {
    Command::new("login")
        .about("Create a session with Tower")
}

pub async fn do_login(config: Config, configuration: Configuration) {
    // Create anonymous configuration (no bearer token)
    let configuration = Configuration {
        base_path: config.tower_url.to_string(),
        ..configuration
    };

    output::banner();

    let mut spinner = output::spinner("Starting device login...");

    // Request device login code
    match default_api::create_device_login(&configuration).await {
        Ok(response) => {
            spinner.success();
            if let CreateDeviceLoginSuccess::Status200(_login) = response.entity.unwrap() {
                // Now create the claim with the user_code from the login response
                match default_api::create_device_login(
                    &configuration
                ).await {
                    Ok(claim_response) => {
                        if let CreateDeviceLoginSuccess::Status200(claim) = claim_response.entity.unwrap() {
                            handle_device_login(&config, &configuration, claim).await;
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
    claim: tower_api::models::CreateDeviceLoginResponse,
) {
    // Try to open the login URL in browser
    if let Err(_) = open::that(&claim.verification_url) {
        let line = format!("Please open the following URL in your browser: {}", claim.verification_url);
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
    claim: &tower_api::models::CreateDeviceLoginResponse,
    spinner: &mut output::Spinner,
) -> bool {
    let interval_duration = Duration::from_secs(claim.interval as u64);
    let mut ticker = time::interval(interval_duration);

    let expires_in = chrono::Duration::seconds(claim.expires_in as i64);
    let expires_at = chrono::Utc::now() + expires_in;

    while chrono::Utc::now() < expires_at {
        match default_api::describe_device_login_claim(
            configuration,
            DescribeDeviceLoginClaimParams {
                device_code: claim.device_code.clone()
            }
        ).await {
            Ok(response) => {
                if let DescribeDeviceLoginClaimSuccess::Status200(session_response) = response.entity.unwrap() {
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
    session_response: &tower_api::models::DescribeDeviceLoginClaimResponse,
    _configuration: &Configuration,
    spinner: &mut output::Spinner,
) {
    // Create and save the session
    let session = config::Session::new(
        config::User {
            email: session_response.user.email.clone(),
            created_at: session_response.user.created_at.clone(),
        },
        config::Token {
            jwt: session_response.token.clone(),
        }
    );

    if let Err(err) = session.save() {
        spinner.failure();
        output::failure(&format!("Failed to save session: {}", err));
    } else {
        spinner.success();
        let message = format!("Hello, {}!", session_response.user.email);
        output::success(&message);
    }
}
