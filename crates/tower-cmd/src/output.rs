use std::io::{self, Write};
use colored::Colorize;
use cli_table::{print_stdout, Table, format::{Border, Separator, HorizontalLine}};
pub use cli_table::{Cell, format::Justify};

const BANNER_TEXT: &str = include_str!("./banner.txt");

pub fn success(msg: &str) {
    let line = format!("{} {}\n", "Success!".green(), msg);
    io::stdout().write_all(line.as_bytes()).unwrap();
}

pub fn package_error(err: tower_package::Error) {
    let msg = match err {
        tower_package::Error::NoManifest => {
            "No manifeset was found".to_string()
        },
        tower_package::Error::InvalidManifest => {
            "Invalid manifest was found or created".to_string()
        },
    };

    let line = format!("{} {}\n", "Package error:".red(), msg);
    io::stdout().write_all(line.as_bytes()).unwrap();
}

pub fn config_error(err: config::Error) {
    let msg = match err {
        config::Error::ConfigDirNotFound => {
            "No home directory found"
        },
        config::Error::NoHomeDir => {
            "No home directory found"
        },
        config::Error::NoSession => {
            "No session"
        },
        config::Error::InvalidTowerfile => {
            "Couldn't read the Towerfile in this directory"
        },
        config::Error::MissingTowerfile => {
            "No Towerfile was found in the current directory"
        }
    };

    let line = format!("{} {}\n", "Config error:".red(), msg);
    io::stdout().write_all(line.as_bytes()).unwrap();
}

pub fn tower_error(err: tower_api::TowerError) {
    let line = format!("{} {}\n", "Error:".red(), err.description.friendly);
    io::stdout().write_all(line.as_bytes()).unwrap();
}

pub fn table(headers: Vec<String>, data: Vec<Vec<String>>) {
    let separator = Separator::builder()
        .title(Some(HorizontalLine::default()))
        .build();

    let table = data.table()
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
    io::stdout().write_all(BANNER_TEXT.as_bytes()).unwrap();
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

    pub fn success(mut self) {
        let sym = "✔".bold().green().to_string();
        self.spinner.stop_and_persist(&sym, format!("{} Done!", self.msg));
        newline();
    }

    pub fn failure(mut self) {
        let sym = "✘".bold().red().to_string();
        self.spinner.stop_and_persist(&sym, format!("{} Failed!", self.msg));
        newline();
    }
}

/// spinner starts and returns a Spinner object. This is useful for long running tasks where you
/// want to demonstrate there's something happening.
pub fn spinner(msg: &str) -> Spinner {
    Spinner::new(msg.into())
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
