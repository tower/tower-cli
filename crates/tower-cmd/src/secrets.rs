use colored::Colorize;
use clap::{value_parser, Arg, ArgMatches, Command};
use config::Config;
use tower_api::Client;
use crypto::encrypt;

use crate::output;

pub fn secrets_cmd() -> Command {
    Command::new("secrets")
        .about("Interact with the secrets in your Tower account")
        .arg_required_else_help(true)
        .subcommand(
            Command::new("list")
                .arg(
                    Arg::new("show")
                        .short('s')
                        .long("show")
                        .action(clap::ArgAction::SetTrue)
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set)
                )
                .arg(
                    Arg::new("all")
                        .short('a')
                        .long("all")
                        .action(clap::ArgAction::SetTrue)
                )
                .about("List all of your secrets")
        )
        .subcommand(
            Command::new("create")
                .arg(
                    Arg::new("name")
                        .short('n')
                        .long("name")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set)
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set)
                )
                .arg(
                    Arg::new("value")
                        .short('v')
                        .long("value")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set)
                )
                .about("Create a new secret in your Tower account")
        )
        .subcommand(
            Command::new("delete")
                .allow_external_subcommands(true)
                .about("Delete a secret in Tower")
        )
}

pub async fn do_list_secrets(_config: Config, client: Client, args: &ArgMatches) {
    let show = args.get_one::<bool>("show").unwrap_or(&false);

    // Since environment has a default value, it is a big problem if it's not defined.
    let env = args.get_one::<String>("environment").unwrap();

    let all = args.get_one::<bool>("all").unwrap_or(&false);

    let (headers, data) = if *show {
        match client.export_secrets(*all, Some(env.to_string())).await {
            Ok(secrets) => (
                vec![
                    "Secret".bold().yellow().to_string(),
                    "Environment".bold().yellow().to_string(),
                    "Value".bold().yellow().to_string(),
                ],
                secrets.iter().map(|sum| {
                    vec![
                        sum.name.clone(),
                        sum.environment.clone(),
                        sum.value.dimmed().to_string(),
                    ]
                }).collect(),
            ),
            Err(err) => return output::tower_error(err),
        }
    } else {
        match client.list_secrets(*all, Some(env.to_string())).await {
            Ok(secrets) => (
                vec![
                    "Secret".bold().yellow().to_string(),
                    "Environment".bold().yellow().to_string(),
                    "Preview".bold().yellow().to_string(),
                ],
                secrets.iter().map(|sum| {
                    vec![
                        sum.name.clone(),
                        sum.environment.clone(),
                        sum.preview.dimmed().to_string(),
                    ]
                }).collect(),
            ),
            Err(err) => return output::tower_error(err),
        }
    };

    output::table(headers, data);
}

pub async fn do_create_secret(_config: Config, client: Client, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("Secret name (--name) is required");
    });

    // Since environment has a default value, it is a big problem if it's not defined.
    let environment = args.get_one::<String>("environment").unwrap();

    let value = args.get_one::<String>("value").unwrap_or_else(|| {
        output::die("Secret value (--value) is required");
    });

    let mut spinner = output::spinner("Creating secret...");

    match client.secrets_key().await {
        Ok(public_key) => {
            let encrypted_value = encrypt(public_key, value.to_string());
            let preview = create_preview(value);

            match client.create_secret(&name, &encrypted_value, &preview, &environment).await {
                Ok(secret) => {
                    spinner.success();

                    let line = format!("Secret \"{}\" was created", secret.name);
                    output::success(&line);
                },
                Err(err) => {
                    spinner.failure();
                    output::tower_error(err);
                }
            }
        },
        Err(err) => {
            spinner.failure();
            output::tower_error(err);
        }
    }
}

pub async fn do_delete_secret(_config: Config, client: Client, cmd: Option<(&str, &ArgMatches)>) {
    let opts = cmd.unwrap_or_else(|| {
        output::die("Secret name (e.g. tower secrets delete <name>) is required");
    });

    let mut spinner = output::spinner("Deleting secret...");

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

fn create_preview(value: &str) -> String {
    let len = value.len();
    let preview_len = 10;
    let suffix_length = 4;

    if len <= preview_len {
        "XXXXXXXXXX".to_string()
    } else {
        let suffix = &value[value.char_indices().rev().nth(suffix_length - 1).unwrap().0..];
        format!("XXXXXX{}", suffix)
    }
}
