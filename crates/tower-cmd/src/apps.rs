use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;

use tower_api::{
    apis::default_api::{
        self, CreateAppsParams, DeleteAppParams, DescribeAppParams,
        GetAppRunLogsParams, ListAppsParams,
    },
    models::{CreateAppParams, Run},
};

use crate::{
    output,
    api::{
        handle_api_response,
        with_spinner,
    }
};

pub fn apps_cmd() -> Command {
    Command::new("apps")
        .about("Interact with the apps that you own")
        .arg_required_else_help(true)
        .subcommand(Command::new("list").about("List all of your apps`"))
        .subcommand(
            Command::new("show")
                .allow_external_subcommands(true)
                .arg(
                    Arg::new("name")
                        .short('n')
                        .long("name")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .action(clap::ArgAction::Set),
                )
                .about("Show the details about an app in Tower"),
        )
        .subcommand(
            Command::new("logs")
                .allow_external_subcommands(true)
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
                .allow_external_subcommands(true)
                .arg(
                    Arg::new("name")
                        .short('n')
                        .long("name")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .action(clap::ArgAction::Set),
                )
                .about("Delete an app in Tower"),
        )
}

pub async fn do_logs_app(config: Config, cmd: Option<(&str, &ArgMatches)>) {
    let (app_name, seq) = extract_app_run(cmd);
    
    let response = with_spinner(
        "Fetching logs...",
        default_api::get_app_run_logs(
            &config.into(),
            GetAppRunLogsParams {
                name: app_name.clone(),
                seq,
            },
        ),
    ).await;

    for line in response.log_lines {
        output::log_line(&line.timestamp, &line.message, output::LogLineType::Remote);
    }
}

pub async fn do_show_app(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap();

    let api_config = &config.into();

    let params = DescribeAppParams {
        name: name.to_string(),
        runs: Some(5),
    };

    let resp = handle_api_response(|| default_api::describe_app(&api_config, params)).await;

    match resp {
        Ok(app_response) => {
            let app = app_response.app;
            let runs = app_response.runs;

            let line = format!("{} {}\n", "Name:".bold().green(), app.name);
            output::write(&line);

            let line = format!("{}\n", "Description:".bold().green());
            output::write(&line);

            let line = output::paragraph(&app.short_description);
            output::write(&line);

            output::newline();
            output::newline();

            let line = format!("{}\n", "Recent runs:".bold().green());
            output::write(&line);

            let headers = vec!["#", "Status", "Start Time", "Elapsed Time"]
                .into_iter()
                .map(|h| h.yellow().to_string())
                .collect();

            let rows = runs
                .iter()
                .map(|run: &Run| {
                    let status = &run.status;
                    let status_str = format!("{:?}", status);

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
                            if let (Some(started_at), Some(ended_at)) =
                                (&run.started_at, &run.ended_at)
                            {
                                let start =
                                    started_at.parse::<chrono::DateTime<chrono::Utc>>().ok();
                                let end =
                                    ended_at.parse::<chrono::DateTime<chrono::Utc>>().ok();
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

                    vec![
                        run.number.to_string(),
                        status_str,
                        start_time,
                        elapsed_time,
                    ]
                })
                .collect();

            output::table(headers, rows);
        }
        Err(err) => {
            output::tower_error(err);
        }
    }
}

pub async fn do_list_apps(config: Config) {
    let api_config = &config.into();
    let params = ListAppsParams {
        query: None,
        page: None,
        page_size: None,
        period: None,
        num_runs: None,
        status: None,
    };

    let resp = handle_api_response(|| default_api::list_apps(&api_config, params)).await;

    match resp {
        Ok(resp) => {
            let items = resp
                .apps
                .into_iter()
                .map(|app_summary| {
                    let app = app_summary.app;
                    let desc = if app.short_description.is_empty() {
                        "No description".white().dimmed().italic()
                    } else {
                        app.short_description.normal().clear()
                    };
                    format!("{}\n{}", app.name.bold().green(), desc)
                })
                .collect();
            output::list(items);
        },
        Err(err) => {
            output::tower_error(err);
        }
    }
}

pub async fn do_create_app(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("App name (--name) is required");
    });

    let description = args.get_one::<String>("description").unwrap();

    with_spinner(
        "Creating app",
        default_api::create_apps(
            &config.into(),
            CreateAppsParams {
                create_app_params: CreateAppParams {
                    schema: None,
                    name: name.clone(),
                    short_description: Some(description.clone()),
                },
            },
        ),
    )
    .await;

    output::success(&format!("App '{}' created", name));
}

pub async fn do_delete_app(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap();

    with_spinner(
        "Deleting app...",
        default_api::delete_app(
            &config.into(),
            DeleteAppParams {
                name: name.to_string(),
            },
        ),
    ).await;

    output::success(&format!("App '{}' deleted", name));
}

/// Extract app name and run number from command
fn extract_app_run(cmd: Option<(&str, &ArgMatches)>) -> (String, i64) {
    if let Some((name, _)) = cmd {
        if let Some((app, num)) = name.split_once('#') {
            return (
                app.to_string(),
                num.parse::<i64>().unwrap_or_else(|_| {
                    output::die("Run number must be a valid number");
                }),
            );
        }
        output::die("Run number is required (e.g. tower apps logs <app name>#<run number>)");
    }
    output::die("App name (e.g. tower apps logs <app name>#<run number>) is required");
}
