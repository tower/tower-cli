use colored::Colorize;
use clap::Command;
use config::Config;
use tower_api::Client;

use crate::output;

pub fn apps_cmd() -> Command {
    Command::new("apps")
        .about("Interact with the apps that you own")
        .arg_required_else_help(true)
        .subcommand(
            Command::new("list")
                .about("List all of your apps`")
        )
        .subcommand(
            Command::new("create")
                .about("Create a new app")
        )
        .subcommand(
            Command::new("delete")
                .about("Delete an app")
        )
}

pub async fn do_list_apps(_config: Config, client: Client) {
    let res = client.list_apps().await;

    match res {
        Ok(apps) => {
            let items = apps.iter().map(|sum| {
                let desc = sum.app.short_description.clone();
                let desc = if desc.is_empty() {
                    "No description".to_string().white().italic()
                } else { 
                    desc.normal().clear()
                };

                format!("{}\n{}", sum.app.name.bold().green(), desc)
            }).collect();

            output::list(items);
        },
        Err(err) => {
            output::tower_error(err);
        }
    }
}

pub async fn do_create_app(_config: Config, _client: Client) {
    todo!()
}

pub async fn do_delete_app(_config: Config, _client: Client) {
    todo!()
}
