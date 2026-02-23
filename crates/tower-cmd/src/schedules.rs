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
                .arg(
                    Arg::new("schedule_id")
                        .required(true)
                        .value_parser(value_parser!(String))
                        .help("The schedule ID to delete")
                        .action(clap::ArgAction::Set),
                )
                .override_usage("tower schedules delete [OPTIONS] <SCHEDULE_ID>")
                .after_help("Example: tower schedules delete 123")
                .about("Delete a schedule"),
        )
        .subcommand(
            Command::new("update")
                .arg(
                    Arg::new("schedule_id")
                        .required(true)
                        .value_parser(value_parser!(String))
                        .help("The schedule ID to update")
                        .action(clap::ArgAction::Set),
                )
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
                .override_usage("tower schedules update [OPTIONS] <SCHEDULE_ID>")
                .after_help("Example: tower schedules update 123 --cron \"*/15 * * * *\"")
                .about("Update an existing schedule"),
        )
}

pub async fn do_list(config: Config, args: &ArgMatches) {
    let app = args.get_one::<String>("app").map(|s| s.as_str());
    let environment = args.get_one::<String>("environment").map(|s| s.as_str());

    let response = output::with_spinner(
        "Listing schedules",
        api::list_schedules(&config, app, environment),
    )
    .await;

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

pub async fn do_create(config: Config, args: &ArgMatches) {
    let app_name = args.get_one::<String>("app").unwrap();
    let environment = args.get_one::<String>("environment").unwrap();
    let cron = args.get_one::<String>("cron").unwrap();
    let parameters = parse_parameters(args);

    let response = output::with_spinner(
        "Creating schedule",
        api::create_schedule(&config, app_name, environment, cron, parameters),
    )
    .await;

    output::success(&format!(
        "Schedule created with ID: {}",
        response.schedule.id
    ));
}

pub async fn do_update(config: Config, args: &ArgMatches) {
    let schedule_id = args.get_one::<String>("schedule_id").unwrap();
    let cron = args.get_one::<String>("cron");
    let parameters = parse_parameters(args);

    output::with_spinner(
        "Updating schedule",
        api::update_schedule(&config, schedule_id, cron, parameters),
    )
    .await;

    output::success(&format!("Schedule {} updated", schedule_id));
}

pub async fn do_delete(config: Config, args: &ArgMatches) {
    let schedule_id = args.get_one::<String>("schedule_id").unwrap();

    output::with_spinner(
        "Deleting schedule",
        api::delete_schedule(&config, schedule_id),
    )
    .await;

    output::success(&format!("Schedule {} deleted", schedule_id));
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

        if param_map.is_empty() {
            None
        } else {
            Some(param_map)
        }
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::{parse_parameters, schedules_cmd};

    #[test]
    fn update_accepts_positional_schedule_id_and_flags() {
        let matches = schedules_cmd()
            .try_get_matches_from([
                "schedules",
                "update",
                "sch_123",
                "--cron",
                "*/10 * * * *",
                "--parameter",
                "env=prod",
                "-p",
                "team=platform",
            ])
            .expect("update args should parse");

        let ("update", update_args) = matches.subcommand().expect("expected update subcommand")
        else {
            panic!("expected update subcommand");
        };

        assert_eq!(
            update_args
                .get_one::<String>("schedule_id")
                .map(String::as_str),
            Some("sch_123")
        );
        assert_eq!(
            update_args.get_one::<String>("cron").map(String::as_str),
            Some("*/10 * * * *")
        );

        let params: Vec<&str> = update_args
            .get_many::<String>("parameters")
            .expect("expected parameters")
            .map(String::as_str)
            .collect();
        assert_eq!(params, vec!["env=prod", "team=platform"]);
    }

    #[test]
    fn update_accepts_equals_sign_flag_forms() {
        let matches = schedules_cmd()
            .try_get_matches_from([
                "schedules",
                "update",
                "sch_456",
                "--cron=*/5 * * * *",
                "--parameter=region=us-east-1",
            ])
            .expect("equals-form args should parse");

        let ("update", update_args) = matches.subcommand().expect("expected update subcommand")
        else {
            panic!("expected update subcommand");
        };

        assert_eq!(
            update_args
                .get_one::<String>("schedule_id")
                .map(String::as_str),
            Some("sch_456")
        );
        assert_eq!(
            update_args.get_one::<String>("cron").map(String::as_str),
            Some("*/5 * * * *")
        );
        assert_eq!(
            update_args
                .get_many::<String>("parameters")
                .expect("expected parameter")
                .next()
                .map(String::as_str),
            Some("region=us-east-1")
        );
    }

    #[test]
    fn update_requires_schedule_id() {
        let result =
            schedules_cmd().try_get_matches_from(["schedules", "update", "--cron", "*/15 * * * *"]);
        assert!(result.is_err());
    }

    #[test]
    fn delete_requires_schedule_id() {
        let result = schedules_cmd().try_get_matches_from(["schedules", "delete"]);
        assert!(result.is_err());
    }

    #[test]
    fn parse_parameters_valid_pairs() {
        let matches = schedules_cmd()
            .try_get_matches_from([
                "schedules",
                "update",
                "sch_789",
                "--parameter",
                "env=prod",
                "-p",
                "team=platform",
            ])
            .expect("update args should parse");

        let ("update", update_args) = matches.subcommand().expect("expected update subcommand")
        else {
            panic!("expected update subcommand");
        };

        let params = parse_parameters(update_args).expect("expected parsed parameters");
        assert_eq!(params.get("env"), Some(&"prod".to_string()));
        assert_eq!(params.get("team"), Some(&"platform".to_string()));
    }

    #[test]
    fn parse_parameters_invalid_entries_return_none() {
        let matches = schedules_cmd()
            .try_get_matches_from([
                "schedules",
                "update",
                "sch_789",
                "--parameter",
                "invalid",
                "-p",
                "=missing-key",
            ])
            .expect("update args should parse");

        let ("update", update_args) = matches.subcommand().expect("expected update subcommand")
        else {
            panic!("expected update subcommand");
        };

        assert_eq!(parse_parameters(update_args), None);
    }

    #[test]
    fn parse_parameters_mixed_valid_and_invalid_keeps_valid() {
        let matches = schedules_cmd()
            .try_get_matches_from([
                "schedules",
                "update",
                "sch_789",
                "--parameter",
                "env=prod",
                "-p",
                "invalid",
            ])
            .expect("update args should parse");

        let ("update", update_args) = matches.subcommand().expect("expected update subcommand")
        else {
            panic!("expected update subcommand");
        };

        let params = parse_parameters(update_args).expect("expected parsed parameters");
        assert_eq!(params.get("env"), Some(&"prod".to_string()));
        assert_eq!(params.len(), 1);
    }
}
