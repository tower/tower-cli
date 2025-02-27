use crate::output;
use clap::Command;
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
                if list_teams_response.teams.is_empty() {
                    let line =
                        format!("{}\n", "You don't belong to any teams yet!".bold().yellow());
                    output::write(&line);
                    return;
                }

                // Create headers for the table
                let headers = vec!["Slug", "Team Name"]
                    .into_iter()
                    .map(|h| h.yellow().to_string())
                    .collect();

                // Create data rows for the table
                let data: Vec<Vec<String>> = list_teams_response
                    .teams
                    .iter()
                    .map(|team| vec![team.slug.clone(), team.name.clone()])
                    .collect();

                // Display the table using the existing table function
                output::table(headers, data);
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
