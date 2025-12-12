use crate::output::write;
use crate::api;
use clap::Command;
use colored::Colorize;
use config::Config;

pub fn doctor_cmd() -> Command {
    Command::new("doctor")
        .about("Check your Tower CLI installation and configuration")
}

pub async fn do_doctor(config: Config) {
    write(&format!("{}\n\n", "Running Tower doctor...".bold()));

    let mut all_ok = true;

    all_ok &= check_uv().await;
    all_ok &= check_authentication(&config).await;
    all_ok &= check_cli_version().await;

    write("\n");
    if all_ok {
        write(&format!("{}\n", "All checks passed!".green().bold()));
    } else {
        write(&format!("{}\n", "Some checks failed. See above for details.".yellow().bold()));
    }
}

async fn check_uv() -> bool {
    write("Checking UV... ");

    match tower_uv::Uv::new(None, false).await {
        Ok(uv) => {
            let version_output = tokio::process::Command::new(&uv.uv_path)
                .arg("--version")
                .output()
                .await;

            match version_output {
                Ok(cmd_output) => {
                    let version = String::from_utf8_lossy(&cmd_output.stdout).trim().to_string();
                    write(&format!("{}\n", "OK".green()));
                    write(&format!("  Path: {}\n", uv.uv_path.display()));
                    write(&format!("  Version: {}\n", version));
                    true
                }
                Err(e) => {
                    write(&format!("{}\n", "FAILED".red()));
                    write(&format!("  Path: {}\n", uv.uv_path.display()));
                    write(&format!("  Error getting version: {}\n", e));
                    false
                }
            }
        }
        Err(e) => {
            write(&format!("{}\n", "FAILED".red()));
            write(&format!("  Error: {:?}\n", e));
            false
        }
    }
}

async fn check_authentication(config: &Config) -> bool {
    write("Checking authentication... ");

    match config::Session::from_config_dir() {
        Ok(session) => {
            let config_with_session = config.clone().with_session(session.clone());

            match api::refresh_session(&config_with_session).await {
                Ok(_) => {
                    write(&format!("{}\n", "OK".green()));
                    write(&format!("  Logged in as: {}\n", session.user.email));
                    if let Some(team) = session.active_team {
                        write(&format!("  Active team: {}\n", team.name));
                    }
                    true
                }
                Err(_) => {
                    write(&format!("{}\n", "EXPIRED".red()));
                    write(&format!("  Session for {} has expired.\n", session.user.email));
                    write("  Run 'tower login' to re-authenticate.\n");
                    false
                }
            }
        }
        Err(_) => {
            write(&format!("{}\n", "NOT LOGGED IN".yellow()));
            write("  Run 'tower login' to authenticate.\n");
            true
        }
    }
}

async fn check_cli_version() -> bool {
    write("Checking CLI version... ");

    let current = tower_version::current_version();

    match tower_version::check_latest_version().await {
        Ok(Some(latest)) => {
            if current == latest {
                write(&format!("{}\n", "OK".green()));
                write(&format!("  Current: {} (latest)\n", current));
            } else {
                write(&format!("{}\n", "UPDATE AVAILABLE".yellow()));
                write(&format!("  Current: {}\n", current));
                write(&format!("  Latest:  {}\n", latest));
            }
            true
        }
        Ok(None) => {
            write(&format!("{}\n", "OK".green()));
            write(&format!("  Current: {}\n", current));
            write("  Could not check for updates.\n");
            true
        }
        Err(_) => {
            write(&format!("{}\n", "OK".green()));
            write(&format!("  Current: {}\n", current));
            write("  Could not check for updates (offline?).\n");
            true
        }
    }
}
