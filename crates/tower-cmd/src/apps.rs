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
            let headers = vec!["Name".to_string(), "Description".to_string()];
            let data = apps.iter().map(|sum| {
                vec![sum.app.name.clone(), sum.app.short_description.clone()]
            }).collect();

            output::table(headers, data);
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
