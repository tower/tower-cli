use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use std::time::Duration;
use tokio::sync::oneshot;
use tokio::time::{sleep, timeout, Instant};

use tower_api::models::run::Status as RunStatus;
use tower_api::models::Run;
use tower_telemetry::debug;

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
                .override_usage("tower apps show [OPTIONS] <APP_NAME>")
                .after_help("Example:\n  tower apps show hello-world")
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
                .arg(
                    Arg::new("follow")
                        .short('f')
                        .long("follow")
                        .help("Follow the logs of the run in real time")
                        .action(clap::ArgAction::SetTrue),
                )
                .override_usage("tower apps logs [OPTIONS] <APP_NAME>#<RUN_NUMBER>")
                .after_help(
                    "Examples:\n  \
                     tower apps logs hello-world#11              Show the stored logs of run 11\n  \
                     tower apps logs hello-world 11              Same, with a separate run number\n  \
                     tower apps logs hello-world --follow        Follow the latest run in real time",
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
                .override_usage("tower apps delete [OPTIONS] <APP_NAME>")
                .after_help("Example:\n  tower apps delete hello-world")
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

    if cmd.get_flag("follow") {
        follow_run_logs(out, &config, &name, seq).await;
        return;
    }

    if let Ok(resp) = api::describe_run_logs(&config, &name, seq).await {
        for line in resp.log_lines {
            out.remote_log_event(&line);
        }
    }
}

/// How often the run's status is polled, both while waiting for it to start
/// and while monitoring for completion during streaming.
const STATUS_POLL_INTERVAL: Duration = Duration::from_millis(500);

/// How long to wait quietly before printing the "Waiting for run to start..."
/// notice, so fast starts stay quiet but a slow start isn't a silent hang.
const WAIT_NOTICE_AFTER: Duration = Duration::from_secs(3);

/// How long to wait for a run to start before giving up.
const WAIT_FOR_START_TIMEOUT: Duration = Duration::from_secs(30);

/// Grace window after the run completes for the stream to deliver any
/// remaining buffered lines.
const STREAM_DRAIN_GRACE: Duration = Duration::from_secs(5);

/// Consecutive status-check failures tolerated before completion monitoring
/// gives up (without killing an otherwise healthy stream).
const MAX_STATUS_CHECK_FAILURES: u32 = 5;

/// The three groups a run status can fall into for follow purposes. The
/// grouping is deliberately conservative: only known-final statuses are
/// terminal, only known pre-start statuses count as not started, and anything
/// else — including statuses introduced after this code was written — counts
/// as in progress so a follow doesn't silently end early.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum RunPhase {
    Terminal,
    NotStarted,
    InProgress,
}

fn run_phase(status: &RunStatus) -> RunPhase {
    match status {
        RunStatus::Crashed | RunStatus::Errored | RunStatus::Exited | RunStatus::Cancelled => {
            RunPhase::Terminal
        }
        RunStatus::Scheduled | RunStatus::Pending | RunStatus::Starting => RunPhase::NotStarted,
        _ => RunPhase::InProgress,
    }
}

/// Tracks the highest log line number printed so far, so a line is never
/// printed twice across reconnects and the final catch-up fetch. Log line
/// numbers increase monotonically, so anything at or below the highest number
/// already printed is a repeat (or out of order) and is dropped.
struct LineTracker {
    highest: Option<i64>,
}

impl LineTracker {
    fn new() -> Self {
        Self { highest: None }
    }

    /// Returns true when the line should be printed, updating the high-water
    /// mark; false when it's a duplicate or out-of-order line.
    fn accept(&mut self, line_num: i64) -> bool {
        match self.highest {
            Some(highest) if line_num <= highest => false,
            _ => {
                self.highest = Some(line_num);
                true
            }
        }
    }
}

/// Exponential reconnect backoff: starts at 500ms, doubles per attempt, caps
/// at 5s, and resets to the initial delay after any successful connection.
struct Backoff {
    current: Duration,
}

impl Backoff {
    const INITIAL: Duration = Duration::from_millis(500);
    const MAX: Duration = Duration::from_secs(5);

