use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;

use tower_api::models::Run;

use crate::{api, output, util::cmd};

pub fn apps_cmd() -> Command {
    Command::new("apps")
        .about("Manage the apps in your current Tower account")
        .arg_required_else_help(true)
        .subcommand(
            Command::new("list")
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .value_parser(value_parser!(String))
                        .help("Filter apps by environment")
                        .action(clap::ArgAction::Set),
                )
                .about("List all apps in your Tower account"),
        )
        .subcommand(
            Command::new("show")
                .arg(
                    Arg::new("app_name")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("Name of the app"),
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .help("The environment to resolve the app against")
                        .action(clap::ArgAction::Set),
                )
                .about("Show details for a Tower app and its recent runs"),
        )
        .subcommand(
            Command::new("logs")
                .arg(
                    Arg::new("app_name")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("app_name#run_number"),
                )
                .arg(
                    Arg::new("run_number")
                        .value_parser(value_parser!(i64))
                        .index(2),
                )
                .about("Get the logs from a previous Tower app run"),
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
                    Arg::new("description")
                        .long("description")
                        .value_parser(value_parser!(String))
                        .default_value("")
                        .action(clap::ArgAction::Set),
                )
                .about("Create a new app in Tower"),
        )
        .subcommand(
            Command::new("delete")
                .arg(
                    Arg::new("app_name")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("Name of the app"),
                )
                .about("Delete an app in Tower"),
        )
        .subcommand(
            Command::new("cancel")
                .arg(
                    Arg::new("app_name")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("Name of the app"),
                )
                .arg(
                    Arg::new("run_number")
                        .value_parser(value_parser!(i64))
                        .index(2)
                        .required(true)
                        .help("Run number to cancel"),
                )
                .about("Cancel a running app run"),
        )
}

pub async fn do_logs(out: &output::Out, config: Config, cmd: &ArgMatches) {
    let app_name_raw = cmd
        .get_one::<String>("app_name")
        .expect("app_name is required");
    let (name, seq) = if let Some((name, num_str)) = app_name_raw.split_once('#') {
        let num = num_str
            .parse::<i64>()
            .unwrap_or_else(|_| out.die("Run number must be a number"));
        (name.to_string(), num)
    } else {
        let num = match cmd.get_one::<i64>("run_number").copied() {
            Some(n) => n,
            None => latest_run_number(out, &config, app_name_raw).await,
        };
        (app_name_raw.clone(), num)
    };

    if let Ok(resp) = api::describe_run_logs(&config, &name, seq).await {
        for line in resp.log_lines {
            out.remote_log_event(&line);
        }
    }
}

pub async fn do_show(out: &output::Out, config: Config, cmd: &ArgMatches) {
    let name = cmd
        .get_one::<String>("app_name")
        .expect("app_name is required");
    let env = cmd::get_string_flag(cmd, "environment");

    match api::describe_app(&config, &name, Some(&env)).await {
        Ok(app_response) => out.text(&app_details_text(&app_response), &app_response),
        Err(err) => out.tower_error_and_die(err, "Fetching app details failed"),
    }
}

fn app_details_text(response: &tower_api::models::DescribeAppResponse) -> String {
    let app = &response.app;
    let mut text = String::new();

    text.push_str(&format!("{} {}\n", "Name:".bold().green(), app.name));
    text.push_str(&format!("{}\n", "Description".bold().green()));
    text.push_str(&output::paragraph(&app.short_description));
    text.push_str("\n\n");
    text.push_str(&format!("{}\n", "Recent runs".bold().green()));

    let headers = vec!["#", "Status", "Start Time", "Elapsed Time"]
        .into_iter()
        .map(str::to_string)
        .collect();

    let rows = response
        .runs
        .iter()
        .map(|run: &Run| {
            let status_str = format!("{:?}", &run.status);

            // Format start time
            let start_time = if let Some(started_at) = &run.started_at {
                if !started_at.is_empty() {
                    started_at.to_string()
                } else {
                    format!("Scheduled at {}", &run.scheduled_at)
                }
            } else {
                format!("Scheduled at {}", &run.scheduled_at)
            };

            // Calculate elapsed time
            let elapsed_time = if let Some(ended_at) = &run.ended_at {
                if !ended_at.is_empty() {
                    if let (Some(started_at), Some(ended_at)) = (&run.started_at, &run.ended_at) {
                        let start = started_at.parse::<chrono::DateTime<chrono::Utc>>().ok();
                        let end = ended_at.parse::<chrono::DateTime<chrono::Utc>>().ok();
                        if let (Some(start), Some(end)) = (start, end) {
                            format!("{:.1}s", (end - start).num_seconds())
                        } else {
                            "Invalid time".into()
                        }
                    } else {
                        "Invalid time".into()
                    }
                } else if run.started_at.is_some() {
                    "Running".into()
                } else {
                    "Pending".into()
                }
            } else if run.started_at.is_some() {
                "Running".into()
            } else {
                "Pending".into()
            };

            vec![run.number.to_string(), status_str, start_time, elapsed_time]
        })
        .collect();

    text.push_str(&format!("{}\n", output::table_text(headers, rows)));
    text
}

