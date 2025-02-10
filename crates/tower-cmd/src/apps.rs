use colored::Colorize;
use clap::{value_parser, Arg, ArgMatches, Command};
use config::Config;

use tower_api::apis::{
    configuration::Configuration,
    default_api::{self, ListAppsParams, CreateAppsParams, DeleteAppParams, DescribeAppParams, GetAppRunLogsParams},
};

use crate::output;

pub fn apps_cmd() -> Command {
    Command::new("apps")
        .about("Interact with the apps that you own")
        .arg_required_else_help(true)
        .subcommand(
            Command::new("list")
                .about("List all of your apps`")
        )
        .subcommand(
            Command::new("show")
                .allow_external_subcommands(true)
                .about("Show the details about an app in Tower")
        )
        .subcommand(
            Command::new("logs")
                .allow_external_subcommands(true)
                .about("Get the logs from a previous Tower app run")
        )
        .subcommand(
            Command::new("create")
                .arg(
                    Arg::new("name")
                        .long("name")
                        .value_parser(value_parser!(String))
                        .action(clap::ArgAction::Set)
                )
                .arg(
                    Arg::new("description")
                        .long("description")
                        .value_parser(value_parser!(String))
                        .default_value("")
                        .action(clap::ArgAction::Set)
                )
                .about("Create a new app in Tower")
        )
        .subcommand(
            Command::new("delete")
                .allow_external_subcommands(true)
                .about("Delete an app in Tower")
        )
}

pub async fn do_logs_app(_config: Config, configuration: &Configuration, cmd: Option<(&str, &ArgMatches)>) {
    let (app_name, seq) = if let Some((name, _)) = cmd {
        if let Some((app, num)) = name.split_once('#') {
            (app.to_string(), num.parse::<i64>().unwrap_or_else(|_| {
                output::die("Run number must be a valid number");
            }))
        } else {
            output::die("Run number is required (e.g. tower apps logs <app name>#<run number>)");
        }
    } else {
        output::die("App name (e.g. tower apps logs <app name>#<run number>) is required");
    };

    let mut spinner = output::spinner("Fetching logs...");
    
    match default_api::get_app_run_logs(configuration, GetAppRunLogsParams { name: app_name, seq }).await {
        Ok(response) => {
            spinner.success();
            match response.entity {
                Some(default_api::GetAppRunLogsSuccess::Status200(logs)) => {
                    for line in logs.log_lines {
                        output::log_line(&line.timestamp, &line.message, output::LogLineType::Remote);
                    }
                },
                Some(default_api::GetAppRunLogsSuccess::UnknownValue(value)) => {
                    output::failure(&format!("Received unexpected response format from server: {}", value));
                },
                None => {
                    output::failure("No response received from server");
                }
            }
        },
        Err(err) => {
            spinner.failure();
            output::tower_error(err);
        }
    }
}

pub async fn do_show_app(_config: Config, configuration: &Configuration, cmd: Option<(&str, &ArgMatches)>) {
    let name = cmd.map(|(name, _)| name).unwrap_or_else(|| {
        output::die("App name (e.g. tower apps show <app name>) is required");
    });

    match default_api::describe_app(configuration, DescribeAppParams { 
        name: name.to_string(),
        runs: Some(5) // Get 5 recent runs
    }).await {
        Ok(response) => {
            match response.entity {
                Some(default_api::DescribeAppSuccess::Status200(resp)) => {
                    let app = resp.app;
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
            
                    let headers = vec![
                        "#".yellow().to_string(),
                        "Status".yellow().to_string(),
                        "Start Time".yellow().to_string(),
                        "Elapsed Time".yellow().to_string(),
                    ];

                    let rows = resp.runs.iter().map(|run| {
                    let status = &run.status;

                    // Format start time
                    let start_time = if !run.started_at.is_empty() {
                        run.started_at.clone()
                    } else {
                        format!("Scheduled at {}", run.scheduled_at)
                    };

                    // Calculate elapsed time
                    let elapsed_time = if !run.ended_at.is_empty() {
                        format!("{}s", run.elapsed_time)
                    } else if !run.started_at.is_empty() {
                        format!("Running for {}s", run.elapsed_time)
                    } else {
                        format!("{}s ago", run.elapsed_time)
                    };

                    vec![
                        run.number.to_string(),
                        status.to_string(),
                        start_time,
                        elapsed_time,
                    ]
                }).collect();

                    output::table(headers, rows);
                },
                Some(default_api::DescribeAppSuccess::UnknownValue(value)) => {
                    output::failure(&format!("Received unexpected response format from server: {}", value));
                },
                None => {
                    output::failure("No response received from server");
                }
            }
        },
        Err(err) => {
            output::tower_error(err);
        }
    }
}