    fn new() -> Self {
        Self {
            current: Self::INITIAL,
        }
    }

    fn next_delay(&mut self) -> Duration {
        let delay = self.current;
        self.current = std::cmp::min(self.current * 2, Self::MAX);
        delay
    }

    fn reset(&mut self) {
        self.current = Self::INITIAL;
    }
}

async fn describe_run_or_die(out: &output::Out, config: &Config, name: &str, seq: i64) -> Run {
    match api::describe_run(config, name, seq).await {
        Ok(resp) => resp.run,
        Err(err) => out.tower_error_and_die(err, "Fetching run details failed"),
    }
}

/// Prints the stored logs of a run, skipping anything already printed.
async fn print_stored_logs(
    out: &output::Out,
    config: &Config,
    name: &str,
    seq: i64,
    tracker: &mut LineTracker,
) {
    match api::describe_run_logs(config, name, seq).await {
        Ok(resp) => {
            for line in resp.log_lines {
                if tracker.accept(line.line_num) {
                    out.remote_log_event(&line);
                }
            }
        }
        Err(err) => out.tower_error_and_die(err, "Fetching run logs failed"),
    }
}

enum WaitOutcome {
    Started,
    Finished,
    TimedOut,
}

/// Polls the run until it starts, finishes, or the wait times out. Prints a
/// single informational notice if the wait takes longer than a few seconds.
async fn wait_for_run_start(
    out: &output::Out,
    config: &Config,
    name: &str,
    seq: i64,
) -> WaitOutcome {
    let started_waiting = Instant::now();
    let mut printed_notice = false;

    loop {
        if started_waiting.elapsed() >= WAIT_FOR_START_TIMEOUT {
            return WaitOutcome::TimedOut;
        }

        if !printed_notice && started_waiting.elapsed() >= WAIT_NOTICE_AFTER {
            out.write("Waiting for run to start...\n");
            printed_notice = true;
        }

        sleep(STATUS_POLL_INTERVAL).await;

        let run = describe_run_or_die(out, config, name, seq).await;
        match run_phase(&run.status) {
            RunPhase::Terminal => return WaitOutcome::Finished,
            RunPhase::InProgress => return WaitOutcome::Started,
            RunPhase::NotStarted => {}
        }
    }
}

/// Watches the run's status in the background and resolves the returned
/// channel when it reaches a terminal state. If the status check fails several
/// times in a row, monitoring is abandoned (with a diagnostic) and the channel
/// closes without resolving, so the stream itself keeps running.
fn spawn_completion_monitor(
    out: output::Out,
    config: Config,
    name: String,
    seq: i64,
) -> oneshot::Receiver<()> {
    let (tx, rx) = oneshot::channel();

    tokio::spawn(async move {
        let mut failures: u32 = 0;

        loop {
            match api::describe_run(&config, &name, seq).await {
                Ok(resp) => {
                    failures = 0;
                    if run_phase(&resp.run.status) == RunPhase::Terminal {
                        let _ = tx.send(());
                        return;
                    }
                }
                Err(err) => {
                    debug!("Failed to check run status: {:?}", err);
                    failures += 1;
                    if failures >= MAX_STATUS_CHECK_FAILURES {
                        out.error(
                            "Monitoring the run status failed repeatedly; continuing to stream logs.",
                        );
                        return;
                    }
                }
            }

            sleep(STATUS_POLL_INTERVAL).await;
        }
    });

    rx
}

/// Waits on the completion monitor. Returns true when the run completed and
/// false when monitoring was abandoned; either way the receiver is consumed so
/// the caller stops selecting on it.
async fn wait_completion(rx: &mut Option<oneshot::Receiver<()>>) -> bool {
    let receiver = rx
        .as_mut()
        .expect("wait_completion called without a receiver");
    let completed = receiver.await.is_ok();
    *rx = None;
    completed
}