pub async fn do_list_apps(out: &output::Out, config: Config, args: &ArgMatches) {
    let env = args.get_one::<String>("environment").map(|s| s.as_str());
    let apps = out
        .with_spinner("Listing apps", api::list_apps(&config, env))
        .await;

    let items = apps
        .iter()
        .map(|app_summary| {
            let app = &app_summary.app;
            let desc = if app.short_description.is_empty() {
                output::placeholder("No description")
            } else {
                app.short_description.to_string()
            };
            format!("{}\n{}", output::title(&app.name), desc)
        })
        .collect();
    out.list(items, Some(&apps));
}

pub async fn do_create(out: &output::Out, config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        out.die("App name (--name) is required");
    });

    let description = args.get_one::<String>("description").unwrap();

    let app = out
        .with_spinner("Creating app", api::create_app(&config, name, description))
        .await;

    out.success_with_data(&format!("App '{}' created", name), Some(app));
}

pub async fn do_delete(out: &output::Out, config: Config, cmd: &ArgMatches) {
    let name = cmd
        .get_one::<String>("app_name")
        .expect("app_name is required");

    out.with_spinner("Deleting app", api::delete_app(&config, name))
        .await;
}

pub async fn do_cancel(out: &output::Out, config: Config, cmd: &ArgMatches) {
    let name = cmd
        .get_one::<String>("app_name")
        .expect("app_name should be required");
    let seq = cmd
        .get_one::<i64>("run_number")
        .copied()
        .expect("run_number should be required");

    let response = out
        .with_spinner("Cancelling run", api::cancel_run(&config, name, seq))
        .await;

    let run = &response.run;
    let status = format!("{:?}", run.status);
    out.success_with_data(
        &format!("Run #{} for '{}' cancelled (status: {})", seq, name, status),
        Some(response),
    );
}

async fn latest_run_number(out: &output::Out, config: &Config, name: &str) -> i64 {
    match api::describe_app(config, name, None).await {
        Ok(resp) => resp
            .runs
            .iter()
            .map(|r| r.number)
            .max()
            .unwrap_or_else(|| out.die(&format!("No runs found for app '{}'", name))),
        Err(err) => out.tower_error_and_die(err, "Fetching app details failed"),
    }
}

#[cfg(test)]
mod tests {
    use super::apps_cmd;

    #[test]
    fn test_separate_run_number_parsing() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "logs", "hello-world", "11"])
            .unwrap();
        let (_, sub_matches) = matches.subcommand().unwrap();

        assert_eq!(
            sub_matches
                .get_one::<String>("app_name")
                .map(|s| s.as_str()),
            Some("hello-world")
        );
        assert_eq!(sub_matches.get_one::<i64>("run_number"), Some(&11));
    }

    #[test]
    fn test_cancel_args_parsing() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "cancel", "my-app", "42"])
            .unwrap();
        let (cmd, sub_matches) = matches.subcommand().unwrap();

        assert_eq!(cmd, "cancel");
        assert_eq!(
            sub_matches
                .get_one::<String>("app_name")
                .map(|s| s.as_str()),
            Some("my-app")
        );
        assert_eq!(sub_matches.get_one::<i64>("run_number"), Some(&42));
    }

    #[test]
    fn test_cancel_requires_both_args() {
        let result = apps_cmd().try_get_matches_from(["apps", "cancel", "my-app"]);
        assert!(result.is_err());

        let result = apps_cmd().try_get_matches_from(["apps", "cancel"]);
        assert!(result.is_err());
    }

    #[test]
    fn list_defaults_to_no_environment_filter() {
        let matches = apps_cmd().try_get_matches_from(["apps", "list"]).unwrap();
        let (_, list_args) = matches.subcommand().unwrap();

        assert_eq!(list_args.get_one::<String>("environment"), None);
    }

    #[test]
    fn list_accepts_environment_flag() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "list", "-e", "production"])
            .unwrap();
        let (_, list_args) = matches.subcommand().unwrap();

        assert_eq!(
            list_args
                .get_one::<String>("environment")
                .map(|s| s.as_str()),
            Some("production")
        );
    }

    #[test]
    fn show_defaults_to_default_environment() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "show", "my-app"])
            .unwrap();
        let (_, show_args) = matches.subcommand().unwrap();

        assert_eq!(
            show_args.get_one::<String>("environment").unwrap(),
            "default"
        );
    }

    #[test]
    fn show_accepts_environment_flag() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "show", "my-app", "-e", "production"])
            .unwrap();
        let (_, show_args) = matches.subcommand().unwrap();

        assert_eq!(
            show_args.get_one::<String>("environment").unwrap(),
            "production"
        );
    }
}
