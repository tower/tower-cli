use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use crypto::encrypt;
use rsa::pkcs1::DecodeRsaPublicKey;

use tower_api::{
    apis:: {
        Error,
        ResponseContent,
        default_api::{
            self,
            CreateSecretParams,
            DeleteSecretParams,
            ListSecretsParams,
            ExportSecretsParams,
            CreateSecretSuccess,
            CreateSecretError,
        },
    },
    models::{
        ExportUserSecretsParams,
        CreateSecretParams as CreateSecretParamsModel,
    },
};

use crate::{
    output,
    api::{
        with_spinner,
        handle_api_response,
    },
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

        let params = ExportSecretsParams {
            export_user_secrets_params: ExportUserSecretsParams {
                schema: None,
                public_key: crypto::serialize_public_key(public_key),
            },
            environment: Some(env.clone()),
            all: Some(*all),
            page: None,
            page_size: None,
        };

        let api_config = &config.into();

        match handle_api_response(|| default_api::export_secrets(api_config, params)).await {
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
        let params = ListSecretsParams {
            environment: Some(env.clone()),
            all: Some(*all),
            page: None,
            page_size: None,
        };

        let api_config = &config.into();

        match handle_api_response(|| default_api::list_secrets(api_config, params)).await {
            Ok(list_response) => {
                let (headers, data) = (
                    vec![
                    "Secret".bold().yellow().to_string(),
                    "Environment".bold().yellow().to_string(),
                    "Preview".bold().yellow().to_string(),
                    ],
                    list_response
                        .secrets
                        .iter()
                        .map(|secret| {
                            vec![
                                secret.name.clone(),
                                secret.environment.clone(),
                                secret.preview.dimmed().to_string(),
                            ]
                        })
                        .collect(),
                );
                output::table(headers, data);
            },
            Err(err) => output::tower_error(err),
        };
    }
}

pub async fn do_create_secret(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap();
    let environment = args.get_one::<String>("environment").unwrap();
    let value = args.get_one::<String>("value").unwrap();

    with_spinner(
        "Creating secret...",
        encrypt_and_create_secret(config, name.clone(), value.clone(), environment.clone()),
    ).await;
}

pub async fn do_delete_secret(config: Config, args: &ArgMatches) {
    let env_default = "default".to_string();
    let name = args.get_one::<String>("name").unwrap();
    let environment = args
        .get_one::<String>("environment")
        .unwrap_or(&env_default);

    let params = DeleteSecretParams {
        name: name.to_string(),
        environment: Some(environment.to_string()),
    };

    with_spinner(
        "Deleting secret...",
        default_api::delete_secret(&config.into(), params),
    ).await;
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
    config: Config,
    name: String,
    value: String,
    environment: String,
) -> Result<ResponseContent<CreateSecretSuccess>, Error<CreateSecretError>> {
    let api_config = &config.into();

    match handle_api_response(|| default_api::describe_secrets_key(&api_config, default_api::DescribeSecretsKeyParams {
        format: None,
    })).await {
        Ok(key_response) => {
            let public_key = rsa::RsaPublicKey::from_pkcs1_pem(&key_response.public_key)
                .unwrap_or_else(|_| {
                    output::die("Failed to parse public key");
                });

            let encrypted_value = encrypt(public_key, value.to_string());
            let preview = create_preview(&value.clone());

            let create_params = CreateSecretParams {
                create_secret_params: CreateSecretParamsModel {
                    schema: None,
                    name: name.clone(),
                    encrypted_value,
                    environment: environment.clone(),
                    preview,
                }
            };

            default_api::create_secret(&api_config, create_params).await
        },
        Err(err) => {
            // Convert the DescribeSecretsKeyError into CreateSecretError
            let converted_err = match err {
                Error::ResponseError(response) => {
                    Error::ResponseError(ResponseContent {
                        status: response.status,
                        content: response.content,
                        entity: None, // CreateSecretError doesn't carry the same entity type
                    })
                }
                Error::Reqwest(e) => Error::Reqwest(e),
                Error::Serde(e) => Error::Serde(e),
                Error::Io(e) => Error::Io(e),
            };

            Err(converted_err)
        }
    }
}