/// Prints a single stream event: log lines are deduped through the tracker,
/// warnings are rendered as `Warning: <content>`. Shared between the live
/// streaming loop and the post-completion drain.
fn print_stream_event(out: &output::Out, event: api::LogStreamEvent, tracker: &mut LineTracker) {
    match event {
        api::LogStreamEvent::EventLog(log) => {
            if tracker.accept(log.line_num) {
                out.remote_log_event(&log);
            }
        }
        api::LogStreamEvent::EventWarning(warning) => {
            out.write(&format!("Warning: {}\n", warning.content));
        }
    }
}

/// Drains any remaining buffered lines and warnings from the stream for a
/// short grace window after the run completes.
async fn drain_stream_with_grace(
    out: &output::Out,
    mut events: tokio::sync::mpsc::Receiver<api::LogStreamEvent>,
    tracker: &mut LineTracker,
) {
    let _ = timeout(STREAM_DRAIN_GRACE, async {
        while let Some(event) = events.recv().await {
            print_stream_event(out, event, tracker);
        }
    })
    .await;
}

/// Follows the logs of a run: prints stored logs for a finished run, waits for
/// a not-yet-started run, and otherwise attaches to the live log stream with
/// reconnects, dedup, and independent completion detection.
async fn follow_run_logs(out: &output::Out, config: &Config, name: &str, seq: i64) {
    let mut tracker = LineTracker::new();

    let run = describe_run_or_die(out, config, name, seq).await;

    match run_phase(&run.status) {
        RunPhase::Terminal => {
            print_stored_logs(out, config, name, seq, &mut tracker).await;
            return;
        }
        RunPhase::NotStarted => match wait_for_run_start(out, config, name, seq).await {
            WaitOutcome::Started => {}
            WaitOutcome::Finished => {
                print_stored_logs(out, config, name, seq, &mut tracker).await;
                return;
            }
            WaitOutcome::TimedOut => {
                out.die("Timed out waiting for the run to start. The runner may be unavailable.");
            }
        },
        RunPhase::InProgress => {}
    }

    stream_logs_with_reconnect(out, config, name, seq, &run.dollar_link, &mut tracker).await;
}

