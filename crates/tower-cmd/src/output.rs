pub use cli_table::{format::Justify, Cell};
use cli_table::{
    format::{Border, HorizontalLine, Separator},
    Table, TableStruct,
};
use colored::Colorize;
use http::StatusCode;
use serde::Serialize;
use std::io::{self, IsTerminal, Write};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc::UnboundedSender;
use tower_api::{
    apis::{Error as ApiError, ResponseContent},
    models::ErrorModel,
};
use tower_telemetry::debug;

const BANNER_TEXT: &str = include_str!("./banner.txt");

/// How results are rendered. `Human` produces the coloured, formatted output;
/// `Json` produces machine-parseable JSON.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Format {
    Human,
    Json,
}

/// `Out` is the explicit output destination for a command. It carries the render
/// format and the writer to send results to, so nothing needs to consult a global
/// to decide where output goes. The CLI builds one over stdout; the MCP server
/// builds one over a channel that forwards each line to the connected peer.
///
/// `Out` is cheap to clone and safe to send between tasks — clones share the same
/// underlying writer through an `Arc<Mutex<_>>`, so a spawned task (e.g. a log
/// monitor) can own a clone and write to the same destination as the foreground.
#[derive(Clone)]
pub struct Out {
    format: Format,
    writer: Arc<Mutex<Box<dyn Write + Send>>>,
    /// True only when driving an interactive terminal, where spinners animate.
    /// False for JSON and for MCP capture.
    interactive: bool,
    /// True when this is a foreground CLI process that owns terminal signals
    /// (so it may install a Ctrl+C handler). False for MCP/captured output.
    foreground: bool,
}

impl Out {
    fn new(
        format: Format,
        writer: Box<dyn Write + Send>,
        interactive: bool,
        foreground: bool,
    ) -> Self {
        Self {
            format,
            writer: Arc::new(Mutex::new(writer)),
            interactive,
            foreground,
        }
    }

    /// Human-formatted output to stdout. Spinners animate when stdout is a TTY.
    pub fn human() -> Self {
        let interactive = io::stdout().is_terminal();
        Self::new(Format::Human, Box::new(io::stdout()), interactive, true)
    }

    /// JSON output to stdout. No spinner animation so stdout stays parseable.
    pub fn json_stdout() -> Self {
        Self::new(Format::Json, Box::new(io::stdout()), false, true)
    }

    /// Output captured for an MCP tool call. Each written line is forwarded to the
    /// supplied channel; the MCP server collects the lines and optionally streams
    /// them to the peer as logging notifications.
    pub fn mcp(sender: UnboundedSender<String>) -> Self {
        Self::new(Format::Human, Box::new(McpWriter { sender }), false, false)
    }

    /// Output that goes nowhere. Used where a command emits progress that the caller
    /// discards (e.g. the MCP deploy tool builds its own result message).
    pub fn sink() -> Self {
        Self::new(Format::Human, Box::new(io::sink()), false, false)
    }

    fn is_json(&self) -> bool {
        self.format == Format::Json
    }

    /// Whether this process owns terminal signal handling (CLI foreground). MCP and
    /// other captured outputs return false, so they don't trap Ctrl+C.
    pub fn foreground(&self) -> bool {
        self.foreground
    }

    /// Whether this output drives an interactive terminal: human format on a
    /// stdout TTY. False for JSON, MCP capture, and redirected output.
    pub fn interactive(&self) -> bool {
        self.interactive
    }

    /// Writes raw text to the destination. On a broken pipe the process exits
    /// cleanly, matching classic Unix tool behaviour.
    pub fn write(&self, msg: &str) {
        let mut writer = self.writer.lock().unwrap();
        if let Err(err) = writer.write_all(msg.as_bytes()) {
            if err.kind() == io::ErrorKind::BrokenPipe {
                std::process::exit(0);
            }
            panic!("failed writing output: {err}");
        }
        writer.flush().ok();
    }

    pub fn newline(&self) {
        self.write("\n");
    }

    pub fn banner(&self) {
        self.write(BANNER_TEXT);
    }

    fn json<T: Serialize>(&self, data: &T) {
        match serde_json::to_string_pretty(data) {
            Ok(json_str) => {
                let line = format!("{}\n", json_str);
                self.write(&line);
            }
            Err(e) => {
                self.error(&format!("Failed to serialize to JSON: {}", e));
            }
        }
    }

    pub fn success(&self, msg: &str) {
        self.success_with_data(msg, None::<serde_json::Value>);
    }

