use colored::Colorize;
use clap::{value_parser, Arg, ArgMatches, Command};
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
                .arg(
                    Arg::new("name")
                        .long("name")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set)
                )
                .arg(
                    Arg::new("description")
                        .long("description")
                        .value_parser(value_parser!(String))
                        .default_value("")
                        .action(clap::ArgAction::Set)
                )
                .about("Create a new app in Tower")
        )
        .subcommand(
            Command::new("delete")
                .allow_external_subcommands(true)
                .about("Delete an app in Tower")
        )
}

pub async fn do_list_apps(_config: Config, client: Client) {
    let res = client.list_apps().await;

    match res {
        Ok(apps) => {
            let items = apps.iter().map(|sum| {
                let desc = sum.app.short_description.clone();
                let desc = if desc.is_empty() {
                    "No description".white().dimmed().italic()
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

pub async fn do_create_app(_config: Config, client: Client, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("App name (--name) is required");
    });

    let description = args.get_one::<String>("description").unwrap();

    let spinner = output::spinner("Creating app");

    match client.create_app(&name, &description).await {
        Ok(_app) => {
            spinner.success();

            let line = format!("App \"{}\" was created", name);
            output::success(&line);
        },
        Err(err) => {
            spinner.failure();

            output::tower_error(err);
        }
    }
}

pub async fn do_delete_app(_config: Config, client: Client, cmd: Option<(&str, &ArgMatches)>) {
    let opts = cmd.unwrap_or_else(|| {
        output::die("App name (e.g. tower apps delete <name>) is required");
    });

    let spinner = output::spinner("Deleting app...");

    match client.delete_app(&opts.0).await {
        Ok(_app) => {
            spinner.success();

            let line = format!("App \"{}\" was deleted", &opts.0);
            output::success(&line);
        },
        Err(err) => {
            spinner.failure();

            output::tower_error(err);
        }
    }
}
