use clap::{value_parser, Arg, ArgMatches, Command};
use config::Config;
use tokio::sync::oneshot;
use tokio::time::{sleep, Duration, Instant};

use tower_api::models::{Run, RunLogLine};

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
const RUN_START_POLL_INTERVAL: Duration = Duration::from_millis(500);
const RUN_START_MESSAGE_DELAY: Duration = Duration::from_secs(3);

async fn follow_logs(config: Config, name: String, seq: i64) {
    let enable_ctrl_c = !output::get_output_mode().is_mcp();
    let mut backoff = FOLLOW_BACKOFF_INITIAL;
    let mut cancel_monitor: Option<oneshot::Sender<()>> = None;
    let mut last_line_num: Option<i64> = None;

    loop {
        let mut run = match api::describe_run(&config, &name, seq).await {
            Ok(res) => res.run,
            Err(err) => output::tower_error_and_die(err, "Fetching run details failed"),
        };

        if is_run_finished(&run) {
            if let Ok(resp) = api::describe_run_logs(&config, &name, seq).await {
                for line in resp.log_lines {
                    emit_log_if_new(&line, &mut last_line_num);
                }
            }
            return;
        }

        if !is_run_started(&run) {
            let wait_started = Instant::now();
            let mut notified = false;
            loop {
                sleep(RUN_START_POLL_INTERVAL).await;
                // Avoid blank output on slow starts while keeping fast starts quiet.
                if should_notify_run_wait(notified, wait_started.elapsed()) {
                    output::write("Waiting for run to start...\n");
                    notified = true;
                }
                run = match api::describe_run(&config, &name, seq).await {
                    Ok(res) => res.run,
                    Err(err) => output::tower_error_and_die(err, "Fetching run details failed"),
                };
                if is_run_finished(&run) {
                    if let Ok(resp) = api::describe_run_logs(&config, &name, seq).await {
                        for line in resp.log_lines {
                            emit_log_if_new(&line, &mut last_line_num);
                        }
                    }
                    return;
                }
                if is_run_started(&run) {
                    break;
                }
            }
        }

        // Cancel any prior watcher so we don't accumulate pollers after reconnects.
        if let Some(cancel) = cancel_monitor.take() {
            let _ = cancel.send(());
        }
        let (cancel_tx, cancel_rx) = oneshot::channel();
        cancel_monitor = Some(cancel_tx);
        let run_complete = monitor_run_completion(&config, &name, seq, cancel_rx);
        match api::stream_run_logs(&config, &name, seq).await {
            Ok(log_stream) => {
                // Reset after a successful connection so transient drops recover quickly.
                backoff = FOLLOW_BACKOFF_INITIAL;
                match stream_logs_until_complete(
                    log_stream,
                    run_complete,
                    enable_ctrl_c,
                    &run.dollar_link,
                    &mut last_line_num,
                )
                .await
                {
                    Ok(LogFollowOutcome::Completed) => {
                        if let Some(cancel) = cancel_monitor.take() {
                            let _ = cancel.send(());
                        }
                        return;
                    }
                    Ok(LogFollowOutcome::Interrupted) => {
                        if let Some(cancel) = cancel_monitor.take() {
                            let _ = cancel.send(());
                        }
                        return;
                    }
                    Ok(LogFollowOutcome::Disconnected) => {}
                    Err(_) => {
                        if let Some(cancel) = cancel_monitor.take() {
                            let _ = cancel.send(());
                        }
                        return;
                    }
                }
            }
            Err(err) => {
                if is_fatal_stream_error(&err) {
                    output::error(&format!("Failed to stream run logs: {}", err));
                    return;
                }
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
    last_line_num: &mut Option<i64>,
) -> Result<LogFollowOutcome, crate::Error> {
    loop {
        tokio::select! {
            event = log_stream.recv() => match event {
                Some(api::LogStreamEvent::EventLog(log)) => {
                    emit_log_if_new(&log, last_line_num);
                },
                Some(api::LogStreamEvent::EventWarning(warning)) => {
                    output::write(&format!("Warning: {}\n", warning.data.content));
                }
                None => return Ok(LogFollowOutcome::Disconnected),
            },
            res = &mut run_complete => {
                match res {
                    Ok(_) => {
                        drain_remaining_logs(log_stream, last_line_num).await;
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

async fn drain_remaining_logs(
    mut log_stream: tokio::sync::mpsc::Receiver<api::LogStreamEvent>,
    last_line_num: &mut Option<i64>,
) {
    let _ = tokio::time::timeout(LOG_DRAIN_DURATION, async {
        while let Some(event) = log_stream.recv().await {
            match event {
                api::LogStreamEvent::EventLog(log) => {
                    emit_log_if_new(&log, last_line_num);
                }
                api::LogStreamEvent::EventWarning(warning) => {
                    output::write(&format!("Warning: {}\n", warning.data.content));
                }
            }
        }
    })
    .await;
}

fn emit_log_if_new(log: &RunLogLine, last_line_num: &mut Option<i64>) {
    if should_emit_line(last_line_num, log.line_num) {
        output::remote_log_event(log);
    }
}

fn should_emit_line(last_line_num: &mut Option<i64>, line_num: i64) -> bool {
    if last_line_num.map_or(true, |last| line_num > last) {
        *last_line_num = Some(line_num);
        true
    } else {
        false
    }
}

fn is_fatal_stream_error(err: &api::LogStreamError) -> bool {
    match err {
        api::LogStreamError::Reqwest(reqwest_err) => reqwest_err
            .status()
            .map(|status| status.is_client_error() && status.as_u16() != 429)
            .unwrap_or(false),
        api::LogStreamError::Unknown => false,
    }
}

fn monitor_run_completion(
    config: &Config,
    app_name: &str,
    seq: i64,
    mut cancel: oneshot::Receiver<()>,
) -> oneshot::Receiver<Run> {
    let (tx, rx) = oneshot::channel();
    let config_clone = config.clone();
    let app_name = app_name.to_string();

    tokio::spawn(async move {
        let mut failures = 0;
        loop {
            tokio::select! {
                _ = &mut cancel => return,
                result = api::describe_run(&config_clone, &app_name, seq) => match result {
                    Ok(res) => {
                        failures = 0;
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
                },
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

fn is_run_started(run: &Run) -> bool {
    match run.status {
        tower_api::models::run::Status::Scheduled | tower_api::models::run::Status::Pending => {
            false
        }
        _ => true,
    }
}

fn should_notify_run_wait(already_notified: bool, elapsed: Duration) -> bool {
    !already_notified && elapsed >= RUN_START_MESSAGE_DELAY
}

#[cfg(test)]
mod tests {
    use super::is_run_finished;
    use super::{
        apps_cmd, is_run_started, next_backoff, should_emit_line, should_notify_run_wait,
        stream_logs_until_complete, LogFollowOutcome, FOLLOW_BACKOFF_INITIAL, FOLLOW_BACKOFF_MAX,
    };
    use tokio::sync::{mpsc, oneshot};
    use tokio::time::Duration;
    use tower_api::models::run::Status;
    use tower_api::models::Run;

    #[test]
    fn test_follow_flag_parsing() {
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
    fn test_terminal_statuses_explicit() {
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
    fn test_status_variants_exhaustive() {
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

    #[test]
    fn test_run_started_statuses() {
        let not_started = [Status::Scheduled, Status::Pending];
        for status in not_started {
            let run = Run {
                status,
                ..Default::default()
            };
            assert!(!is_run_started(&run));
        }

        let started = [
            Status::Running,
            Status::Crashed,
            Status::Errored,
            Status::Exited,
            Status::Cancelled,
        ];
        for status in started {
            let run = Run {
                status,
                ..Default::default()
            };
            assert!(is_run_started(&run));
        }
    }

    #[test]
    fn test_run_wait_notification_logic() {
        assert!(!should_notify_run_wait(
            true,
            super::RUN_START_MESSAGE_DELAY
        ));
        assert!(!should_notify_run_wait(
            false,
            super::RUN_START_MESSAGE_DELAY - Duration::from_millis(1)
        ));
        assert!(should_notify_run_wait(
            false,
            super::RUN_START_MESSAGE_DELAY
        ));
    }

    #[tokio::test]
    async fn test_stream_completion_on_run_finish() {
        let (tx, rx) = mpsc::channel(1);
        let (done_tx, done_rx) = oneshot::channel();
        let mut last_line_num = None;

        let done_task = tokio::spawn(async move {
            let _ = done_tx.send(Run::default());
            tokio::time::sleep(Duration::from_millis(10)).await;
            drop(tx);
        });

        let res = stream_logs_until_complete(rx, done_rx, false, "link", &mut last_line_num).await;
        done_task.await.unwrap();

        assert!(matches!(res, Ok(LogFollowOutcome::Completed)));
    }

    #[tokio::test]
    async fn test_stream_disconnection_on_close() {
        let (tx, rx) = mpsc::channel(1);
        drop(tx);
        let (_done_tx, done_rx) = oneshot::channel::<Run>();
        let mut last_line_num = None;

        let res = stream_logs_until_complete(rx, done_rx, false, "link", &mut last_line_num).await;

        assert!(matches!(res, Ok(LogFollowOutcome::Disconnected)));
    }

    #[test]
    fn test_backoff_growth_and_cap() {
        let mut backoff = FOLLOW_BACKOFF_INITIAL;
        backoff = next_backoff(backoff);
        assert_eq!(backoff, Duration::from_secs(1));
        backoff = next_backoff(backoff);
        assert_eq!(backoff, Duration::from_secs(2));
        backoff = next_backoff(backoff);
        assert_eq!(backoff, Duration::from_secs(4));
        backoff = next_backoff(backoff);
        assert_eq!(backoff, FOLLOW_BACKOFF_MAX);
        backoff = next_backoff(backoff);
        assert_eq!(backoff, FOLLOW_BACKOFF_MAX);
    }

    #[test]
    fn test_duplicate_line_filtering() {
        let mut last_line_num = None;
        assert!(should_emit_line(&mut last_line_num, 1));
        assert_eq!(last_line_num, Some(1));
        assert!(!should_emit_line(&mut last_line_num, 1));
        assert_eq!(last_line_num, Some(1));
        assert!(!should_emit_line(&mut last_line_num, 0));
        assert_eq!(last_line_num, Some(1));
        assert!(should_emit_line(&mut last_line_num, 2));
        assert_eq!(last_line_num, Some(2));
        assert!(should_emit_line(&mut last_line_num, 10));
        assert_eq!(last_line_num, Some(10));
    }

    #[test]
    fn test_out_of_order_log_handling() {
        let mut last_line_num = None;
        assert!(should_emit_line(&mut last_line_num, 1));
        assert_eq!(last_line_num, Some(1));
        assert!(should_emit_line(&mut last_line_num, 3));
        assert_eq!(last_line_num, Some(3));
        assert!(!should_emit_line(&mut last_line_num, 2));
        assert_eq!(last_line_num, Some(3));
        assert!(should_emit_line(&mut last_line_num, 4));
        assert_eq!(last_line_num, Some(4));
    }
}
