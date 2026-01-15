use clap::{value_parser, Arg, ArgMatches, Command};
use config::Config;
use tokio::sync::oneshot;
use tokio::time::{sleep, Duration};

use tower_api::models::Run;

use crate::{api, output};

pub fn apps_cmd() -> Command {
    Command::new("apps")
        .about("Manage the apps in your current Tower account")
        .arg_required_else_help(true)
        .subcommand(Command::new("list").about("List all of your apps"))
        .subcommand(
            Command::new("show")
                .allow_external_subcommands(true)
                .override_usage("tower apps show [OPTIONS] <APP_NAME>")
                .after_help("Example: tower apps show hello-world")
                .about("Show the details about an app in Tower"),
        )
        .subcommand(
            Command::new("logs")
                .arg(
                    Arg::new("follow")
                        .short('f')
                        .long("follow")
                        .help("Follow logs in real time")
                        .action(clap::ArgAction::SetTrue),
                )
                .allow_external_subcommands(true)
                .override_usage("tower apps logs [OPTIONS] <APP_NAME>#<RUN_NUMBER>")
                .after_help("Example: tower apps logs hello-world#11")
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
                .override_usage("tower apps delete [OPTIONS] <APP_NAME>")
                .after_help("Example: tower apps delete hello-world")
                .about("Delete an app in Tower"),
        )
}

pub async fn do_logs(config: Config, cmd: &ArgMatches) {
    let (name, seq) = extract_app_name_and_run("logs", cmd.subcommand());
    let follow = cmd.get_one::<bool>("follow").copied().unwrap_or(false);

    if follow {
        follow_logs(config, name, seq).await;
        return;
    }

    if let Ok(resp) = api::describe_run_logs(&config, &name, seq).await {
        for line in resp.log_lines {
            output::remote_log_event(&line);
        }
    }
}

pub async fn do_show(config: Config, cmd: &ArgMatches) {
    let name = extract_app_name("show", cmd.subcommand());

    match api::describe_app(&config, &name).await {
        Ok(app_response) => {
            if output::get_output_mode().is_json() {
                output::json(&app_response);
                return;
            }

            let app = &app_response.app;
            let runs = &app_response.runs;

            output::detail("Name", &app.name);
            output::header("Description");
            let line = output::paragraph(&app.short_description);
            output::write(&line);
            output::newline();
            output::newline();
            output::header("Recent runs");

            let headers = vec!["#", "Status", "Start Time", "Elapsed Time"]
                .into_iter()
                .map(|h| h.to_string())
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

            output::table(headers, rows, Some(&app_response));
        }
        Err(err) => output::tower_error_and_die(err, "Fetching app details failed"),
    }
}

pub async fn do_list_apps(config: Config) {
    let resp = output::with_spinner("Listing apps", api::list_apps(&config)).await;

    let items = resp
        .apps
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
    output::list(items, Some(&resp.apps));
}

pub async fn do_create(config: Config, args: &ArgMatches) {
    let name = args.get_one::<String>("name").unwrap_or_else(|| {
        output::die("App name (--name) is required");
    });

    let description = args.get_one::<String>("description").unwrap();

    let app =
        output::with_spinner("Creating app", api::create_app(&config, name, description)).await;

    output::success_with_data(&format!("App '{}' created", name), Some(app));
}

pub async fn do_delete(config: Config, cmd: &ArgMatches) {
    let name = extract_app_name("delete", cmd.subcommand());

    output::with_spinner("Deleting app", api::delete_app(&config, &name)).await;
}

/// Extract app name and run number from command
fn extract_app_name_and_run(subcmd: &str, cmd: Option<(&str, &ArgMatches)>) -> (String, i64) {
    if let Some((name, _)) = cmd {
        if let Some((name, num)) = name.split_once('#') {
            return (
                name.to_string(),
                num.parse::<i64>().unwrap_or_else(|_| {
                    output::die("Run number must be an actual number");
                }),
            );
        }

        let line = format!(
            "Run number is required. Example: tower apps {} <app name>#<run number>",
            subcmd
        );
        output::die(&line);
    }
    let line = format!(
        "App name is required. Example: tower apps {} <app name>#<run number>",
        subcmd
    );
    output::die(&line)
}

