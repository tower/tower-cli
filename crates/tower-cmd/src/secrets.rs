use colored::Colorize;
use clap::{value_parser, Arg, ArgMatches, Command};
use config::Config;
use tower_api::Client;

use crate::output;

pub fn secrets_cmd() -> Command {
    Command::new("secrets")
        .about("Interact with the secrets in your Tower account")
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

pub async fn do_list_secrets(_config: Config, client: Client) {
    let res = client.list_secrets().await;

    match res {
        Ok(secrets) => {
            let headers = vec![
                "Secret".bold().yellow().to_string(),
                "Preview".bold().yellow().to_string(),
            ];

            let data = secrets.iter().map(|sum| {
                vec![
                    sum.name.clone(),
                    sum.preview.dimmed().to_string(),
                ]
            }).collect();

            output::table(headers, data);
        },
        Err(err) => {
            output::tower_error(err);
        }
    }
}

pub async fn do_create_secret(_config: Config, client: Client, args: &ArgMatches) {
    todo!()
}

pub async fn do_delete_secret(_config: Config, client: Client, cmd: Option<(&str, &ArgMatches)>) {
    let opts = cmd.unwrap_or_else(|| {
        output::die("Secret name (e.g. tower secrets delete <name>) is required");
        std::process::exit(1);
    });

    let spinner = output::spinner("Deleting secret...");

    match client.delete_secret(&opts.0).await {
        Ok(_app) => {
            spinner.success();

            let line = format!("Secret \"{}\" was deleted", &opts.0);
            output::success(&line);
        },
        Err(err) => {
            spinner.failure();

            output::tower_error(err);
        }
    }
}