pub async fn do_list_apps(_config: Config, configuration: &Configuration) {
    match default_api::list_apps(configuration, ListAppsParams {
        query: None,
        page: None,
        page_size: None,
    }).await {
        Ok(response) => {
            match response.entity {
                Some(default_api::ListAppsSuccess::Status200(resp)) => {
                    let items = resp.apps.into_iter().map(|app| {
                        let desc = if app.short_description.is_empty() {
                            "No description".white().dimmed().italic()
                        } else {
                            app.short_description.normal().clear()
                        };
                        format!("{}\n{}", app.name.bold().green(), desc)
                    }).collect();
                    output::list(items);
                },
                Some(default_api::ListAppsSuccess::UnknownValue(value)) => {
                    output::failure(&format!("Received unexpected response format from server: {}", value));
                },
                None => {
                    output::failure("No response received from server");
                }
            }
        },
        Err(err) => {
            output::tower_error(err);
        }
    }
}

pub async fn do_create_app(_config: Config, configuration: &Configuration, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("App name (--name) is required");
    });

    let description = args.get_one::<String>("description").unwrap();
    let schedule = args.get_one::<String>("schedule").unwrap();

    let mut spinner = output::spinner("Creating app");

    match default_api::create_apps(configuration, CreateAppsParams {
        create_app_params: tower_api::models::CreateAppParams::new(name.clone())
            .with_short_description(Some(description.clone()))
            .with_schedule(Some(schedule.clone()))
    }).await {
        Ok(response) => {
            match response.entity {
                Some(default_api::CreateAppsSuccess::Status200(_)) => {
                    spinner.success();
                    let line = format!("App \"{}\" was created", name);
                    output::success(&line);
                },
                Some(default_api::CreateAppsSuccess::UnknownValue(value)) => {
                    spinner.failure();
                    output::failure(&format!("Received unexpected response format from server: {}", value));
                },
                None => {
                    spinner.failure();
                    output::failure("No response received from server");
                }
            }
        },
        Err(err) => {
            spinner.failure();
            output::tower_error(err);
        }
    }
}

pub async fn do_delete_app(_config: Config, configuration: &Configuration, cmd: Option<(&str, &ArgMatches)>) {
    let name = cmd.map(|(name, _)| name).unwrap_or_else(|| {
        output::die("App name (e.g. tower apps delete <app name>) is required");
    });

    let mut spinner = output::spinner("Deleting app...");

    match default_api::delete_app(configuration, DeleteAppParams {
        name: name.to_string()
    }).await {
        Ok(response) => {
            match response.entity {
                Some(default_api::DeleteAppSuccess::Status200(_)) => {
                    spinner.success();
                    let line = format!("App \"{}\" was deleted", name);
                    output::success(&line);
                },
                Some(default_api::DeleteAppSuccess::UnknownValue(value)) => {
                    spinner.failure();
                    output::failure(&format!("Received unexpected response format from server: {}", value));
                },
                None => {
                    spinner.failure();
                    output::failure("No response received from server");
                }
            }
        },
        Err(err) => {
            spinner.failure();
            output::tower_error(err);
        }
    }
}
