pub use cli_table::{format::Justify, Cell};
use cli_table::{
    format::{Border, HorizontalLine, Separator},
    print_stdout, Table,
};
use colored::{control, Colorize};
use http::StatusCode;
use serde::Serialize;
use std::io::{self, Write};
use std::sync::{Mutex, OnceLock};
use tokio::sync::mpsc::UnboundedSender;
use tower_api::{
    apis::{Error as ApiError, ResponseContent},
    models::ErrorModel,
};
use tower_telemetry::debug;

const BANNER_TEXT: &str = include_str!("./banner.txt");

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OutputMode {
    /// Normal CLI output with colors and formatting
    Normal,
    /// JSON output mode
    Json,
    /// MCP server with stdio transport (no notifications, capture output)
    McpStdio,
    /// MCP server with streaming transport like SSE/HTTP (send notifications)
    McpStreaming,
}

impl OutputMode {
    pub fn is_mcp(self) -> bool {
        matches!(self, Self::McpStdio | Self::McpStreaming)
    }

    pub fn is_json(self) -> bool {
        matches!(self, Self::Json)
    }

    pub fn is_normal(self) -> bool {
        matches!(self, Self::Normal)
    }
}

static OUTPUT_MODE: OnceLock<OutputMode> = OnceLock::new();
static CURRENT_SENDER: Mutex<Option<UnboundedSender<String>>> = Mutex::new(None);

pub fn set_output_mode(mode: OutputMode) {
    OUTPUT_MODE.set(mode).ok();
    if mode.is_mcp() {
        control::set_override(false);
    }
}

pub fn get_output_mode() -> OutputMode {
    OUTPUT_MODE.get().copied().unwrap_or(OutputMode::Normal)
}

pub fn set_current_sender(sender: UnboundedSender<String>) {
    *CURRENT_SENDER.lock().unwrap() = Some(sender);
}

pub fn clear_current_sender() {
    *CURRENT_SENDER.lock().unwrap() = None;
}

fn send_to_current_sender(msg: String) {
    if let Ok(sender_guard) = CURRENT_SENDER.lock() {
        if let Some(tx) = sender_guard.as_ref() {
            tx.send(msg).ok();
        }
    }
}

pub fn json<T: Serialize>(data: &T) {
    match serde_json::to_string_pretty(data) {
        Ok(json_str) => {
            write(&format!("{}\n", json_str));
        }
        Err(e) => {
            error(&format!("Failed to serialize to JSON: {}", e));
        }
    }
}

pub fn success(msg: &str) {
    success_with_data(msg, None::<serde_json::Value>);
}

