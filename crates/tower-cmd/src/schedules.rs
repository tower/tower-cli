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
                .arg(
                    Arg::new("schedule_id")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("The ID of the schedule to delete"),
                )
                .override_usage("tower schedules delete [OPTIONS] <SCHEDULE_ID>")
                .after_help(
                    "Example:\n  tower schedules delete 01890a5d-ac96-774b-bcce-b302099a8057",
                )
                .about("Delete a schedule"),
        )
        .subcommand(
            Command::new("update")
                .arg(
                    Arg::new("schedule_id")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("The ID of the schedule to update"),
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
                .after_help(
                    "Example:\n  tower schedules update 01890a5d-ac96-774b-bcce-b302099a8057 --cron '0 9 * * *'",
                )
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
    let schedule_id = args
        .get_one::<String>("schedule_id")
        .expect("schedule_id is required");
    let cron = args.get_one::<String>("cron");
    let parameters = parse_parameters(out, args);

    out.with_spinner(
        "Updating schedule",
        api::update_schedule(&config, schedule_id, cron, parameters),
    )
    .await;

    out.success(&format!("Schedule {} updated", schedule_id));
}

pub async fn do_delete(out: &crate::output::Out, config: Config, args: &ArgMatches) {
    let schedule_id = args
        .get_one::<String>("schedule_id")
        .expect("schedule_id is required");

    out.with_spinner(
        "Deleting schedule",
        api::delete_schedule(&config, schedule_id),
    )
    .await;

    out.success(&format!("Schedule {} deleted", schedule_id));
}

/// Parses `--parameter` arguments into a HashMap of key-value pairs.
/// Handles format like "--parameter key=value". Malformed entries (no `=`, or
/// an empty key) are reported and dropped. When no valid entries remain, this
/// returns `None` so the request is sent as if `--parameter` was never given.
fn parse_parameters(
    out: &crate::output::Out,
    args: &ArgMatches,
) -> Option<HashMap<String, String>> {
    let parameters = args.get_many::<String>("parameters")?;
    let mut param_map = HashMap::new();

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

    if param_map.is_empty() {
        None
    } else {
        Some(param_map)
    }
}

#[cfg(test)]
mod tests {
    use super::{parse_parameters, schedules_cmd};
    use crate::output;

    fn parse(args: &[&str]) -> Result<clap::ArgMatches, clap::Error> {
        let mut full = vec!["schedules"];
        full.extend_from_slice(args);
        schedules_cmd().try_get_matches_from(full)
    }

    fn sub<'a>(matches: &'a clap::ArgMatches) -> (&'a str, &'a clap::ArgMatches) {
        matches.subcommand().unwrap()
    }

    #[test]
    fn delete_parses_positional_schedule_id() {
        let matches = parse(&["delete", "sched-123"]).unwrap();
        let (name, args) = sub(&matches);

        assert_eq!(name, "delete");
        assert_eq!(
            args.get_one::<String>("schedule_id").map(|s| s.as_str()),
            Some("sched-123")
        );
    }

    #[test]
    fn delete_without_schedule_id_is_a_parse_error() {
        assert!(parse(&["delete"]).is_err());
    }

    #[test]
    fn update_parses_positional_id_with_space_separated_flags() {
        let matches = parse(&["update", "sched-123", "--cron", "0 9 * * *"]).unwrap();
        let (name, args) = sub(&matches);

        assert_eq!(name, "update");
        assert_eq!(
            args.get_one::<String>("schedule_id").map(|s| s.as_str()),
            Some("sched-123")
        );
        assert_eq!(
            args.get_one::<String>("cron").map(|s| s.as_str()),
            Some("0 9 * * *")
        );
    }

    #[test]
    fn update_parses_equals_flag_forms() {
        let matches = parse(&[
            "update",
            "sched-123",
            "--cron=0 9 * * *",
            "--parameter=key=value",
        ])
        .unwrap();
        let (_, args) = sub(&matches);

        assert_eq!(
            args.get_one::<String>("cron").map(|s| s.as_str()),
            Some("0 9 * * *")
        );
        let params: Vec<&String> = args.get_many::<String>("parameters").unwrap().collect();
        assert_eq!(params, vec!["key=value"]);
    }

    #[test]
    fn update_accepts_repeated_parameters() {
        let matches = parse(&["update", "sched-123", "-p", "a=1", "-p", "b=2"]).unwrap();
        let (_, args) = sub(&matches);

        let params: Vec<&String> = args.get_many::<String>("parameters").unwrap().collect();
        assert_eq!(params, vec!["a=1", "b=2"]);
    }

    #[test]
    fn update_without_schedule_id_is_a_parse_error() {
        assert!(parse(&["update"]).is_err());
        assert!(parse(&["update", "--cron", "0 9 * * *"]).is_err());
    }

    #[test]
    fn parse_parameters_keeps_valid_pairs() {
        let out = output::Out::sink();
        let matches = parse(&["update", "sched-123", "-p", "a=1", "-p", "b=two"]).unwrap();
        let (_, args) = sub(&matches);

        let params = parse_parameters(&out, args).expect("expected parameters");
        assert_eq!(params.get("a").map(|s| s.as_str()), Some("1"));
        assert_eq!(params.get("b").map(|s| s.as_str()), Some("two"));
    }

    #[test]
    fn parse_parameters_drops_malformed_entries() {
        let out = output::Out::sink();
        let matches = parse(&[
            "update",
            "sched-123",
            "-p",
            "good=1",
            "-p",
            "no-equals",
            "-p",
            "=empty-key",
        ])
        .unwrap();
        let (_, args) = sub(&matches);

        let params = parse_parameters(&out, args).expect("expected parameters");
        assert_eq!(params.len(), 1);
        assert_eq!(params.get("good").map(|s| s.as_str()), Some("1"));
    }

    #[test]
    fn parse_parameters_yields_none_when_nothing_valid_remains() {
        let out = output::Out::sink();
        let matches =
            parse(&["update", "sched-123", "-p", "no-equals", "-p", "=empty-key"]).unwrap();
        let (_, args) = sub(&matches);

        assert!(parse_parameters(&out, args).is_none());
    }

    #[test]
    fn parse_parameters_yields_none_when_flag_absent() {
        let out = output::Out::sink();
        let matches = parse(&["update", "sched-123"]).unwrap();
        let (_, args) = sub(&matches);

        assert!(parse_parameters(&out, args).is_none());
    }
}
