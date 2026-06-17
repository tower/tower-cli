use clap::{value_parser, Arg, ArgMatches, Command};
use config::Config;
use tower_api::models::DescribeEnvironmentResponse;

use crate::{
    api, output,
    util::{
        prompt,
        text::{join_with_and, pluralize},
    },
};

pub fn environments_cmd() -> Command {
    Command::new("environments")
        .about("Manage the environments in your current Tower account")
        .arg_required_else_help(true)
        .subcommand(Command::new("list").about("List all of your environments"))
        .subcommand(
            Command::new("delete")
                .arg(
                    Arg::new("name")
                        .short('n')
                        .long("name")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .action(clap::ArgAction::Set),
                )
                .about("Delete an environment"),
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
                .about("Create a new environment in Tower"),
        )
}

pub async fn do_list(config: Config) {
    let environments =
        output::with_spinner("Listing environments", api::list_environments(&config)).await;

    let headers = vec!["Name".to_string()];

    let envs_data: Vec<Vec<String>> = environments
        .iter()
        .map(|env| vec![env.name.clone()])
        .collect();

    // Display the table using the existing table function
    output::table(headers, envs_data, Some(&environments));
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

fn env_resources_description(env: DescribeEnvironmentResponse) -> Option<String> {
    if env.number_catalogs > 0 || env.number_schedules > 0 || env.number_secrets > 0 {
        let resources: Vec<_> = vec![
            (env.number_catalogs, "catalog"),
            (env.number_schedules, "schedule"),
            (env.number_secrets, "secret"),
        ]
        .into_iter()
        .filter(|(count, _)| *count > 0)
        .map(|(count, noun)| format!("{} {}", count, pluralize(noun, count, None)))
        .collect();

        return Some(join_with_and(resources));
    }

    return None;
}

pub async fn do_delete(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("Environment name (--name) is required");
    });

    let env = output::with_spinner(
        "Retrieving environment...",
        api::describe_environment(&config, name),
    )
    .await;

    if !env.environment.is_deletable {
        output::error(&format!("You cannot delete the {name} environment."));
        return;
    }

    if let Some(desc) = env_resources_description(env) {
        output::write(&format!("Warning! Your environment contains {desc}.\n"))
    }

    let ans = prompt::confirm(
        &format!("Are you sure you want to delete your {name} environment?"),
        false,
    );

    match ans {
        Ok(true) => {
            output::with_spinner(
                &format!("Deleting environment {name}"),
                api::delete_environment(&config, name),
            )
            .await;

            output::success(&format!("Environment '{name}' deleted"));
        }
        Ok(false) => output::write("Aborting environment deletion.\n"),
        Err(prompt::Error::ConfirmationPromptCancelled) => {
            output::write("Aborting environment deletion.\n")
        }
        Err(_) => {
            output::error(
                "Something went wrong. Please try again, and contact us if the issue persists.",
            );
        }
    }
}