fn extract_app_name(subcmd: &str, cmd: Option<(&str, &ArgMatches)>) -> String {
    if let Some((name, _)) = cmd {
        return name.to_string();
    }

    let line = format!(
        "App name is required. Example: tower apps {} <app name>",
        subcmd
    );
    output::die(&line);
}

const FOLLOW_BACKOFF_INITIAL: Duration = Duration::from_millis(500);
const FOLLOW_BACKOFF_MAX: Duration = Duration::from_secs(5);
const LOG_DRAIN_DURATION: Duration = Duration::from_secs(5);

async fn follow_logs(config: Config, name: String, seq: i64) {
    let enable_ctrl_c = !output::get_output_mode().is_mcp();
    let mut backoff = FOLLOW_BACKOFF_INITIAL;

    loop {
        let run = match api::describe_run(&config, &name, seq).await {
            Ok(res) => res.run,
            Err(err) => output::tower_error_and_die(err, "Fetching run details failed"),
        };

        if is_run_finished(&run) {
            if let Ok(resp) = api::describe_run_logs(&config, &name, seq).await {
                for line in resp.log_lines {
                    output::remote_log_event(&line);
                }
            }
            return;
        }

        let run_complete = monitor_run_completion(&config, &name, seq);
        match api::stream_run_logs(&config, &name, seq).await {
            Ok(log_stream) => {
                backoff = FOLLOW_BACKOFF_INITIAL;
                match stream_logs_until_complete(
                    log_stream,
                    run_complete,
                    enable_ctrl_c,
                    &run.dollar_link,
                )
                .await
                {
                    Ok(LogFollowOutcome::Completed) => return,
                    Ok(LogFollowOutcome::Interrupted) => return,
                    Ok(LogFollowOutcome::Disconnected) => {}
                    Err(_) => return,
                }
            }
            Err(err) => {
                output::error(&format!("Failed to stream run logs: {}", err));
                sleep(backoff).await;
                backoff = next_backoff(backoff);
                continue;
            }
        }

        let latest = match api::describe_run(&config, &name, seq).await {
            Ok(res) => res.run,
            Err(err) => output::tower_error_and_die(err, "Fetching run details failed"),
        };
        if is_run_finished(&latest) {
            return;
        }

        sleep(backoff).await;
        backoff = next_backoff(backoff);
    }
}

fn next_backoff(current: Duration) -> Duration {
    let next = current.checked_mul(2).unwrap_or(FOLLOW_BACKOFF_MAX);
    if next > FOLLOW_BACKOFF_MAX {
        FOLLOW_BACKOFF_MAX
    } else {
        next
    }
}

enum LogFollowOutcome {
    Completed,
    Disconnected,
    Interrupted,
}

async fn stream_logs_until_complete(
    mut log_stream: tokio::sync::mpsc::Receiver<api::LogStreamEvent>,
    mut run_complete: oneshot::Receiver<Run>,
    enable_ctrl_c: bool,
    run_link: &str,
) -> Result<LogFollowOutcome, crate::Error> {
    loop {
        tokio::select! {
            event = log_stream.recv() => match event {
                Some(api::LogStreamEvent::EventLog(log)) => {
                    output::remote_log_event(&log);
                },
                None => return Ok(LogFollowOutcome::Disconnected),
                _ => {},
            },
            res = &mut run_complete => {
                match res {
                    Ok(_) => {
                        drain_remaining_logs(log_stream).await;
                        return Ok(LogFollowOutcome::Completed);
                    }
                    // If monitoring failed, keep following and let the caller retry.
                    Err(_) => return Ok(LogFollowOutcome::Disconnected),
                }
            },
            _ = tokio::signal::ctrl_c(), if enable_ctrl_c => {
                output::write("Received Ctrl+C, stopping log streaming...\n");
                output::write("Note: The run will continue in Tower cloud\n");
                output::write(&format!("  See more: {}\n", run_link));
                return Ok(LogFollowOutcome::Interrupted);
            },
        }
    }
}

async fn drain_remaining_logs(mut log_stream: tokio::sync::mpsc::Receiver<api::LogStreamEvent>) {
    let _ = tokio::time::timeout(LOG_DRAIN_DURATION, async {
        while let Some(event) = log_stream.recv().await {
            if let api::LogStreamEvent::EventLog(log) = event {
                output::remote_log_event(&log);
            }
        }
    })
    .await;
}

