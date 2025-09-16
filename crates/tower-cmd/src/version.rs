use crate::output;
use clap::Command;

pub fn version_cmd() -> Command {
    Command::new("version").about("Print the current version of Tower")
}

pub async fn do_version() {
    let line = format!("v{}\n", tower_version::current_version());
    output::write(&line);
}
