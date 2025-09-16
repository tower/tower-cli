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
    let resp = api::list_environments(&config).await;

    match resp {
        Ok(resp) => {
            let items = resp
                .environments
                .into_iter()
                .map(|env| env.name.bold().green().to_string())
                .collect();
            output::list(items);
        }
        Err(err) => {
            output::tower_error(err);
        }
    }
}

pub async fn do_create(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("Environment name (--name) is required");
    });

    let mut spinner = output::spinner("Creating environment");

    if let Err(err) = api::create_environment(&config, name).await {
        spinner.failure();
        output::tower_error(err);
    } else {
        spinner.success();
        output::success(&format!("Environment '{}' created", name));
    }
}
