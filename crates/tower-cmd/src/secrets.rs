use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use crypto::encrypt;
use rsa::pkcs1::DecodeRsaPublicKey;

use tower_api::{
    apis:: {
        Error,
        default_api::CreateSecretError,
    },
    models::CreateSecretResponse,
};

use crate::{
    output,
    api,
};

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
                        .action(clap::ArgAction::SetTrue),
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("all")
                        .short('a')
                        .long("all")
                        .action(clap::ArgAction::SetTrue),
                )
                .about("List all of your secrets"),
        )
        .subcommand(
            Command::new("create")
                .arg(
                    Arg::new("name")
                        .short('n')
                        .long("name")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("value")
                        .short('v')
                        .long("value")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .action(clap::ArgAction::Set),
                )
                .about("Create a new secret in your Tower account"),
        )
        .subcommand(
            Command::new("delete")
                .allow_external_subcommands(true)
                .arg(
                    Arg::new("name")
                        .short('n')
                        .long("name")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .help("Name of the secret to delete")
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set)
                        .help("Environment the secret belongs to"),
                )
                .about("Delete a secret in Tower"),
        )
}

pub async fn do_list_secrets(config: Config, args: &ArgMatches) {
    let show = args.get_one::<bool>("show").unwrap_or(&false);
    let env = args.get_one::<String>("environment").unwrap();
    let all = args.get_one::<bool>("all").unwrap_or(&false);

    if *show {
        let (private_key, public_key) = crypto::generate_key_pair();

        match api::export_secrets(&config, env, *all, public_key).await {
            Ok(list_response) => {
                let headers = vec![
                    "Secret".bold().yellow().to_string(),
                    "Environment".bold().yellow().to_string(),
                    "Value".bold().yellow().to_string(),
                ];
                let data = list_response.secrets.iter().map(|secret| {
                    // now we decrypt the value and show it.
                    let decrypted_value = crypto::decrypt(
                        private_key.clone(),
                        secret.encrypted_value.clone(),
                    );

                    vec![
                        secret.name.clone(),
                        secret.environment.clone(),
                        decrypted_value,
                    ]
                }).collect();
                output::table(headers, data);
            },
            Err(err) => output::tower_error(err),
        }
    } else {
        match api::list_secrets(&config, env, *all).await {
            Ok(list_response) => {
                let headers = vec![
                    "Secret".bold().yellow().to_string(),
                    "Environment".bold().yellow().to_string(),
                    "Preview".bold().yellow().to_string(),
                ];
                let data = list_response.secrets.iter().map(|secret| {
                    vec![
                        secret.name.clone(),
                        secret.environment.clone(),
                        secret.preview.dimmed().to_string(),
                    ]
                }).collect();
                output::table(headers, data);
            },
            Err(err) => output::tower_error(err),
        }
    }
}

pub async fn do_create_secret(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap();
    let environment = args.get_one::<String>("environment").unwrap();
    let value = args.get_one::<String>("value").unwrap();

    let mut spinner = output::spinner("Creating secret...");

    match encrypt_and_create_secret(&config, name, value, environment).await { 
        Ok(_) => {
            spinner.success();

            let line = format!(
                "Secret {} created in environment {}",
                name,
                environment,
            );

            output::success(&line);
        },
        Err(err) => {
            log::debug!("Failed to create secrets: {}", err);
            spinner.failure();
        }
    }
}

pub async fn do_delete_secret(config: Config, args: &ArgMatches) {
    let env_default = "default".to_string();
    let name = args.get_one::<String>("name").unwrap();
    let environment = args
        .get_one::<String>("environment")
        .unwrap_or(&env_default);

    let mut spinner = output::spinner("Deleting secret...");

    if let Ok(_) = api::delete_secret(&config, name, environment).await {
        spinner.success();
    } else {
        spinner.failure();
        output::die("There was a problem with the Tower API! Please try again later.");
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

async fn encrypt_and_create_secret(
    config: &Config,
    name: &str,
    value: &str,
    environment: &str,
) -> Result<CreateSecretResponse, Error<CreateSecretError>> {
    match api::describe_secrets_key(config).await {
        Ok(res) => {
            let public_key = rsa::RsaPublicKey::from_pkcs1_pem(&res.public_key)
                .unwrap_or_else(|_| {
                    output::die("Failed to parse public key");
                });

            let encrypted_value = encrypt(public_key, value.to_string());
            let preview = create_preview(value);

            api::create_secret(&config, name, environment, &encrypted_value, &preview).await
        },
        Err(err) => {
            log::debug!("failed to talk to tower api: {}", err);
            output::die("There was a problem with the Tower API! Please try again later.");
        }
    }
}
