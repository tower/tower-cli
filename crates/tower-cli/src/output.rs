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
    println!("> Tower error: {}", err.code)
}
