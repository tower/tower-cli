use crate::output;
use clap::{Arg, Command};
use colored::*;
use config::Config;
use tower_api::apis::default_api;

pub fn teams_cmd() -> Command {
    Command::new("teams")
        .about("View information about team membership and switch between teams")
        .subcommand_required(true)
        .arg_required_else_help(true)
        .subcommand(list_cmd())
}

fn list_cmd() -> Command {
    Command::new("list").about("List teams you belong to")
}

pub async fn do_list_teams(config: Config) {
    let api_config = config.get_api_configuration().unwrap();

    match default_api::list_teams(api_config).await {
        Ok(response) => {
            if let Some(default_api::ListTeamsSuccess::Status200(list_teams_response)) =
                response.entity
            {
                output::newline();

                // Create headers for the table
                let headers = vec!["Slug", "Team Name"]
                    .into_iter()
                    .map(|h| h.yellow().to_string())
                    .collect();

                // Get the current active team from the session
                let active_team = config.get_active_team().unwrap_or(None);
                let active_team_slug = active_team.map(|team| team.slug.clone());

                // Format the teams data for the table
                let teams_data: Vec<Vec<String>> = list_teams_response
                    .teams
                    .iter()
                    .map(|team| {
                        let team_name = if Some(&team.slug) == active_team_slug.as_ref() {
                            format!("{} *", team.name)
                        } else {
                            team.name.clone()
                        };
                        vec![team.slug.clone(), team_name]
                    })
                    .collect();

                // Display the table using the existing table function
                output::table(headers, teams_data);
                output::newline();

                // Add a legend for the asterisk
                println!("{}", "* indicates currently active team".dimmed());
                output::newline();
            } else {
                eprintln!("{}", "Unexpected response format from server.".red());
                std::process::exit(1);
            }
        }
        Err(e) => {
            eprintln!("{}", format!("Failed to list teams: {}", e).red());
            std::process::exit(1);
        }
    }
}
