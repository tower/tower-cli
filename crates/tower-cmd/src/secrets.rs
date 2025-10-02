use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use crypto::encrypt;
use rsa::pkcs1::DecodeRsaPublicKey;

use tower_api::{
    apis::{default_api::CreateSecretError, Error},
    models::CreateSecretResponse,
};
use tower_telemetry::debug;

use crate::{api, output, util::cmd};

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
                .about("Delete a secret in Tower"),
        )
}

pub async fn do_list(config: Config, args: &ArgMatches) {
    let all = cmd::get_bool_flag(args, "all");
    let show = cmd::get_bool_flag(args, "show");
    let env = cmd::get_string_flag(args, "environment");

    debug!(
        "listing secrets, environment={} all={} show={}",
        env, all, show
    );

    if show {
        let (private_key, public_key) = crypto::generate_key_pair();

        match api::export_secrets(&config, &env, all, public_key).await {
            Ok(list_response) => {
                let headers = vec![
                    "Secret".bold().yellow().to_string(),
                    "Environment".bold().yellow().to_string(),
                    "Value".bold().yellow().to_string(),
                ];
                let data = list_response
                    .secrets
                    .iter()
                    .map(|secret| {
                        // now we decrypt the value and show it.
                        let decrypted_value =
                            crypto::decrypt(private_key.clone(), secret.encrypted_value.clone())
                                .unwrap();

                        vec![
                            secret.name.clone(),
                            secret.environment.clone(),
                            decrypted_value,
                        ]
                    })
                    .collect();
                output::table(headers, data, Some(&list_response.secrets));
            }
            Err(err) => output::tower_error(err),
        }
    } else {
        match api::list_secrets(&config, &env, all).await {
            Ok(list_response) => {
                let headers = vec![
                    "Secret".bold().yellow().to_string(),
                    "Environment".bold().yellow().to_string(),
                    "Preview".bold().yellow().to_string(),
                ];
                let data = list_response
                    .secrets
                    .iter()
                    .map(|secret| {
                        vec![
                            secret.name.clone(),
                            secret.environment.clone(),
                            secret.preview.dimmed().to_string(),
                        ]
                    })
                    .collect();
                output::table(headers, data, Some(&list_response.secrets));
            }
            Err(err) => output::tower_error(err),
        }
    }
}

pub async fn do_create(config: Config, args: &ArgMatches) {
    let name = cmd::get_string_flag(args, "name");
    let environment = cmd::get_string_flag(args, "environment");
    let value = cmd::get_string_flag(args, "value");

    let mut spinner = output::spinner("Creating secret...");

    match encrypt_and_create_secret(&config, &name, &value, &environment).await {
        Ok(_) => {
            spinner.success();

            let line = format!("Secret {} created in environment {}", name, environment,);

            output::success(&line);
        }
        Err(err) => {
            debug!("Failed to create secrets: {}", err);
            spinner.failure();
        }
    }
}

pub async fn do_delete(config: Config, args: &ArgMatches) {
    let (environment, name) = extract_secret_environment_and_name("delete", args.subcommand());
    debug!("deleting secret, environment={} name={}", environment, name);

    let mut spinner = output::spinner("Deleting secret...");

    if let Ok(_) = api::delete_secret(&config, &name, &environment).await {
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
            let public_key =
                rsa::RsaPublicKey::from_pkcs1_pem(&res.public_key).unwrap_or_else(|_| {
                    output::die("Failed to parse public key");
                });

            let encrypted_value = encrypt(public_key, value.to_string()).unwrap();
            let preview = create_preview(value);

            api::create_secret(&config, name, environment, &encrypted_value, &preview).await
        }
        Err(err) => {
            debug!("failed to talk to tower api: {}", err);
            output::die("There was a problem with the Tower API! Please try again later.");
        }
    }
}

fn extract_secret_environment_and_name(
    subcmd: &str,
    cmd: Option<(&str, &ArgMatches)>,
) -> (String, String) {
    if let Some((slug, _)) = cmd {
        if let Some((env, name)) = slug.split_once('/') {
            return (env.to_string(), name.to_string());
        }

        let line = format!(
            "Secret name is required. Example: tower secrets {} <environment>/<secret name>",
            subcmd
        );
        output::die(&line);
    }

    let line = format!("Secret name and environment is required. Example: tower secrets {} <environment>/<secret name>", subcmd);
    output::die(&line);
}
