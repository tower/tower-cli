use crate::{output, util::spinner::with_spinner};
use clap::{value_parser, Arg, ArgMatches, Command};
use colored::*;
use config::Config;
use tower_api::apis::default_api;

pub fn teams_cmd() -> Command {
    Command::new("teams")
        .about("View information about team membership and switch between teams")
        .arg_required_else_help(true)
        .subcommand(Command::new("list").about("List teams you belong to"))
        .subcommand(
            Command::new("switch")
                .about("Switch context to a different team")
                .arg(
                    Arg::new("team_slug")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set),
                ),
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

    // Then refresh it with the API
    let api_config = config.clone().into();

    // Create the required refresh_session_params
    let refresh_params = default_api::RefreshSessionParams {
        refresh_session_params: tower_api::models::RefreshSessionParams::new(),
    };

    let response = with_spinner(
        "Refreshing session...",
        default_api::refresh_session(&api_config, refresh_params),
        None,
    )
    .await;

    if let Some(default_api::RefreshSessionSuccess::Status200(session_response)) = response.entity {
        // Create a mutable copy of the session to update
        let mut session = current_session;

        // Update it with the API response
        if let Err(e) = session.update_from_api_response(&session_response) {
            output::config_error(e);
            std::process::exit(1);
        }

        session
    } else {
        output::die("Unexpected response format from server.");
    }
}

pub async fn do_list_teams(config: Config) {
    // Refresh the session and get the updated data
    let session = refresh_session(&config).await;

    // Get the current active team from the session
    let active_team = session.active_team.clone();
    let active_team_slug = active_team.map(|team| team.slug.clone());

    // Create headers for the table
    let headers = vec!["", "Slug", "Team Name"]
        .into_iter()
        .map(|h| h.yellow().to_string())
        .collect();

    // Format the teams data for the table
    let teams = session.teams.clone();
    let teams_data: Vec<Vec<String>> = teams
        .iter()
        .map(|team| {
            // Create the active indicator in its own column
            let active_indicator = if Some(&team.slug) == active_team_slug.as_ref() {
                "*".to_string()
            } else {
                "".to_string()
            };

            // Use the plain slug without asterisk
            let slug_display = team.slug.clone();

            // Check if team name is blank and use user's name instead
            let display_name = if team.name.trim().is_empty() {
                // Get the user's first and last name from the session
                let user = &session.user;
                let first_name = user.first_name.trim();
                let last_name = user.last_name.trim();

                if !first_name.is_empty() || !last_name.is_empty() {
                    // Use first and last name if available
                    format!("{} {}", first_name, last_name).trim().to_string()
                } else {
                    // Fall back to "Personal Workspace" if both names are empty
                    "Personal Workspace".to_string()
                }
            } else {
                team.name.clone()
            };

            vec![active_indicator, slug_display, display_name]
        })
        .collect();

    output::newline();
    // Display the table using the existing table function
    output::table(headers, teams_data);
    output::newline();

    // Add a legend for the asterisk
    println!("{}", "* indicates currently active team".dimmed());
    output::newline();
}

pub async fn do_switch_team(config: Config, args: &ArgMatches) {
    let team_slug = args
        .get_one::<String>("team_slug")
        .map(|s| s.as_str())
        .unwrap_or_else(|| {
            output::die("Team Slug (e.g. tower teams switch <team_slug>) is required");
        });

    // Refresh the session first to ensure we have the latest teams data
    let session = refresh_session(&config).await;

    // Check if the provided team slug exists in the refreshed session
    let team = session.teams.iter().find(|team| team.slug == team_slug);

    match team {
        Some(team) => {
            // Team found, set it as active
            match config.set_active_team_by_slug(team_slug) {
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
            output::failure(&format!(
                "Team '{}' not found. Use 'tower teams list' to see available teams.",
                team_slug
            ));
            std::process::exit(1);
        }
    }
}
