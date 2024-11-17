use clap::Command;
use config::Config;
use tower_api::Client;
use promptly::prompt;
use crate::output;

pub fn login_cmd() -> Command {
    Command::new("login")
        .about("Create a session with Tower")
}

pub async fn do_login(config: Config, client: Client) {
    // reset the client so that we don't use previous session information--including the
    // last-authenticated tower_url!
    let client = client.with_tower_url(config.tower_url.clone())
        .anonymous();

    output::banner();
    let email: String = prompt("Email").unwrap();
    let password: String = rpassword::prompt_password("Password: ").unwrap();
    let spinner = output::spinner("Logging in...");

    match client.login(&email, &password).await {
        Ok(mut session) => {
            session.tower_url = config.tower_url.clone();
            spinner.success();

            if let Err(err) = session.save() {
                output::config_error(err);
            } else {
                let line = format!("Hello, {}!", session.user.email);
                output::success(&line);
            }
        },
        Err(err) => {
            spinner.failure();

            output::tower_error(err);
        }
    }
}
