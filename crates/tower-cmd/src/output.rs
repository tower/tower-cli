use std::io::{self, Write};
use colored::Colorize;
use cli_table::{print_stdout, Table};
pub use cli_table::{Cell, format::Justify};

pub fn success(msg: &str) {
    let line = format!("{} {}\n", "Success!".green(), msg);
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
    let table = data.table()
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
