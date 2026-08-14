use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use std::collections::HashMap;

use crate::api;

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

pub async fn do_list(out: &crate::output::Out, config: Config, args: &ArgMatches) {
    let app = args.get_one::<String>("app").map(|s| s.as_str());
    let environment = args.get_one::<String>("environment").map(|s| s.as_str());

    let schedules = out
        .with_spinner(
            "Listing schedules",
            api::list_schedules(&config, app, environment),
        )
        .await;

    if schedules.is_empty() {
        out.text("No schedules found.\n", &schedules);
        return;
    }

    let headers = vec!["ID", "App", "Environment", "Cron", "Status"]
        .into_iter()
        .map(str::to_string)
        .collect();

    let rows: Vec<Vec<String>> = schedules
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

    out.table(headers, rows, Some(&schedules));
}

pub async fn do_create(out: &crate::output::Out, config: Config, args: &ArgMatches) {
    let app_name = args.get_one::<String>("app").unwrap();
    let environment = args.get_one::<String>("environment").unwrap();
    let cron = args.get_one::<String>("cron").unwrap();
    let parameters = parse_parameters(out, args);

    let response = out
        .with_spinner(
            "Creating schedule",
            api::create_schedule(&config, app_name, environment, cron, parameters),
        )
        .await;

    out.success(&format!(
        "Schedule created with ID: {}",
        response.schedule.id
    ));
}

pub async fn do_update(out: &crate::output::Out, config: Config, args: &ArgMatches) {
    let schedule_id = extract_schedule_id(out, "update", args.subcommand());
    let cron = args.get_one::<String>("cron");
    let parameters = parse_parameters(out, args);

    out.with_spinner(
        "Updating schedule",
        api::update_schedule(&config, &schedule_id, cron, parameters),
    )
    .await;

    out.success(&format!("Schedule {} updated", schedule_id));
}

pub async fn do_delete(out: &crate::output::Out, config: Config, args: &ArgMatches) {
    let schedule_id = extract_schedule_id(out, "delete", args.subcommand());

    out.with_spinner(
        "Deleting schedule",
        api::delete_schedule(&config, &schedule_id),
    )
    .await;

    out.success(&format!("Schedule {} deleted", schedule_id));
}

fn extract_schedule_id(
    out: &crate::output::Out,
    subcmd: &str,
    cmd: Option<(&str, &ArgMatches)>,
) -> String {
    if let Some((id, _)) = cmd {
        return id.to_string();
    }

    let line = format!(
        "Schedule ID is required. Example: tower schedules {} <schedule-id>",
        subcmd
    );
    out.die(&line);
}

/// Parses `--parameter` arguments into a HashMap of key-value pairs.
/// Handles format like "--parameter key=value"
fn parse_parameters(
    out: &crate::output::Out,
    args: &ArgMatches,
) -> Option<HashMap<String, String>> {
    let mut param_map = HashMap::new();

    if let Some(parameters) = args.get_many::<String>("parameters") {
        for param in parameters {
            match param.split_once('=') {
                Some((key, value)) => {
                    if key.is_empty() {
                        out.error(&format!(
                            "Invalid parameter format: '{}'. Key cannot be empty.",
                            param
                        ));
                        continue;
                    }
                    param_map.insert(key.to_string(), value.to_string());
                }
                None => {
                    out.error(&format!(
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
