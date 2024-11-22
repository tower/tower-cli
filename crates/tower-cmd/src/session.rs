use clap::Command;
use config::Config;
use tower_api::{Client, DeviceLoginTicket, Session};
use crate::output;
use tokio::{time, time::Duration};

pub fn login_cmd() -> Command {
    Command::new("login")
        .about("Create a session with Tower")
}

pub async fn do_login(config: Config, client: Client) {
    let client = client.with_tower_url(config.tower_url.clone())
        .anonymous();
    output::banner();

    match client.device_login().await {
        Ok(ticket) => handle_device_login(&config, client, ticket).await,
        Err(err) => output::tower_error(err),
    }
}

/// Handles the device login process, including polling for user authentication.
async fn handle_device_login(config: &Config, client: Client, ticket: DeviceLoginTicket) {
    // first open the link in the browser. if we can't do that, we'll just print the link for
    // people.
    if let Err(_) = open::that(&ticket.login_url) {
        let line = format!("Please open the following URL in your browser: {}", ticket.login_url);
        output::write(&line);
    }

    let mut spinner = output::spinner("Waiting for login...");

    if !poll_for_login(&client, &ticket, config, &mut spinner).await {
        spinner.failure();
        output::failure("Login request expired. Please try again.");
    }
}

/// Polls for login completion, returns `true` if login is successful, `false` otherwise.
async fn poll_for_login(
    client: &Client,
    ticket: &DeviceLoginTicket,
    config: &Config,
    spinner: &mut output::Spinner,
) -> bool {
    let interval_duration = Duration::from_secs(ticket.interval as u64);
    let mut ticker = time::interval(interval_duration);

    let expires_in = chrono::Duration::seconds(ticket.expires_in as i64);
    let expires_at = ticket.generated_at + expires_in;

    while chrono::Utc::now() < expires_at {
        match client.check_device_login(&ticket.device_code).await {
            Ok(mut session) => {
                finalize_session(&mut session, config, spinner);
                return true;
            }
            Err(err) => {
                if err.code != "tower_sessions_incomplete_device_login_error" {
                    output::tower_error(err);
                    return false;
                }
                // If the error is incomplete login, continue polling.
            }
        }
        ticker.tick().await;
    }
    false
}

/// Finalizes the user session, saving it and providing user feedback.
fn finalize_session(session: &mut Session, config: &Config, spinner: &mut output::Spinner) {
    session.tower_url = config.tower_url.clone();

    if let Err(err) = session.save() {
        spinner.failure();
        output::config_error(err);
    } else {
        spinner.success();
        let message = format!("Hello, {}!", session.user.email);
        output::success(&message);
    }
}
