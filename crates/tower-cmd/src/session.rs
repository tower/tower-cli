use crate::output;
use clap::Command;
use config::Config;
use tokio::{time, time::Duration};
use tower_api::{
    models::{
        CreateDeviceLoginTicketResponse
    },
    apis::default_api::{
        self as api,
        CreateDeviceLoginTicketSuccess,
        DescribeDeviceLoginSessionSuccess, DescribeDeviceLoginSessionParams, 
    },
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
        ).await;

        match resp {
            Ok(resp) => {
                let success = resp.entity.unwrap();

                if let DescribeDeviceLoginSessionSuccess::Status200(response) = success {
                    finalize_session(config, &response, spinner);
                    return true;
                } else {
                    spinner.failure();
                    output::failure("The Tower API returned an unexpected response.");
                    return false;
                }
            }
            Err(err) => {
                if let tower_api::apis::Error::ResponseError(err) = err {
                    // Try to parse the error content as an ErrorModel
                    if let Ok(error_model) =
                        serde_json::from_str::<tower_api::models::ErrorModel>(&err.content)
                    {
                        // Check if any error detail has "incomplete_device_login" in its location
                        // FIXME: Ugly, but I don't have a better option currently.
                        let is_incomplete_login = error_model
                            .errors
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
                jwt: t
                    .token
                    .as_ref()
                    .map(|token| token.jwt.clone())
                    .unwrap_or_default(),
            },
        })
        .collect();

    // Create and save the session
    let mut session = config::Session::new(
        config::User {
            email: session_response.session.user.email.clone(),
            created_at: session_response.session.user.created_at.clone(),
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
        log::debug!("Session saved successfully (Tower URL: {}, User: {})", session.tower_url, session.user.email);
        spinner.success();
        let message = format!("Hello, {}!", session_response.session.user.email.clone());
        output::success(&message);
    }
}