    pub fn success_with_data<T: Serialize>(&self, msg: &str, data: Option<T>) {
        let mut response = serde_json::json!({
            "result": "success",
            "message": msg
        });

        if let Some(data) = data {
            response["data"] = serde_json::to_value(data).unwrap();
        }

        let line = format!("{} {}\n", "Success!".green(), msg);
        self.text(&line, &response);
    }

    /// Writes a low-emphasis informational line, dimmed in human output.
    pub fn muted(&self, msg: &str) {
        if self.is_json() {
            let response = serde_json::json!({
                "result": "muted",
                "message": msg
            });
            self.json(&response);
        } else {
            let line = format!("{}\n", msg.dimmed());
            self.write(&line);
        }
    }

    pub fn error(&self, msg: &str) {
        if self.is_json() {
            let response = serde_json::json!({
                "result": "error",
                "message": msg
            });
            self.json(&response);
        } else {
            let line = format!("{} {}\n", "Oh no!".red(), msg);
            self.write(&line);
        }
    }

    pub fn log_line(&self, timestamp: &str, message: &str, t: LogLineType) {
        let line = format!("{} {}\n", format_timestamp(timestamp, t), message);
        self.write(&line);
    }

    pub fn remote_log_event(&self, log: &tower_api::models::RunLogLine) {
        let ts = crate::util::dates::format_str(&log.reported_at);
        self.log_line(&ts, &log.content, LogLineType::Remote);
    }

    pub fn package_error(&self, err: tower_package::Error) {
        let msg = match err {
            tower_package::Error::NoManifest => "No manifest was found".to_string(),
            tower_package::Error::InvalidManifest => {
                "Invalid manifest was found or created".to_string()
            }
            tower_package::Error::InvalidPath => {
                "There was a problem determining exactly where your Towerfile was stored on disk"
                    .to_string()
            }
            tower_package::Error::InvalidGlob { message } => {
                format!("Invalid file glob pattern: {}", message)
            }
            tower_package::Error::InvalidTowerfile { message } => {
                format!("Invalid Towerfile: {}", message)
            }
            tower_package::Error::MissingTowerfile => {
                "No Towerfile was found in the target directory".to_string()
            }
            tower_package::Error::MissingRequiredAppField { field } => {
                format!("Missing required app field `{}` in Towerfile", field)
            }
            tower_package::Error::Io { source } => format!("IO error: {}", source),
            tower_package::Error::MissingScript { script } => {
                format!("Script '{}' not found. Check that the 'script' field in your Towerfile points to a file that exists in your project.", script)
            }
        };

        let line = format!("{} {}\n", "Package error:".red(), msg);
        self.write(&line);
    }

    pub fn config_error(&self, err: config::Error) {
        let msg = match err {
            config::Error::ConfigDirNotFound => "Config directory not found".to_string(),
            config::Error::NoHomeDir => "No home directory found".to_string(),
            config::Error::Io { ref source } => format!("IO error: {}", source),
            config::Error::NoSession => "No session".to_string(),
            config::Error::TeamNotFound { ref team_name } => {
                format!("Team with name `{}` not found!", team_name)
            }
            config::Error::UnknownDescribeSessionValue { value: _ } => {
                "An error occured while describing the session associated with the JWT you provided. Maybe your CLI is out of date?".to_string()
            }
            config::Error::DescribeSessionError { ref err } => {
                format!("An error occured while describing the session associated with the JWT you provided: {}", err)
            }
        };

        let line = format!("{} {}\n", "Config error:".red(), msg);
        self.write(&line);
    }

    // Outputs both the model.detail and the model.errors fields in a human readable format.
    fn output_full_error_details(&self, model: &ErrorModel) {
        // Show the main detail message if available
        if let Some(detail) = &model.detail {
            self.write(&format!("\n{}\n", "Error details:".yellow()));
            self.write(&format!("{}\n", detail.red()));
        }

        // Show any additional error details from the errors field
        if let Some(errors) = &model.errors {
            if !errors.is_empty() {
                if model.detail.is_none() {
                    self.write(&format!("\n{}\n", "Error details:".yellow()));
                }
                for error in errors {
                    let msg = format!(
                        "  • {}",
                        error.message.as_deref().unwrap_or("Unknown error")
                    );
                    self.write(&format!("{}\n", msg.red()));
                }
            }
        }
    }

