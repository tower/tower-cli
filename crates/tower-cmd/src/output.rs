pub use cli_table::{format::Justify, Cell};
use cli_table::{
    format::{Border, HorizontalLine, Separator},
    print_stdout, Table,
};
use colored::Colorize;
use std::io::{self, Write};

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
        tower_package::Error::NoManifest => "No manifeset was found".to_string(),
        tower_package::Error::InvalidManifest => {
            "Invalid manifest was found or created".to_string()
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
    };

    let line = format!("{} {}\n", "Config error:".red(), msg);
    write(&line);
}

pub fn write(msg: &str) {
    io::stdout().write_all(msg.as_bytes()).unwrap();
}

pub fn runtime_error(err: tower_runtime::errors::Error) {
    let line = format!("{} {}\n", "Runtime Error:".red(), err.to_string());
    io::stdout().write_all(line.as_bytes()).unwrap();
}

pub fn tower_error<T>(err: tower_api::apis::Error<T>)
where
    T: std::fmt::Debug + serde::de::DeserializeOwned,
{
    match err {
        tower_api::apis::Error::ResponseError(response) => {
            // Try to deserialize as ErrorModel first
            if let Ok(error_model) =
                serde_json::from_str::<tower_api::models::ErrorModel>(&response.content)
            {
                // Show the main error message from the detail field
                let detail = error_model.detail.as_deref().unwrap_or("Unknown error");
                let line = format!("{} {}\n", "Error:".red(), detail);
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
            } else {
                // If it's not an ErrorModel, try to show the raw content
                let line = format!(
                    "{} {}: {}\n",
                    "Error:".red(),
                    response.status,
                    response.content
                );
                io::stdout().write_all(line.as_bytes()).unwrap();
            }
        }
        tower_api::apis::Error::Reqwest(e) => {
            let line = format!("{} Network error: {}\n", "Error:".red(), e);
            io::stdout().write_all(line.as_bytes()).unwrap();
        }
        tower_api::apis::Error::Serde(e) => {
            let line = format!("{} Data parsing error: {}\n", "Error:".red(), e);
            io::stdout().write_all(line.as_bytes()).unwrap();
        }
        tower_api::apis::Error::Io(e) => {
            let line = format!("{} I/O error: {}\n", "Error:".red(), e);
            io::stdout().write_all(line.as_bytes()).unwrap();
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
            "A newer version of tower-cli is available: {} (you have {})",
            latest, current
        )
        .yellow(),
        "To upgrade, run: pip install --upgrade tower-cli".yellow()
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
