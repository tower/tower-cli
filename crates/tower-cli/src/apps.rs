use clap::Command;
use config::Config;
use tower_api::Client;

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

pub async fn do_list_apps(config: Config, client: Client) {
    let res = client.list_apps().await;
}

pub async fn do_create_app(config: Config, client: Client) {
    todo!()
}

pub async fn do_delete_app(config: Config, client: Client) {
    todo!()
}
