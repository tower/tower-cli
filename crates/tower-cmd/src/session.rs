use clap::Command;
use config::Config;
use tower_api::Client;
use promptly::prompt;
use crate::output;

pub fn login_cmd() -> Command {
    Command::new("login")
        .about("Create a session with Tower")
}

pub async fn do_login(_config: Config, client: Client) {
    output::banner();
    let email: String = prompt("Email").unwrap();
    let password: String = rpassword::prompt_password("Password: ").unwrap();
    let spinner = output::spinner("Logging in...");

    match client.login(&email, &password).await {
        Ok(session) => {
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
