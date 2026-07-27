use clap::{value_parser, Arg, ArgMatches, Command};
use colored::*;
use config::Config;

use crate::api;

pub fn teams_cmd() -> Command {
    Command::new("teams")
        .about("View information about team membership and switch between teams")
        .arg_required_else_help(true)
        .subcommand(Command::new("list").about("List teams you belong to"))
        .subcommand(
            Command::new("switch")
                .arg(
                    Arg::new("team_name")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("Name of the team to switch to"),
                )
                .about("Switch context to a different team"),
        )
}

/// Refreshes the session with the Tower API and returns the updated session
async fn refresh_session(out: &crate::output::Out, config: &Config) -> config::Session {
    // First get the current session
    let current_session = match config.get_current_session() {
        Ok(session) => session,
        Err(e) => {
            out.config_error(e);
            std::process::exit(1);
        }
    };

    let resp = out
        .with_spinner("Refreshing session", api::refresh_session(&config))
        .await;

    // Create a mutable copy of the session to update
    let mut session = current_session;

    // Update it with the API response
    if let Err(e) = session.update_from_api_response(&resp) {
        out.config_error(e);
        std::process::exit(1);
    }

    session
}

pub async fn do_list(out: &crate::output::Out, config: Config) {
    if config.api_key.is_some() {
        do_list_via_api(out, &config).await;
    } else {
        do_list_via_session(out, &config).await;
    }
}

async fn do_list_via_api(out: &crate::output::Out, config: &Config) {
    let teams = out
        .with_spinner("Fetching teams", api::list_teams(config))
        .await;

    let headers = vec!["Name".to_string()];

    let teams_data: Vec<Vec<String>> = teams.iter().map(|team| vec![team.name.clone()]).collect();

    out.newline();
    out.table(headers, teams_data, None::<&Vec<config::Team>>);
    out.newline();
}

async fn do_list_via_session(out: &crate::output::Out, config: &Config) {
    // Refresh the session and get the updated data
    let session = refresh_session(out, config).await;

    // Get the current active team from the session
    let active_team = session.active_team.clone();
    let active_team_name = active_team.map(|team| team.name.clone());

    // Create headers for the table
    let headers = vec!["".to_string(), "Name".to_string()];

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

    out.newline();
    // Display the table using the existing table function
    out.table(headers, teams_data, Some(&teams));
    out.newline();

    // Add a legend for the asterisk
    out.note(&format!(
        "{}\n",
        "* indicates currently active team".dimmed()
    ));
    out.newline();
}

pub async fn do_switch(out: &crate::output::Out, config: Config, args: &ArgMatches) {
    let name = args
        .get_one::<String>("team_name")
        .expect("team_name is required");

    // Refresh the session first to ensure we have the latest teams data
    let session = refresh_session(out, &config).await;

    // Check if the provided team name exists in the refreshed session
    let team = session.teams.iter().find(|team| team.name == *name);

    match team {
        Some(team) => {
            // Team found, set it as active
            match config.set_active_team_by_name(name) {
                Ok(_) => {
                    out.success(&format!("Switched to team: {}", team.name));
                }
                Err(e) => {
                    out.config_error(e);
                    std::process::exit(1);
                }
            }
        }
        None => {
            // Team not found
            out.error(&format!(
                "Team '{}' not found. Use 'tower teams list' to see all your teams.",
                name,
            ));
            std::process::exit(1);
        }
    }
}
