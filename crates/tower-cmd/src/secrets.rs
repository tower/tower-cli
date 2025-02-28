use colored::Colorize;
use clap::{value_parser, Arg, ArgMatches, Command};
use config::Config;
use crypto::encrypt;
use rsa::pkcs1::DecodeRsaPublicKey;

use tower_api::{
    apis::default_api::{self, CreateSecretParams, DeleteSecretParams, ListSecretsParams, ExportSecretsParams},
    models::{
        CreateSecretParams as CreateSecretParamsModel,
        ExportSecretsParams as ExportSecretsParamsModel
    },
};

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

pub async fn do_list_secrets(config: Config, args: &ArgMatches) {
    let show = args.get_one::<bool>("show").unwrap_or(&false);
    let env = args.get_one::<String>("environment").unwrap();
    let all = args.get_one::<bool>("all").unwrap_or(&false);

    if *show {
        let (private_key, public_key) = crypto::generate_key_pair();

        let params = ExportSecretsParams {
            export_secrets_params: ExportSecretsParamsModel {
                schema: None,
                public_key: crypto::serialize_public_key(public_key),
            },
            environment: Some(env.clone()),
            all: Some(*all),
            page: None,
            page_size: None,
        };

        match default_api::export_secrets(&config.into(), params).await {
            Ok(response) => {
                if let Some(list_response) = response.entity {
                    match list_response {
                        default_api::ExportSecretsSuccess::Status200(list_response) => {
                            let headers = vec![
                                "Secret".bold().yellow().to_string(),
                                "Environment".bold().yellow().to_string(),
                                "Value".bold().yellow().to_string(),
                            ];
                            let data = list_response.secrets.iter().map(|secret| {
                                // now we decrypt the value and show it.
                                let decrypted_value = crypto::decrypt(private_key.clone(), secret.encrypted_value.clone());

                                vec![
                                    secret.name.clone(),
                                    secret.environment.clone(),
                                    decrypted_value,
                                ]
                            }).collect();
                            output::table(headers, data);
                        },
                        default_api::ExportSecretsSuccess::UnknownValue(_) => {
                            output::failure("Received unknown response format from server");
                        }
                    }
                }
            },
            Err(err) => output::tower_error(err),
        }

    } else {
        let params = ListSecretsParams {
            environment: Some(env.clone()),
            all: Some(*all),
            page: None,
            page_size: None,
        };

        match default_api::list_secrets(&config.into(), params).await {
            Ok(response) => {
                if let Some(list_response) = response.entity {
                    match list_response {
                        default_api::ListSecretsSuccess::Status200(list_response) => {
                            let (headers, data) = (
                                vec![
                                    "Secret".bold().yellow().to_string(),
                                    "Environment".bold().yellow().to_string(),
                                    "Preview".bold().yellow().to_string(),
                                ],
                                list_response.secrets.iter().map(|secret| {
                                    vec![
                                        secret.name.clone(),
                                        secret.environment.clone(),
                                        secret.preview.dimmed().to_string(),
                                    ]
                                }).collect(),
                            );
                            output::table(headers, data);
                        },
                        default_api::ListSecretsSuccess::UnknownValue(_) => {
                            output::failure("Received unknown response format from server");
                        }
                    }
                }
            },
            Err(err) => output::tower_error(err),
        }

    }
}

pub async fn do_create_secret(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("Secret name (--name) is required");
    });

    let environment = args.get_one::<String>("environment").unwrap();

    let value = args.get_one::<String>("value").unwrap_or_else(|| {
        output::die("Secret value (--value) is required");
    });

    let mut spinner = output::spinner("Creating secret...");
    let api_config = config.into();

    // First get the secrets key
    match default_api::describe_secrets_key(&api_config, default_api::DescribeSecretsKeyParams {
        format: None,
    }).await {
        Ok(key_response) => {
            if let Some(key_success) = key_response.entity {
                match key_success {
                    default_api::DescribeSecretsKeySuccess::Status200(key_response) => {
                        let public_key = rsa::RsaPublicKey::from_pkcs1_pem(&key_response.public_key)
                            .unwrap_or_else(|_| {
                                spinner.failure();
                                output::die("Failed to parse public key");
                            });
                        let encrypted_value = encrypt(public_key, value.to_string());
                        let preview = create_preview(value);

                        let create_params = CreateSecretParams {
                            create_secret_params: CreateSecretParamsModel {
                                schema: None,
                                name: name.clone(),
                                encrypted_value,
                                environment: environment.clone(),
                                preview,
                            }
                        };

                        match default_api::create_secret(&api_config, create_params).await {
                            Ok(create_response) => {
                                if let Some(create_success) = create_response.entity {
                                    match create_success {
                                        default_api::CreateSecretSuccess::Status200(response) => {
                                            spinner.success();
                                            output::success(&format!("Secret \"{}\" was created", response.secret.name));
                                        },
                                        default_api::CreateSecretSuccess::UnknownValue(_) => {
                                            spinner.failure();
                                            output::failure("Received unknown response format from server");
                                        }
                                    }
                                }
                            },
                            Err(err) => {
                                spinner.failure();
                                output::tower_error(err);
                            }
                        }
                    },
                    default_api::DescribeSecretsKeySuccess::UnknownValue(_) => {
                        spinner.failure();
                        output::failure("Received unknown response format from server");
                    }
                }
            }
        },
        Err(err) => {
            spinner.failure();
            output::tower_error(err);
        }
    }
}

pub async fn do_delete_secret(config: Config, cmd: Option<(&str, &ArgMatches)>) {
    let name = cmd.map(|(name, _)| name).unwrap_or_else(|| {
        output::die("Secret name (e.g. tower secrets delete <name>) is required");
    });

    let mut spinner = output::spinner("Deleting secret...");

    let params = DeleteSecretParams {
        name: name.to_string(),
        environment: None,
    };

    match default_api::delete_secret(&config.into(), params).await {
        Ok(_) => {
            spinner.success();
            output::success(&format!("Secret \"{}\" was deleted", name));
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
