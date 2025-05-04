use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;

use tower_api::models::Run;

use crate::{
    output,
    api,
};

pub fn apps_cmd() -> Command {
    Command::new("apps")
        .about("Manage the apps in your current Tower account")
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
                        .short('n')
                        .long("name")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("slug")
                        .short('s')
                        .long("slug")
                        .value_parser(value_parser!(String))
                        .default_value("")
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

pub async fn do_logs(config: Config, cmd: &ArgMatches) {
    let (slug, seq) = extract_app_slug_and_run("logs", cmd.subcommand());

    if let Ok(resp) = api::describe_run_logs(&config, &slug, seq).await {
        for line in resp.log_lines {
            output::log_line(&line.timestamp, &line.message, output::LogLineType::Remote);
        }
    }
}

pub async fn do_show(config: Config, cmd: &ArgMatches) {
    let slug = extract_app_slug("show", cmd.subcommand());

    match  api::describe_app(&config, &slug).await {
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
    let resp = api::list_apps(&config).await;

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

pub async fn do_create(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("App name (--name) is required");
    });

    let slug = args.get_one::<String>("slug").unwrap();

    let description = args.get_one::<String>("description").unwrap();
    let mut spinner = output::spinner("Creating app");

    if let Err(err) = api::create_app(&config, name, slug, description).await {
        spinner.failure();
        output::tower_error(err);
    } else {
        spinner.success();
        output::success(&format!("App '{}' created", name));
    }

}

pub async fn do_delete(config: Config, cmd: &ArgMatches) {
    let slug = extract_app_slug("delete", cmd.subcommand());
    let mut spinner = output::spinner("Deleting app");

    if let Err(err) = api::delete_app(&config, &slug).await {
        spinner.failure();
        output::tower_error(err);
    } else {
        spinner.success();
    }
}

/// Extract app name and run number from command
fn extract_app_slug_and_run(subcmd: &str, cmd: Option<(&str, &ArgMatches)>) -> (String, i64) {
    if let Some((slug, _)) = cmd {
        if let Some((slug, num)) = slug.split_once('#') {
            return (
                slug.to_string(),
                num.parse::<i64>().unwrap_or_else(|_| {
                    output::die("Run number must be an actual number");
                }),
            );
        }

        let line = format!("Run number is required. Example: tower apps {} <app name>#<run number>", subcmd);
        output::die(&line);
    }
    let line = format!("App slug is required. Example: tower apps {} <app name>#<run number>", subcmd);
    output::die(&line)
}

fn extract_app_slug(subcmd: &str, cmd: Option<(&str, &ArgMatches)>) -> String {
    if let Some((slug, _)) = cmd {
        return slug.to_string();
    }

    let line = format!("App slug is required. Example: tower apps {} <app name>", subcmd);
    output::die(&line);
}