pub fn success_with_data<T: Serialize>(msg: &str, data: Option<T>) {
    if get_output_mode().is_json() {
        let mut response = serde_json::json!({
            "result": "success",
            "message": msg
        });

        if let Some(data) = data {
            response["data"] = serde_json::to_value(data).unwrap();
        }

        json(&response);
    } else {
        let line = format!("{} {}\n", "Success!".green(), msg);
        write(&line);
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

pub fn log_line(timestamp: &str, message: &str, t: LogLineType) {
    let line = format!("{} {}\n", format_timestamp(timestamp, t), message);
    write(&line);
}

pub fn remote_log_event(log: &tower_api::models::RunLogLine) {
    let ts = crate::util::dates::format_str(&log.reported_at);
    log_line(&ts, &log.content, LogLineType::Remote);
}

pub fn package_error(err: tower_package::Error) {
    let msg = match err {
        tower_package::Error::NoManifest => "No manifest was found".to_string(),
        tower_package::Error::InvalidManifest => {
            "Invalid manifest was found or created".to_string()
        }
        tower_package::Error::InvalidPath => {
            "There was a problem determining exactly where your Towerfile was stored on disk"
                .to_string()
        }
    };

    let line = format!("{} {}\n", "Package error:".red(), msg);
    write(&line);
}

pub fn header(text: &str) {
    let line = format!("{}\n", text.bold().green());
    write(&line);
}

pub fn detail(label: &str, value: &str) {
    let line = format!("{} {}\n", format!("{}:", label).bold().green(), value);
    write(&line);
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

pub fn config_error(err: config::Error) {
    let msg = match err {
        config::Error::ConfigDirNotFound => "No home directory found".to_string(),
        config::Error::NoHomeDir => "No home directory found".to_string(),
        config::Error::NoSession => "No session".to_string(),
        config::Error::InvalidTowerfile => {
            "Couldn't read the Towerfile in this directory".to_string()
        }
        config::Error::MissingTowerfile => {
            "No Towerfile was found in the target directory".to_string()
        }
        config::Error::MissingRequiredAppField { ref field } => {
            format!("Missing required app field `{}` in Towerfile", field)
        }
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
    write(&line);
}

pub fn write(msg: &str) {
    if get_output_mode().is_mcp() {
        let clean_msg = msg.trim_end().to_string();
        send_to_current_sender(clean_msg);
    } else {
        io::stdout().write_all(msg.as_bytes()).unwrap();
    }
}

pub fn error(msg: &str) {
    if get_output_mode().is_json() {
        let response = serde_json::json!({
            "result": "error",
            "message": msg
        });
        json(&response);
    } else {
        let line = format!("{} {}\n", "Oh no!".red(), msg);
        write(&line);
    }
}

pub fn runtime_error(err: tower_runtime::errors::Error) {
    let line = format!("{} {}\n", "Runtime Error:".red(), err.to_string());
    write(&line);
}

// Outputs both the model.detail and the model.errors fields in a human readable format.
pub fn output_full_error_details(model: &ErrorModel) {
    // Show the main detail message if available
    if let Some(detail) = &model.detail {
        write(&format!("\n{}\n", "Error details:".yellow()));
        write(&format!("{}\n", detail.red()));
    }

    // Show any additional error details from the errors field
    if let Some(errors) = &model.errors {
        if !errors.is_empty() {
            if model.detail.is_none() {
                write(&format!("\n{}\n", "Error details:".yellow()));
            }
            for error in errors {
                let msg = format!(
                    "  • {}",
                    error.message.as_deref().unwrap_or("Unknown error")
                );
                write(&format!("{}\n", msg.red()));
            }
        }
    }
}

fn output_response_content_error<T>(err: ResponseContent<T>) {
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
            write(&format!("\n{}\n", "API Error:".yellow()));
            write(&format!("{}\n", err.content.red()));
            return;
        }
    };

    match err.status {
        StatusCode::CONFLICT => {
            error("There was a conflict while trying to do that!");
            output_full_error_details(&error_model);
        }
        StatusCode::UNPROCESSABLE_ENTITY => {
            output_full_error_details(&error_model);
        }
        StatusCode::INTERNAL_SERVER_ERROR => {
            error("The Tower API encountered an internal error. Maybe try again later on.");
        }
        StatusCode::NOT_FOUND => {
            output_full_error_details(&error_model);
        }
        StatusCode::UNAUTHORIZED => {
            error(
                "You aren't authorized to do that! Are you logged in? Run `tower login` to login.",
            );
        }
        _ => {
            error("The Tower API returned an error that the Tower CLI doesn't know what to do with! Maybe try again in a bit.");
        }
    }
}

pub fn tower_error<T>(err: ApiError<T>) {
    match err {
        ApiError::ResponseError(resp) => {
            output_response_content_error(resp);
        }
        ApiError::Reqwest(e) => {
            debug!("Reqwest error: {:?}", e);
            error("The Tower CLI wasn't able to talk to the Tower API! Are you offline? Try again later.");
        }
        ApiError::Serde(e) => {
            debug!("Serde error: {:?}", e);
            error("The Tower API returned something that the Tower CLI didn't understand. Maybe you need to upgrade Tower CLI?");
        }
        ApiError::Io(e) => {
            debug!("Io error: {:?}", e);
            error("An error happened while talking to the Tower API. You can try that again in a bit.");
        }
    }
}

pub fn table<T: Serialize>(headers: Vec<String>, data: Vec<Vec<String>>, json_data: Option<&T>) {
    if get_output_mode().is_json() {
        if let Some(data) = json_data {
            json(data);
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
            json(&json_output);
        }
    } else {
        let separator = Separator::builder()
            .title(Some(HorizontalLine::default()))
            .build();

        let table = data
            .table()
            .border(Border::builder().build())
            .separator(separator)
            .title(headers.iter().map(|h| h.yellow().to_string()));

        print_stdout(table).unwrap();
    }
}

pub fn list<T: Serialize>(items: Vec<String>, json_data: Option<&T>) {
    if get_output_mode().is_json() {
        if let Some(data) = json_data {
            json(data);
        } else {
            json(&items);
        }
    } else {
        for item in items {
            let line = format!(" * {}\n", item);
            let line = line.replace("\n", "\n   ");
            let line = format!("{}\n", line);
            write(&line);
        }
    }
}

pub fn banner() {
    write(&BANNER_TEXT);
}

pub struct Spinner {
    msg: String,
    spinner: Option<spinners::Spinner>,
}

impl Spinner {
    pub fn new(msg: String) -> Spinner {
        if get_output_mode().is_normal() {
            let spinner = spinners::Spinner::new(spinners::Spinners::Dots, msg.clone());
            Spinner {
                spinner: Some(spinner),
                msg,
            }
        } else {
            Spinner { spinner: None, msg }
        }
    }

    pub fn success(&mut self) {
        if let Some(ref mut spinner) = self.spinner {
            let sym = "✔".bold().green().to_string();
            spinner.stop_and_persist(&sym, format!("{} Done!", self.msg));
        } else if get_output_mode().is_mcp() {
            send_to_current_sender(format!("{} Done!", self.msg));
        }
    }

    pub fn failure(&mut self) {
        if let Some(ref mut spinner) = self.spinner {
            let sym = "✘".bold().red().to_string();
            spinner.stop_and_persist(&sym, format!("{} Failed!", self.msg));
        } else if get_output_mode().is_mcp() {
            send_to_current_sender(format!("{} Failed!", self.msg));
        }
    }
}

/// spinner starts and returns a Spinner object. This is useful for long running tasks where you
/// want to demonstrate there's something happening.
pub fn spinner(msg: &str) -> Spinner {
    Spinner::new(msg.into())
}

pub fn write_update_message(latest: &str, current: &str) {
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
    use std::io::{self, Write};
    io::stderr().write_all(line.as_bytes()).unwrap();
}

/// newline just outputs a newline. This is useful when you have a very specific formatting you
/// want to maintain and you don't want to use println!.
pub fn newline() {
    write("\n");
}

pub fn die(msg: &str) -> ! {
    let line = format!("{} {}\n", "Error:".red(), msg);
    write(&line);
    std::process::exit(1);
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
