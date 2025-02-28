use crate::output;
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

pub async fn do_list_teams(config: Config) {
    let api_config = config.get_api_configuration().unwrap();

    // First refresh the session to ensure we have the latest data
    let mut spinner = output::Spinner::new("Refreshing session...".to_string());

    match default_api::refresh_session(api_config).await {
        Ok(response) => {
            if let Some(default_api::RefreshSessionSuccess::Status200(_session_response)) =
                response.entity
            {
                spinner.success();

                // Get the current active team from the session
                let active_team = config.get_active_team().unwrap_or(None);
                let active_team_slug = active_team.map(|team| team.slug.clone());

                // Create headers for the table
                let headers = vec!["Slug", "Team Name"]
                    .into_iter()
                    .map(|h| h.yellow().to_string())
                    .collect();

                // Format the teams data for the table
                let teams = config.get_teams().unwrap_or_default();
                let teams_data: Vec<Vec<String>> = teams
                    .iter()
                    .map(|team| {
                        let slug_display = if Some(&team.slug) == active_team_slug.as_ref() {
                            format!("* {}", team.slug)
                        } else {
                            team.slug.clone()
                        };
                        vec![slug_display, team.name.clone()]
                    })
                    .collect();

                output::newline();
                // Display the table using the existing table function
                output::table(headers, teams_data);
                output::newline();

                // Add a legend for the asterisk
                println!("{}", "* indicates currently active team".dimmed());
                output::newline();
            } else {
                spinner.failure();
                eprintln!("{}", "Unexpected response format from server.".red());
                std::process::exit(1);
            }
        }
        Err(e) => {
            spinner.failure();
            eprintln!("{}", format!("Failed to refresh session: {}", e).red());
            std::process::exit(1);
        }
    }
}

pub async fn do_switch_team(config: Config, args: &ArgMatches) {
    let team_slug = args
        .get_one::<String>("team_slug")
        .map(|s| s.as_str())
        .unwrap_or_else(|| {
            output::die("Team Slug (e.g. tower teams switch <team_slug>) is required");
        });

    // Get all available teams
    let teams = match config.get_teams() {
        Ok(teams) => teams,
        Err(e) => {
            output::failure(&format!("Failed to get teams: {}", e));
            std::process::exit(1);
        }
    };

    // Check if the provided team slug exists
    let team = teams.iter().find(|team| team.slug == team_slug);

    match team {
        Some(team) => {
            // Team found, set it as active
            match config.set_active_team_by_slug(team_slug) {
                Ok(_) => {
                    output::success(&format!("Switched to team: {}", team.name));
                }
                Err(e) => {
                    output::failure(&format!("Failed to switch team: {}", e));
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
