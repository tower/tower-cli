use serde::{Deserialize, Serialize};

mod error;
mod session;
mod towerfile;

pub use session::{User, Token, Session};
pub use error::Error;
pub use towerfile::Towerfile;

const DEFAULT_TOWER_URL: &str = "https://services.tower.dev";

#[derive(Serialize, Deserialize)]
pub struct Config {
    pub debug: bool,
    pub tower_url: String,
}

impl Config {
    pub fn default() -> Self {
        Self {
            debug: false,
            tower_url: String::from(DEFAULT_TOWER_URL),
        }
    }

    pub fn from_env() -> Self {
        let debug = std::env::var("TOWER_DEBUG").is_ok();
        let tower_url = std::env::var("TOWER_URL").unwrap_or_else(|_| String::from(DEFAULT_TOWER_URL));

        Self {
            debug,
            tower_url,
        }
    }

    pub fn from_arg_matches(matches: &clap::ArgMatches) -> Self {
        let mut config = Config::from_env();

        if matches.get_flag("debug") {
            config.debug = true;
        }

        if let Some(tower_url) = matches.get_one::<String>("tower_url") {
            config.tower_url = tower_url.to_string();
        }

        config
    }
}
