use clap::{ArgMatches, Command};
use colored::*;
use config::Config;
use tower_telemetry::debug;

use crate::{api, output};

pub fn teams_cmd() -> Command {
    Command::new("teams")
        .about("View information about team membership and switch between teams")
        .arg_required_else_help(true)
        .subcommand(Command::new("list").about("List teams you belong to"))
        .subcommand(
            Command::new("switch")
                .allow_external_subcommands(true)
                .about("Switch context to a different team"),
        )
}

/// Refreshes the session with the Tower API and returns the updated session
async fn refresh_session(config: &Config) -> config::Session {
    // First get the current session
    let current_session = match config.get_current_session() {
        Ok(session) => session,
        Err(e) => {
            output::config_error(e);
            std::process::exit(1);
        }
    };

    let mut spinner = output::spinner("Refreshing session...");

    match api::refresh_session(&config).await {
        Ok(resp) => {
            spinner.success();

            // Create a mutable copy of the session to update
            let mut session = current_session;

            // Update it with the API response
            if let Err(e) = session.update_from_api_response(&resp) {
                output::config_error(e);
                std::process::exit(1);
            }

            session
        }
        Err(err) => {
            debug!("Failed to refresh session: {}", err);

            spinner.failure();
            output::die("There was a problem talking to the Tower API. Try again later!");
        }
    }
}

pub async fn do_list(config: Config) {
    // Refresh the session and get the updated data
    let session = refresh_session(&config).await;

    // Get the current active team from the session
    let active_team = session.active_team.clone();
    let active_team_name = active_team.map(|team| team.name.clone());

    // Create headers for the table
    let headers = vec!["", "Name"]
        .into_iter()
        .map(|h| h.yellow().to_string())
        .collect();

    // Format the teams data for the table
    let teams = session.teams.clone();
    let teams_data: Vec<Vec<String>> = teams
        .iter()
        .map(|team| {
            // Create the active indicator in its own column
            let active_indicator = if Some(&team.name) == active_team_name.as_ref() {
                "*".to_string()
            } else {
                "".to_string()
            };

            vec![active_indicator, team.name.clone()]
        })
        .collect();

    output::newline();
    // Display the table using the existing table function
    output::table(headers, teams_data, Some(&teams));
    output::newline();

    // Add a legend for the asterisk
    println!("{}", "* indicates currently active team".dimmed());
    output::newline();
}

pub async fn do_switch(config: Config, args: &ArgMatches) {
    let name = extract_team_name("switch", args.subcommand());

    // Refresh the session first to ensure we have the latest teams data
    let session = refresh_session(&config).await;

    // Check if the provided team name exists in the refreshed session
    let team = session.teams.iter().find(|team| team.name == name);

    match team {
        Some(team) => {
            // Team found, set it as active
            match config.set_active_team_by_name(&name) {
                Ok(_) => {
                    output::success(&format!("Switched to team: {}", team.name));
                }
                Err(e) => {
                    output::config_error(e);
                    std::process::exit(1);
                }
            }
        }
        None => {
            // Team not found
            output::error(&format!(
                "Team '{}' not found. Use 'tower teams list' to see all your teams.",
                name,
            ));
            std::process::exit(1);
        }
    }
}

fn extract_team_name(subcmd: &str, cmd: Option<(&str, &ArgMatches)>) -> String {
    if let Some((name, _)) = cmd {
        return name.to_string();
    }

    let line = format!(
        "Team name is required. Example: tower teams {} <team name>",
        subcmd
    );
    output::die(&line);
}
