use cli_table::{print_stdout, Table};
pub use cli_table::{Cell, format::Justify};

pub fn success(msg: &str) {
    println!("> {}", msg)
}

pub fn config_error(err: config::Error) {
    match err {
        config::Error::ConfigDirNotFound => {
            println!("> Config error: No home directory found")
        },
        config::Error::NoHomeDir => {
            println!("> Config error: No home directory found")
        },
        config::Error::NoSession => {
            println!("> Config error: No session found")
        }
    }
}

pub fn tower_error(err: tower_api::TowerError) {
    println!("> Error: {}", err.description)
}

pub fn table(headers: Vec<String>, data: Vec<Vec<String>>) {
    let table = data.table()
        .title(headers);
        
    print_stdout(table).unwrap();
}
