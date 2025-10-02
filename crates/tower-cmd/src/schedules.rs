use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use std::collections::HashMap;

use crate::{api, output};

use tower_api::models::schedule::Status;

pub fn schedules_cmd() -> Command {
    Command::new("schedules")
        .about("Manage schedules for your Tower apps")
        .arg_required_else_help(true)
        .subcommand(
            Command::new("list")
                .arg(
                    Arg::new("app")
                        .short('a')
                        .long("app")
                        .value_parser(value_parser!(String))
                        .help("Filter schedules by app name")
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .value_parser(value_parser!(String))
                        .help("Filter schedules by environment")
                        .action(clap::ArgAction::Set),
                )
                .about("List all schedules"),
        )
        .subcommand(
            Command::new("create")
                .arg(
                    Arg::new("app")
                        .short('a')
                        .long("app")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .help("The name of the app to schedule")
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .value_parser(value_parser!(String))
                        .default_value("default")
                        .help("The environment to run the app in")
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("cron")
                        .short('c')
                        .long("cron")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .help("The cron expression defining when the app should run")
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("parameters")
                        .short('p')
                        .long("parameter")
                        .help("Parameters (key=value) to pass to the app")
                        .action(clap::ArgAction::Append),
                )
                .about("Create a new schedule for an app"),
        )
        .subcommand(
            Command::new("delete")
                .allow_external_subcommands(true)
                .about("Delete a schedule"),
        )
        .subcommand(
            Command::new("update")
                .arg(
                    Arg::new("cron")
                        .short('c')
                        .long("cron")
                        .value_parser(value_parser!(String))
                        .help("The cron expression defining when the app should run")
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("parameters")
                        .short('p')
                        .long("parameter")
                        .help("Parameters (key=value) to pass to the app")
                        .action(clap::ArgAction::Append),
                )
                .allow_external_subcommands(true)
                .about("Update an existing schedule"),
        )
}

pub async fn do_list(config: Config, args: &ArgMatches) {
    let app = args.get_one::<String>("app").map(|s| s.as_str());
    let environment = args.get_one::<String>("environment").map(|s| s.as_str());

    match api::list_schedules(&config, app, environment).await {
        Ok(response) => {
            if response.schedules.is_empty() {
                output::write("No schedules found.\n");
                return;
            }

            let headers = vec![
                "ID".yellow().to_string(),
                "App".yellow().to_string(),
                "Environment".yellow().to_string(),
                "Cron".yellow().to_string(),
                "Status".yellow().to_string(),
            ];

            let rows: Vec<Vec<String>> = response
                .schedules
                .iter()
                .map(|schedule| {
                    let status = match schedule.status {
                        Status::Active => "active".green(),
                        Status::Disabled => "disabled".red(),
                    };

                    vec![
                        schedule.id.clone(),
                        schedule.app_name.clone(),
                        schedule.environment.clone(),
                        schedule.cron.clone(),
                        status.to_string(),
                    ]
                })
                .collect();

            output::table(headers, rows, Some(&response.schedules));
        }
        Err(err) => {
            output::tower_error(err);
        }
    }
}

pub async fn do_create(config: Config, args: &ArgMatches) {
    let app_name = args.get_one::<String>("app").unwrap();
    let environment = args.get_one::<String>("environment").unwrap();
    let cron = args.get_one::<String>("cron").unwrap();
    let parameters = parse_parameters(args);

    let mut spinner = output::spinner("Creating schedule");

    match api::create_schedule(&config, app_name, environment, cron, parameters).await {
        Ok(response) => {
            spinner.success();
            output::success(&format!(
                "Schedule created with ID: {}",
                response.schedule.id
            ));
        }
        Err(err) => {
            spinner.failure();
            output::tower_error(err);
        }
    }
}

pub async fn do_update(config: Config, args: &ArgMatches) {
    let schedule_id = extract_schedule_id("update", args.subcommand());
    let cron = args.get_one::<String>("cron");
    let parameters = parse_parameters(args);
    let mut spinner = output::spinner("Updating schedule");

    match api::update_schedule(&config, &schedule_id, cron, parameters).await {
        Ok(_) => {
            spinner.success();
            output::success(&format!("Schedule {} updated", schedule_id));
        }
        Err(err) => {
            spinner.failure();
            output::tower_error(err);
        }
    }
}

pub async fn do_delete(config: Config, args: &ArgMatches) {
    let schedule_id = extract_schedule_id("delete", args.subcommand());
    let mut spinner = output::spinner("Deleting schedule");

    match api::delete_schedule(&config, &schedule_id).await {
        Ok(_) => {
            spinner.success();
            output::success(&format!("Schedule {} deleted", schedule_id));
        }
        Err(err) => {
            spinner.failure();
            output::tower_error(err);
        }
    }
}

fn extract_schedule_id(subcmd: &str, cmd: Option<(&str, &ArgMatches)>) -> String {
    if let Some((id, _)) = cmd {
        return id.to_string();
    }

    let line = format!(
        "Schedule ID is required. Example: tower schedules {} <schedule-id>",
        subcmd
    );
    output::die(&line);
}

/// Parses `--parameter` arguments into a HashMap of key-value pairs.
/// Handles format like "--parameter key=value"
fn parse_parameters(args: &ArgMatches) -> Option<HashMap<String, String>> {
    let mut param_map = HashMap::new();

    if let Some(parameters) = args.get_many::<String>("parameters") {
        for param in parameters {
            match param.split_once('=') {
                Some((key, value)) => {
                    if key.is_empty() {
                        output::error(&format!(
                            "Invalid parameter format: '{}'. Key cannot be empty.",
                            param
                        ));
                        continue;
                    }
                    param_map.insert(key.to_string(), value.to_string());
                }
                None => {
                    output::error(&format!(
                        "Invalid parameter format: '{}'. Expected 'key=value'.",
                        param
                    ));
                }
            }
        }

        Some(param_map)
    } else {
        None
    }
}