async fn stream_logs_with_reconnect(
    out: &output::Out,
    config: &Config,
    name: &str,
    seq: i64,
    run_link: &str,
    tracker: &mut LineTracker,
) {
    let enable_ctrl_c = out.foreground();
    let mut backoff = Backoff::new();
    let mut run_complete: Option<oneshot::Receiver<()>> = Some(spawn_completion_monitor(
        out.clone(),
        config.clone(),
        name.to_string(),
        seq,
    ));

    loop {
        match api::stream_run_logs(config, name, seq).await {
            Ok(mut events) => {
                backoff.reset();

                loop {
                    tokio::select! {
                        event = events.recv() => match event {
                            Some(event) => print_stream_event(out, event, tracker),
                            // Stream closed; fall through to the disconnect path.
                            None => break,
                        },
                        completed = wait_completion(&mut run_complete), if run_complete.is_some() => {
                            if completed {
                                drain_stream_with_grace(out, events, tracker).await;
                                print_stored_logs(out, config, name, seq, tracker).await;
                                return;
                            }
                            // Monitoring was abandoned; keep streaming and rely
                            // on the disconnect path to notice completion.
                        }
                        _ = tokio::signal::ctrl_c(), if enable_ctrl_c => {
                            out.write("Received Ctrl+C, stopping log streaming...\n");
                            out.write("Note: The run will continue in Tower cloud\n");
                            out.write(&format!("  See more: {}\n", run_link));
                            return;
                        }
                    }
                }
            }
            Err(err) => {
                out.error(&format!("Failed to stream run logs: {}", err));
                if err.is_fatal() {
                    std::process::exit(1);
                }
            }
        }

        // Disconnected (or a transient open failure): re-check the run status,
        // stop if the run is done, otherwise retry with backoff.
        let run = describe_run_or_die(out, config, name, seq).await;
        if run_phase(&run.status) == RunPhase::Terminal {
            print_stored_logs(out, config, name, seq, tracker).await;
            return;
        }

        sleep(backoff.next_delay()).await;
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
    use super::{apps_cmd, run_phase, Backoff, LineTracker, RunPhase};
    use std::time::Duration;
    use tower_api::models::run::Status as RunStatus;

    #[test]
    fn follow_flag_with_hash_form() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "logs", "hello-world#11", "--follow"])
            .unwrap();
        let (_, sub_matches) = matches.subcommand().unwrap();

        assert_eq!(
            sub_matches
                .get_one::<String>("app_name")
                .map(|s| s.as_str()),
            Some("hello-world#11")
        );
        assert!(sub_matches.get_flag("follow"));
    }

    #[test]
    fn follow_flag_with_separate_run_number() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "logs", "hello-world", "11", "--follow"])
            .unwrap();
        let (_, sub_matches) = matches.subcommand().unwrap();

        assert_eq!(sub_matches.get_one::<i64>("run_number"), Some(&11));
        assert!(sub_matches.get_flag("follow"));
    }

    #[test]
    fn follow_flag_short_form_with_app_only() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "logs", "hello-world", "-f"])
            .unwrap();
        let (_, sub_matches) = matches.subcommand().unwrap();

        assert_eq!(
            sub_matches
                .get_one::<String>("app_name")
                .map(|s| s.as_str()),
            Some("hello-world")
        );
        assert_eq!(sub_matches.get_one::<i64>("run_number"), None);
        assert!(sub_matches.get_flag("follow"));
    }

    #[test]
    fn follow_flag_defaults_to_false() {
        let matches = apps_cmd()
            .try_get_matches_from(["apps", "logs", "hello-world"])
            .unwrap();
        let (_, sub_matches) = matches.subcommand().unwrap();

        assert!(!sub_matches.get_flag("follow"));
    }

    #[test]
    fn terminal_statuses_group_as_terminal() {
        for status in [
            RunStatus::Crashed,
            RunStatus::Errored,
            RunStatus::Exited,
            RunStatus::Cancelled,
        ] {
            assert_eq!(run_phase(&status), RunPhase::Terminal);
        }
    }

    #[test]
    fn pre_start_statuses_group_as_not_started() {
        for status in [
            RunStatus::Scheduled,
            RunStatus::Pending,
            RunStatus::Starting,
        ] {
            assert_eq!(run_phase(&status), RunPhase::NotStarted);
        }
    }

    #[test]
    fn other_statuses_group_as_in_progress() {
        // Running and Retrying aren't in either explicit list, so they (like
        // any future status) count as in progress.
        assert_eq!(run_phase(&RunStatus::Running), RunPhase::InProgress);
        assert_eq!(run_phase(&RunStatus::Retrying), RunPhase::InProgress);
    }

    #[test]
    fn backoff_starts_small_doubles_and_caps() {
        let mut backoff = Backoff::new();

        assert_eq!(backoff.next_delay(), Duration::from_millis(500));
        assert_eq!(backoff.next_delay(), Duration::from_secs(1));
        assert_eq!(backoff.next_delay(), Duration::from_secs(2));
        assert_eq!(backoff.next_delay(), Duration::from_secs(4));
        assert_eq!(backoff.next_delay(), Duration::from_secs(5));
        assert_eq!(backoff.next_delay(), Duration::from_secs(5));
    }

    #[test]
    fn backoff_resets_to_initial_delay() {
        let mut backoff = Backoff::new();
        backoff.next_delay();
        backoff.next_delay();
        backoff.next_delay();

        backoff.reset();
        assert_eq!(backoff.next_delay(), Duration::from_millis(500));
    }

    #[test]
    fn line_tracker_accepts_monotonically_increasing_lines() {
        let mut tracker = LineTracker::new();

        assert!(tracker.accept(1));
        assert!(tracker.accept(2));
        assert!(tracker.accept(5));
    }

    #[test]
    fn line_tracker_drops_repeats_and_out_of_order_lines() {
        let mut tracker = LineTracker::new();

        assert!(tracker.accept(3));
        assert!(!tracker.accept(3));
        assert!(!tracker.accept(2));
        assert!(!tracker.accept(1));
        assert!(tracker.accept(4));
        assert!(!tracker.accept(4));
    }

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
