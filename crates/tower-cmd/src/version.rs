use crate::output::Out;
use clap::Command;

pub fn version_cmd() -> Command {
    Command::new("version").about("Print the current version of Tower")
}

pub async fn do_version(out: &Out) {
    let version = tower_version::current_version();
    out.text(
        &format!("v{}\n", version),
        &serde_json::json!({ "version": version }),
    );
}
