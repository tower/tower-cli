use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;

use crate::{api, output};

pub fn environments_cmd() -> Command {
    Command::new("environments")
        .about("Manage the environments in your current Tower account")
        .arg_required_else_help(true)
        .subcommand(Command::new("list").about("List all of your environments"))
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
                .about("Create a new environment in Tower"),
        )
}

pub async fn do_list(config: Config) {
    let resp = output::with_spinner("Listing environments", api::list_environments(&config)).await;

    let headers = vec!["Name"]
        .into_iter()
        .map(|h| h.yellow().to_string())
        .collect();

    let envs_data: Vec<Vec<String>> = resp
        .environments
        .iter()
        .map(|env| vec![env.name.clone()])
        .collect();

    // Display the table using the existing table function
    output::table(headers, envs_data, Some(&resp.environments));
}

pub async fn do_create(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("Environment name (--name) is required");
    });

    output::with_spinner(
        "Creating environment",
        api::create_environment(&config, name),
    )
    .await;

    output::success(&format!("Environment '{}' created", name));
}
