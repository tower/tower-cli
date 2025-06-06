pub use cli_table::{format::Justify, Cell};
use cli_table::{
    format::{Border, HorizontalLine, Separator},
    print_stdout, Table,
};
use http::StatusCode;
use colored::Colorize;
use std::io::{self, Write};
use tower_api::{
    apis::{
        Error as ApiError,
        ResponseContent,
    },
    models::ErrorModel,
};
use tower_telemetry::debug;

const BANNER_TEXT: &str = include_str!("./banner.txt");

pub fn success(msg: &str) {
    let line = format!("{} {}\n", "Success!".green(), msg);
    write(&line);
}

pub fn failure(msg: &str) {
    let line = format!("{} {}\n", "Oh no!".red(), msg);
    write(&line);
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

pub fn package_error(err: tower_package::Error) {
    let msg = match err {
        tower_package::Error::NoManifest => "No manifest was found".to_string(),
        tower_package::Error::InvalidManifest => {
            "Invalid manifest was found or created".to_string()
        }
        tower_package::Error::InvalidPath => {
            "There was a problem determining exactly where your Towerfile was stored on disk".to_string()
        }
    };

    let line = format!("{} {}\n", "Package error:".red(), msg);
    write(&line);
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
        config::Error::TeamNotFound { ref team_slug } => {
            format!("Team with slug `{}` not found!", team_slug)
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
    io::stdout().write_all(msg.as_bytes()).unwrap();
}

pub fn error(msg: &str) {
    let line = format!("{} {}\n", "Oh no!".red(), msg);
    io::stdout().write_all(line.as_bytes()).unwrap();
}

pub fn runtime_error(err: tower_runtime::errors::Error) {
    let line = format!("{} {}\n", "Runtime Error:".red(), err.to_string());
    io::stdout().write_all(line.as_bytes()).unwrap();
}

fn output_response_content_error<T>(err: ResponseContent<T>) {
    // Attempt to deserialize the error content into an ErrorModel.
    let error_model: ErrorModel = match serde_json::from_str(&err.content) {
        Ok(model) => model,
        Err(e) => {
            debug!("Failed to parse error content as JSON: {}", e);
            debug!("Raw error content: {}", err.content);
            error("An unexpected error occurred while processing the response.");
            return;
        }
    };
    debug!("Error model (status: {}): {:?}", err.status, error_model);

    match err.status {
        StatusCode::CONFLICT => {
            // Show the main error message from the detail field
            error("There was a conflict while trying to do that!");

            // Show any additional error details from the errors field
            if let Some(errors) = &error_model.errors {
                if !errors.is_empty() {
                    writeln!(io::stdout(), "\n{}", "Error details:".yellow()).unwrap();
                    for error in errors {
                        let msg = format!(
                            "  • {}",
                            error.message.as_deref().unwrap_or("Unknown error")
                        );
                        writeln!(io::stdout(), "{}", msg.red()).unwrap();
                    }
                }
            }
            
        },
        StatusCode::UNPROCESSABLE_ENTITY => {
            // Show the main error message from the detail field
            let line = format!("{} {}\n", "Validation error:".red(), "You need to fix one or more validation errors");
            io::stdout().write_all(line.as_bytes()).unwrap();

            // Show any additional error details from the errors field
            if let Some(errors) = &error_model.errors {
                if !errors.is_empty() {
                    writeln!(io::stdout(), "\n{}", "Error details:".yellow()).unwrap();
                    for error in errors {
                        let msg = format!(
                            "  • {}",
                            error.message.as_deref().unwrap_or("Unknown error")
                        );
                        writeln!(io::stdout(), "{}", msg.red()).unwrap();
                    }
                }
            }
        },
        StatusCode::INTERNAL_SERVER_ERROR => {
            error("The Tower API encountered an internal error. Maybe try again later on.");
        },
        StatusCode::UNAUTHORIZED => {
            error("You aren't authorized to do that! Are you logged in? Run `tower login` to login.");
        },
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

pub fn table(headers: Vec<String>, data: Vec<Vec<String>>) {
    let separator = Separator::builder()
        .title(Some(HorizontalLine::default()))
        .build();

    let table = data
        .table()
        .border(Border::builder().build())
        .separator(separator)
        .title(headers);

    print_stdout(table).unwrap();
}

pub fn list(items: Vec<String>) {
    for item in items {
        let line = format!(" * {}\n", item);
        let line = line.replace("\n", "\n   ");
        let line = format!("{}\n", line);
        io::stdout().write_all(line.as_bytes()).unwrap();
    }
}

pub fn banner() {
    write(&BANNER_TEXT);
}

pub struct Spinner {
    msg: String,
    spinner: spinners::Spinner,
}

impl Spinner {
    pub fn new(msg: String) -> Spinner {
        let spinner = spinners::Spinner::new(spinners::Spinners::Dots, msg.clone());
        Spinner { spinner, msg }
    }

    pub fn success(&mut self) {
        let sym = "✔".bold().green().to_string();
        self.spinner
            .stop_and_persist(&sym, format!("{} Done!", self.msg));
    }

    pub fn failure(&mut self) {
        let sym = "✘".bold().red().to_string();
        self.spinner
            .stop_and_persist(&sym, format!("{} Failed!", self.msg));
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

    io::stdout().write_all(line.as_bytes()).unwrap();
}

/// newline just outputs a newline. This is useful when you have a very specific formatting you
/// want to maintain and you don't want to use println!.
pub fn newline() {
    io::stdout().write_all("\n".as_bytes()).unwrap();
}

pub fn die(msg: &str) -> ! {
    let line = format!("{} {}\n", "Error:".red(), msg);
    io::stdout().write_all(line.as_bytes()).unwrap();
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