fn monitor_run_completion(
    config: &Config,
    app_name: &str,
    seq: i64,
) -> oneshot::Receiver<Run> {
    let (tx, rx) = oneshot::channel();
    let config_clone = config.clone();
    let app_name = app_name.to_string();

    tokio::spawn(async move {
        let mut failures = 0u32;
        loop {
            match api::describe_run(&config_clone, &app_name, seq).await {
                Ok(res) => {
                    if is_run_finished(&res.run) {
                        let _ = tx.send(res.run);
                        return;
                    }
                }
                Err(_) => {
                    failures += 1;
                    if failures >= 5 {
                        output::error(
                            "Failed to monitor run completion after repeated errors",
                        );
                        return;
                    }
                }
            }
            sleep(Duration::from_millis(500)).await;
        }
    });

    rx
}

fn is_run_finished(run: &Run) -> bool {
    match run.status {
        // Be explicit about terminal states so new non-terminal statuses
        // don't cause us to stop following logs too early.
        tower_api::models::run::Status::Crashed
        | tower_api::models::run::Status::Errored
        | tower_api::models::run::Status::Exited
        | tower_api::models::run::Status::Cancelled => true,
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::{apps_cmd, next_backoff, stream_logs_until_complete, LogFollowOutcome};
    use super::is_run_finished;
    use tokio::sync::{mpsc, oneshot};
    use tokio::time::Duration;
    use tower_api::models::run::Status;
    use tower_api::models::Run;

    #[test]
    fn logs_follow_flag_is_parsed() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "logs", "--follow", "hello-world#11"])
            .unwrap();
        let (cmd, sub_matches) = matches.subcommand().unwrap();

        assert_eq!(cmd, "logs");
        assert_eq!(sub_matches.get_one::<bool>("follow"), Some(&true));
        assert_eq!(
            sub_matches.subcommand().map(|(name, _)| name),
            Some("hello-world#11")
        );
    }

    #[test]
    fn run_status_terminality_is_explicit() {
        let non_terminal = [Status::Scheduled, Status::Pending, Status::Running];
        for status in non_terminal {
            let run = Run {
                status,
                ..Default::default()
            };
            assert!(!is_run_finished(&run));
        }

        let terminal = [
            Status::Crashed,
            Status::Errored,
            Status::Exited,
            Status::Cancelled,
        ];
        for status in terminal {
            let run = Run {
                status,
                ..Default::default()
            };
            assert!(is_run_finished(&run));
        }
    }

    #[test]
    fn run_status_variants_are_exhaustive() {
        let status = Status::Scheduled;
        match status {
            Status::Scheduled => {}
            Status::Pending => {}
            Status::Running => {}
            Status::Crashed => {}
            Status::Errored => {}
            Status::Exited => {}
            Status::Cancelled => {}
        }
    }

    #[tokio::test]
    async fn stream_logs_completes_on_run_completion() {
        let (tx, rx) = mpsc::channel(1);
        let (done_tx, done_rx) = oneshot::channel();

        let done_task = tokio::spawn(async move {
            let _ = done_tx.send(Run::default());
            tokio::time::sleep(Duration::from_millis(10)).await;
            drop(tx);
        });

        let res = stream_logs_until_complete(rx, done_rx, false, "link").await;
        done_task.await.unwrap();

        assert!(matches!(res, Ok(LogFollowOutcome::Completed)));
    }

    #[tokio::test]
    async fn stream_logs_returns_disconnected_on_closed_stream() {
        let (tx, rx) = mpsc::channel(1);
        drop(tx);
        let (_done_tx, done_rx) = oneshot::channel::<Run>();

        let res = stream_logs_until_complete(rx, done_rx, false, "link").await;

        assert!(matches!(res, Ok(LogFollowOutcome::Disconnected)));
    }

    #[test]
    fn backoff_grows_and_caps() {
        let mut backoff = Duration::from_millis(500);
        backoff = next_backoff(backoff);
        assert_eq!(backoff, Duration::from_secs(1));
        backoff = next_backoff(backoff);
        assert_eq!(backoff, Duration::from_secs(2));
        backoff = next_backoff(backoff);
        assert_eq!(backoff, Duration::from_secs(4));
        backoff = next_backoff(backoff);
        assert_eq!(backoff, Duration::from_secs(5));
        backoff = next_backoff(backoff);
        assert_eq!(backoff, Duration::from_secs(5));
    }
}
