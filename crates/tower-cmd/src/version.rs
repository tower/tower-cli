use clap::Command;
use crate::output;
use tower_api::apis::configuration::Configuration;
use config::Config;

pub fn version_cmd() -> Command {
    Command::new("version")
        .about("Print the current version of Tower")
}

pub async fn do_version(_config: Config, _configuration: &Configuration) {
    let line = format!("v{}\n", tower_version::current_version());
    output::write(&line);
}