    fn output_response_content_error<T>(&self, err: ResponseContent<T>) {
        // Attempt to deserialize the error content into an ErrorModel.
        let error_model = match serde_json::from_str::<ErrorModel>(&err.content) {
            Ok(model) => {
                debug!("Error model (status: {}): {:?}", err.status, model);
                model
            }
            Err(e) => {
                debug!("Failed to parse error content as JSON: {}", e);
                debug!("Raw error content: {}", err.content);
                // Show the raw error content if JSON parsing fails
                self.write(&format!("\n{}\n", "API Error:".yellow()));
                self.write(&format!("{}\n", err.content.red()));
                return;
            }
        };

        match err.status {
            StatusCode::CONFLICT => {
                self.output_full_error_details(&error_model);
            }
            StatusCode::UNPROCESSABLE_ENTITY => {
                self.output_full_error_details(&error_model);
            }
            StatusCode::INTERNAL_SERVER_ERROR => {
                self.error(
                    "The Tower API encountered an internal error. Maybe try again later on.",
                );
            }
            StatusCode::NOT_FOUND => {
                self.output_full_error_details(&error_model);
            }
            StatusCode::UNAUTHORIZED => {
                self.error(
                    "You aren't authorized to do that! Are you logged in? Run `tower login` to login.",
                );
            }
            _ => {
                if error_model.detail.is_none() && error_model.errors.is_none() {
                    self.error("The Tower API returned an error that the Tower CLI doesn't know what to do with! Maybe try again in a bit.");
                }
                self.output_full_error_details(&error_model);
            }
        }
    }

    fn tower_error<T>(&self, err: ApiError<T>) {
        match err {
            ApiError::ResponseError(resp) => {
                self.output_response_content_error(resp);
            }
            ApiError::Reqwest(e) => {
                debug!("Reqwest error: {:?}", e);
                self.error("The Tower CLI wasn't able to talk to the Tower API! Are you offline? Try again later.");
            }
            ApiError::Serde(e) => {
                debug!("Serde error: {:?}", e);
                self.error("The Tower API returned something that the Tower CLI didn't understand. Maybe you need to upgrade Tower CLI?");
            }
            ApiError::Io(e) => {
                debug!("Io error: {:?}", e);
                self.error("An error happened while talking to the Tower API. You can try that again in a bit.");
            }
        }
    }

    /// Handles Tower API errors with context-specific authentication messages.
    /// If the error is a 401 Unauthorized, provides a helpful message mentioning
    /// the operation that failed and suggests running 'tower login'.
    /// Always exits the process with error code 1.
    pub fn tower_error_and_die<T>(&self, err: ApiError<T>, operation: &str) -> ! {
        // Check if this is an authentication error
        if let ApiError::ResponseError(ref resp) = err {
            if resp.status == StatusCode::UNAUTHORIZED {
                self.die(&format!(
                    "{} because you are not logged into Tower. Please run 'tower login' first.",
                    operation
                ));
            }
        }

        // Show the detailed error first
        self.tower_error(err);
        self.die(operation);
    }

    pub fn table<T: Serialize>(
        &self,
        headers: Vec<String>,
        data: Vec<Vec<String>>,
        json_data: Option<&T>,
    ) {
        if self.is_json() {
            if let Some(data) = json_data {
                self.json(data);
            } else {
                // Fallback: convert table data to JSON structure
                let json_output: Vec<serde_json::Map<String, serde_json::Value>> = data
                    .iter()
                    .map(|row| {
                        let mut obj = serde_json::Map::new();
                        for (i, value) in row.iter().enumerate() {
                            let key = headers
                                .get(i)
                                .expect("header should have same number of columns as row");
                            obj.insert(key.to_string(), serde_json::Value::String(value.clone()));
                        }
                        obj
                    })
                    .collect();
                self.json(&json_output);
            }
        } else {
            let line = format!("{}\n", table_text(headers, data));
            self.write(&line);
        }
    }

    pub fn list<T: Serialize>(&self, items: Vec<String>, json_data: Option<&T>) {
        if self.is_json() {
            if let Some(data) = json_data {
                self.json(data);
            } else {
                self.json(&items);
            }
        } else {
            for item in items {
                let line = format!(" * {}\n", item);
                let line = line.replace("\n", "\n   ");
                let line = format!("{}\n", line);
                self.write(&line);
            }
        }
    }

    /// Writes a human-readable rendering of some data, or the data itself as JSON when
    /// in JSON mode. Use this when a command's output is data that has both a plain text
    /// and a JSON representation, mirroring `table` and `list`.
    pub fn text<T: Serialize>(&self, msg: &str, json_data: &T) {
        if self.is_json() {
            self.json(json_data);
        } else {
            self.write(msg);
        }
    }

