use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use tower_api::apis::Error as ApiError;
use std::future::Future;

use tower_api::{
    models::{CreateAppParams, Run},
    apis::default_api::{
        self, CreateAppsParams, DeleteAppParams, DescribeAppParams, DescribeAppSuccess,
        GetAppRunLogsParams, GetAppRunLogsSuccess, ListAppsParams, ListAppsSuccess,
    },
};

use crate::output;

pub fn apps_cmd() -> Command {
    Command::new("apps")
        .about("Interact with the apps that you own")
        .arg_required_else_help(true)
        .subcommand(Command::new("list").about("List all of your apps`"))
        .subcommand(
            Command::new("show")
                .allow_external_subcommands(true)
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
                        .long("name")
                        .value_parser(value_parser!(String))
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
                .about("Delete an app in Tower"),
        )
}

pub async fn do_logs_app(config: Config, cmd: Option<(&str, &ArgMatches)>) {
    let (app_name, seq) = extract_app_run(cmd);
    
    let response = with_spinner(
        "Fetching logs...",
        default_api::get_app_run_logs(
            &config.into(),
            GetAppRunLogsParams { name: app_name.clone(), seq },
        ),
        Some(&app_name)
    ).await;

    if let GetAppRunLogsSuccess::Status200(logs) = response.entity.unwrap() {
        for line in logs.log_lines {
            output::log_line(&line.timestamp, &line.message, output::LogLineType::Remote);
        }
    }
}

pub async fn do_show_app(config: Config, cmd: Option<(&str, &ArgMatches)>) {
    let name = cmd.map(|(name, _)| name).unwrap_or_else(|| {
        output::die("App name (e.g. tower apps show <app name>) is required");
    });

    match default_api::describe_app(
        &config.into(),
        DescribeAppParams {
            name: name.to_string(),
            runs: Some(5),
        },
    )
    .await
    {
        Ok(response) => {
            if let DescribeAppSuccess::Status200(app_response) = response.entity.unwrap() {
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
                            status.to_string(),
                            start_time,
                            elapsed_time,
                        ]
                    })
                    .collect();

                output::table(headers, rows);
            }
        }
        Err(err) => {
            if let tower_api::apis::Error::ResponseError(err) = err {
                if err.status == 404 {
                    output::failure(&format!("The app name {} was not found!", name));
                } else {
                    output::failure(&format!("{}: {}", err.status, err.content));
                }
            } else {
                output::failure(&format!("Unexpected error: {}", err));
            }
        }
    }
}

pub async fn do_list_apps(config: Config) {
    let resp =  handle_api_result(None, default_api::list_apps(
        &config.into(),
        ListAppsParams {
            query: None,
            page: None,
            page_size: None,
            period: None,
            num_runs: None,
            status: None,
        },
    )).await;

    if let ListAppsSuccess::Status200(list_response) = resp.entity.unwrap() {
        let items = list_response
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
    } else {
        // This is most likely the case that there are no apps! So do nothing at all.
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
        Some(name)
    ).await;

    output::success(&format!("App '{}' created", name));
}

pub async fn do_delete_app(config: Config, cmd: Option<(&str, &ArgMatches)>) {
    let name = cmd.map(|(name, _)| name).unwrap_or_else(|| {
        output::die("App name (e.g. tower apps delete <app name>) is required");
    });

    with_spinner(
        "Deleting app...",
        default_api::delete_app(
            &config.into(),
            DeleteAppParams {
                name: name.to_string(),
            },
        ),
        Some(name)
    ).await;

    output::success(&format!("App '{}' deleted", name));
}

/// Helper function to handle common API error patterns
async fn handle_api_result<T, F, V>(spinner: Option<&mut output::Spinner>, operation: F) -> T 
where
    F: Future<Output = Result<T, tower_api::apis::Error<V>>>,
{
    match operation.await {
        Ok(result) => result,
        Err(err) => {
            if let Some(spinner) = spinner {
                spinner.failure();
            }

            match err {
                ApiError::ResponseError(err) => {
                    output::failure(&format!("{}: {}", err.status, err.content));
                    std::process::exit(1);
                }
                _ => {
                    log::debug!("Unexpected error: {}", err);
                    output::failure("The Tower API returned an unexpected error!");
                    std::process::exit(1);
                }
            }
        }
    }
}

/// Helper function to handle operations with spinner
async fn with_spinner<T, F, V>(
    message: &str, 
    operation: F,
    resource_name: Option<&str>
) -> T 
where
    F: Future<Output = Result<T, tower_api::apis::Error<V>>>,
{
    let mut spinner = output::spinner(message);
    match operation.await {
        Ok(result) => {
            spinner.success();
            result
        }
        Err(err) => {
            spinner.failure();
            match err {
                ApiError::ResponseError(err) => {
                    // Check for 404 Not Found errors and provide a more user-friendly message
                    if err.status == 404 {
                        // Extract the resource type from the message
                        let resource_type = message
                            .trim_end_matches("...")
                            .trim_start_matches("Fetching ")
                            .trim_start_matches("Creating ")
                            .trim_start_matches("Updating ")
                            .trim_start_matches("Deleting ");
                        
                        if let Some(name) = resource_name {
                            output::failure(&format!("{} '{}' not found", resource_type, name));
                        } else {
                            output::failure(&format!("The {} was not found", resource_type));
                        }
                    } else {
                        output::failure(&format!("{}: {}", err.status, err.content));
                    }
                    std::process::exit(1);
                }
                _ => {
                    output::failure(&format!("Unexpected error: {}", err));
                    std::process::exit(1);
                }
            }
        }
    }
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
            )
        }
        output::die("Run number is required (e.g. tower apps logs <app name>#<run number>)");
    }
    output::die("App name (e.g. tower apps logs <app name>#<run number>) is required");
}
