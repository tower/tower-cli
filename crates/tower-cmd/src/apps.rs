use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;

use tower_api::apis::default_api::{
    self, CreateAppsParams, DeleteAppParams, DescribeAppParams, DescribeAppSuccess,
    GetAppRunLogsParams, GetAppRunLogsSuccess, ListAppsParams, ListAppsSuccess,
};

use tower_api::models::{CreateAppParams, Run};

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
    let api_config = config.get_api_configuration().unwrap();
    let (app_name, seq) = if let Some((name, _)) = cmd {
        if let Some((app, num)) = name.split_once('#') {
            (
                app.to_string(),
                num.parse::<i64>().unwrap_or_else(|_| {
                    output::die("Run number must be a valid number");
                }),
            )
        } else {
            output::die("Run number is required (e.g. tower apps logs <app name>#<run number>)");
        }
    } else {
        output::die("App name (e.g. tower apps logs <app name>#<run number>) is required");
    };

    let mut spinner = output::spinner("Fetching logs...");

    match default_api::get_app_run_logs(
        api_config,
        GetAppRunLogsParams {
            name: app_name,
            seq,
        },
    )
    .await
    {
        Ok(response) => {
            spinner.success();
            if let GetAppRunLogsSuccess::Status200(logs) = response.entity.unwrap() {
                for line in logs.log_lines {
                    output::log_line(&line.timestamp, &line.message, output::LogLineType::Remote);
                }
            }
        }
        Err(err) => {
            spinner.failure();
            if let tower_api::apis::Error::ResponseError(err) = &err {
                output::failure(&format!("{}: {}", err.status, err.content));
            } else {
                output::failure(&format!("Unexpected error: {}", err));
            }
        }
    }
}

pub async fn do_show_app(config: Config, cmd: Option<(&str, &ArgMatches)>) {
    let api_config = config.get_api_configuration().unwrap();
    let name = cmd.map(|(name, _)| name).unwrap_or_else(|| {
        output::die("App name (e.g. tower apps show <app name>) is required");
    });

    match default_api::describe_app(
        api_config,
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
    let api_config = config.get_api_configuration().unwrap();
    match default_api::list_apps(
        api_config,
        ListAppsParams {
            query: None,
            page: None,
            page_size: None,
            period: None,
            num_runs: None,
            status: None,
        },
    )
    .await
    {
        Ok(response) => {
            if let ListAppsSuccess::Status200(list_response) = response.entity.unwrap() {
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
            }
        }
        Err(err) => {
            if let tower_api::apis::Error::ResponseError(err) = err {
                output::failure(&format!("{}: {}", err.status, err.content));
            } else {
                output::failure(&format!("Unexpected error: {}", err));
            }
        }
    }
}

pub async fn do_create_app(config: Config, args: &ArgMatches) {
    let api_config = config.get_api_configuration().unwrap();
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("App name (--name) is required");
    });

    let description = args.get_one::<String>("description").unwrap();

    let mut spinner = output::Spinner::new("Creating app".to_string());

    match default_api::create_apps(
        api_config,
        CreateAppsParams {
            create_app_params: CreateAppParams {
                schema: None,
                name: name.clone(),
                short_description: Some(description.clone()),
            },
        },
    )
    .await
    {
        Ok(_) => {
            spinner.success();
            output::success(&format!("App '{}' created", name));
        }
        Err(err) => {
            spinner.failure();
            if let tower_api::apis::Error::ResponseError(err) = err {
                output::failure(&format!("{}: {}", err.status, err.content));
            } else {
                output::failure(&format!("Unexpected error: {}", err));
            }
        }
    }
}

pub async fn do_delete_app(config: Config, cmd: Option<(&str, &ArgMatches)>) {
    let api_config = config.get_api_configuration().unwrap();
    let name = cmd.map(|(name, _)| name).unwrap_or_else(|| {
        output::die("App name (e.g. tower apps delete <app name>) is required");
    });

    let mut spinner = output::Spinner::new("Deleting app...".to_string());

    match default_api::delete_app(
        api_config,
        DeleteAppParams {
            name: name.to_string(),
        },
    )
    .await
    {
        Ok(_) => {
            spinner.success();
            output::success(&format!("App '{}' deleted", name));
        }
        Err(err) => {
            spinner.failure();
            if let tower_api::apis::Error::ResponseError(err) = err {
                output::failure(&format!("{}: {}", err.status, err.content));
            } else {
                output::failure(&format!("Unexpected error: {}", err));
            }
        }
    }
}