    /// Writes presentation-only text that accompanies human-formatted output, like table
    /// legends or hints. Suppressed in JSON mode so stdout stays machine-parseable.
    pub fn note(&self, msg: &str) {
        if !self.is_json() {
            self.write(msg);
        }
    }

    pub fn die(&self, msg: &str) -> ! {
        io::stdout().flush().ok();
        io::stderr().flush().ok();
        let line = format!("{} {}\n", "Error:".red(), msg);
        self.write(&line);
        // Flush output before exit to ensure "Error:" message is displayed
        io::stdout().flush().ok();
        io::stderr().flush().ok();
        std::process::exit(1);
    }

    /// Starts a spinner for a long running task. It animates only on an interactive
    /// terminal; otherwise its completion messages are written like any other line so
    /// they are still captured (e.g. by the MCP server).
    pub fn spinner(&self, msg: &str) -> Spinner {
        let anim = if self.interactive {
            Some(spinners::Spinner::new(
                spinners::Spinners::Dots,
                msg.to_string(),
            ))
        } else {
            None
        };
        Spinner {
            msg: msg.to_string(),
            anim,
        }
    }

    /// Runs an async operation with a spinner and proper error handling.
    ///
    /// - Shows a spinner with "{operation}..." while the operation runs
    /// - On success: stops the spinner with success indicator and returns the result
    /// - On error: stops the spinner with failure indicator and shows an auth-aware
    ///   error message, then exits the process.
    pub async fn with_spinner<F, T, E>(&self, operation: &str, future: F) -> T
    where
        F: std::future::Future<Output = Result<T, ApiError<E>>>,
    {
        let spinner_msg = format!("{}...", operation);
        let mut spinner = self.spinner(&spinner_msg);
        match future.await {
            Ok(result) => {
                spinner.success(self);
                result
            }
            Err(err) => {
                spinner.failure(self);
                let error_msg = format!("{} failed", operation);
                self.tower_error_and_die(err, &error_msg);
            }
        }
    }

    /// The MCP-safe version of `with_spinner`: returns errors instead of exiting.
    /// Use this for operations that may be called from MCP or other contexts where
    /// process exit is not acceptable. Returns the error without displaying it, so
    /// the caller decides how to handle and display it.
    pub async fn try_with_spinner<F, T, E>(
        &self,
        operation: &str,
        future: F,
    ) -> Result<T, ApiError<E>>
    where
        F: std::future::Future<Output = Result<T, ApiError<E>>>,
    {
        let spinner_msg = format!("{}...", operation);
        let mut spinner = self.spinner(&spinner_msg);
        match future.await {
            Ok(result) => {
                spinner.success(self);
                Ok(result)
            }
            Err(err) => {
                spinner.failure(self);
                // Just return the error - let the caller decide how to handle it
                Err(err)
            }
        }
    }
}

/// A writer that forwards each written chunk to an MCP channel as one message
/// (trailing whitespace trimmed). This replaces the previous global sender: the
/// destination now lives in the `Out`.
struct McpWriter {
    sender: UnboundedSender<String>,
}

