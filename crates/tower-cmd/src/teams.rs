use clap::{ArgMatches, Command};
use colored::*;
use config::Config;
use tower_telemetry::debug;

use crate::{
    output,
    api,
};

pub fn teams_cmd() -> Command {
    Command::new("teams")
        .about("View information about team membership and switch between teams")
        .arg_required_else_help(true)
        .subcommand(Command::new("list").about("List teams you belong to"))
        .subcommand(
            Command::new("switch")
                .allow_external_subcommands(true)
                .about("Switch context to a different team")
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
        },
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

pub async fn do_switch(config: Config, args: &ArgMatches) {
    let slug = extract_team_slug("switch", args.subcommand());

    // Refresh the session first to ensure we have the latest teams data
    let session = refresh_session(&config).await;

    // Check if the provided team slug exists in the refreshed session
    let team = session.teams.iter().find(|team| team.slug == slug);

    match team {
        Some(team) => {
            // Team found, set it as active
            match config.set_active_team_by_slug(&slug) {
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
                "Team '{}' not found. Use 'tower teams list' to see all your teams.",
                slug
            ));
            std::process::exit(1);
        }
    }
}

fn extract_team_slug(subcmd: &str, cmd: Option<(&str, &ArgMatches)>) -> String {
    if let Some((slug, _)) = cmd {
        return slug.to_string();
    }

    let line = format!("Team slug is required. Example: tower teams {} <team name>", subcmd);
    output::die(&line);
}