impl Write for McpWriter {
    fn write(&mut self, data: &[u8]) -> io::Result<usize> {
        let text = String::from_utf8_lossy(data).trim_end().to_string();
        if !text.is_empty() {
            self.sender.send(text).ok();
        }
        Ok(data.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

pub enum LogLineType {
    Remote,
    Local,
}

fn format_timestamp(timestamp: &str, t: LogLineType) -> String {
    let ts = timestamp.bold();

    let sep = "|".bold();

    match t {
        LogLineType::Remote => format!("{} {}", ts.yellow(), sep.yellow()),
        LogLineType::Local => format!("{} {}", ts.green(), sep.green()),
    }
}

pub fn title(text: &str) -> String {
    text.bold().green().to_string()
}

pub fn placeholder(text: &str) -> String {
    text.white().dimmed().italic().to_string()
}

pub fn paragraph(msg: &str) -> String {
    msg.chars()
        .collect::<Vec<char>>()
        .chunks(78)
        .map(|c| c.iter().collect::<String>())
        .map(|li| format!("  {}", li))
        .collect::<Vec<String>>()
        .join("\n")
}

fn formatted_table(headers: Vec<String>, data: Vec<Vec<String>>) -> TableStruct {
    let separator = Separator::builder()
        .title(Some(HorizontalLine::default()))
        .build();

    data.table()
        .border(Border::builder().build())
        .separator(separator)
        .title(headers.iter().map(|h| h.bold().yellow().to_string()))
}

pub fn table_text(headers: Vec<String>, data: Vec<Vec<String>>) -> String {
    match formatted_table(headers, data).display() {
        Ok(table) => format!("{}", table),
        Err(err) => panic!("failed rendering table: {err}"),
    }
}

pub struct Spinner {
    msg: String,
    anim: Option<spinners::Spinner>,
}

impl Spinner {
    pub fn success(&mut self, out: &Out) {
        if let Some(ref mut spinner) = self.anim {
            let sym = "✔".bold().green().to_string();
            spinner.stop_and_persist(&sym, format!("{} Done!", self.msg));
        } else if out.format == Format::Human {
            out.write(&format!("{} Done!\n", self.msg));
        }
    }

    pub fn failure(&mut self, out: &Out) {
        if let Some(ref mut spinner) = self.anim {
            let sym = "✘".bold().red().to_string();
            spinner.stop_and_persist(&sym, format!("{} Failed!", self.msg));
        } else if out.format == Format::Human {
            out.write(&format!("{} Failed!\n", self.msg));
        }
    }
}

/// Reports a fatal CLI usage error (such as a missing required flag) and exits.
/// Used during argument parsing, before a command's `Out` is in play.
pub fn die_usage(msg: &str) -> ! {
    let line = format!("{} {}\n", "Error:".red(), msg);
    let mut stdout = io::stdout();
    let _ = stdout.write_all(line.as_bytes());
    let _ = stdout.flush();
    std::process::exit(1);
}

/// Writes a diagnostic error to stderr. For background tasks that have no `Out`
/// handle to write through (e.g. a spawned run-completion monitor).
pub fn background_error(msg: &str) {
    write_to_stderr(&format!("{} {}\n", "Oh no!".red(), msg));
}

/// Writes a labelled notice to stderr once per user, ever. The once-per-user
/// claim is only spent when stderr is a terminal, so a script, MCP capture, or
/// CI run can't use it up on a notice nobody saw.
pub(crate) fn notice_once(id: &str, label: &str, msg: &str) {
    if !io::stderr().is_terminal() {
        return;
    }

    match config::claim_notice(id) {
        Ok(true) => notice_to_stderr(label, msg),
        Ok(false) => {}
        Err(err) => debug!("Failed to persist CLI notice {}: {}", id, err),
    }
}

/// Writes a labelled notice to stderr, keeping stdout clean for command output.
fn notice_to_stderr(label: &str, msg: &str) {
    let line = format!("{} {}\n", label.bold().yellow(), msg);
    write_to_stderr(&line);
}

fn write_to_stderr(msg: &str) {
    let mut stderr = io::stderr();
    if let Err(err) = stderr.write_all(msg.as_bytes()) {
        if err.kind() == io::ErrorKind::BrokenPipe {
            std::process::exit(0);
        }
        panic!("failed writing to stderr: {err}");
    }
    stderr.flush().ok();
}

pub fn write_update_available_message(latest: &str, current: &str) {
    let line = format!(
        "{}\n{}\n",
        format!(
            "A newer version of tower is available: {} (you have {})",
            latest, current
        )
        .yellow(),
        "To upgrade, run: pip install --upgrade tower".yellow()
    );

    // Always write version check messages to stderr to avoid polluting stdout
    write_to_stderr(&line);
}

pub fn write_dev_version_message(current: &str, latest: &str) {
    let line = format!(
        "{}\n",
        format!(
            "Running dev version {} (latest published: {})",
            current, latest
        )
        .dimmed()
    );

    write_to_stderr(&line);
}

pub struct ProgressBar {
    inner: indicatif::ProgressBar,
}

impl ProgressBar {
    pub fn new(msg: String) -> ProgressBar {
        let style = indicatif::ProgressStyle::default_bar()
            .template("{spinner:.green} {msg} [{elapsed_precise}] [{bar:40.cyan/blue}] {bytes}/{total_bytes} ({eta})")
            .expect("Failed to setup progress bar somehow");

        let pb = indicatif::ProgressBar::new(0);
        pb.set_style(style);
        pb.set_message(msg);

        ProgressBar { inner: pb }
    }

    pub fn finish(&self) {
        self.inner.finish();
    }

    pub fn set_length(&self, max: u64) {
        self.inner.set_length(max);
    }

    pub fn set_position(&self, pos: u64) {
        self.inner.set_position(pos);
    }
}

pub fn progress_bar(msg: &str) -> ProgressBar {
    ProgressBar::new(msg.to_string())
}
