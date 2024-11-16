use url::Url;
use serde::{Deserialize, Serialize};

mod error;
mod session;
mod towerfile;

pub use session::{
    default_tower_url,
    User,
    Token,
    Session,
};

pub use error::Error;
pub use towerfile::Towerfile;

#[derive(Serialize, Deserialize)]
pub struct Config {
    pub debug: bool,
    pub tower_url: Url,
}

impl Config {
    pub fn default() -> Self {
        Self {
            debug: false,
            tower_url: default_tower_url(),
        }
    }

    pub fn from_env() -> Self {
        let debug = std::env::var("TOWER_DEBUG").is_ok();
        let tower_url = if let Some(url) = std::env::var("TOWER_URL").ok() {
            Url::parse(&url).unwrap()
        } else {
            default_tower_url()
        };

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
            config.tower_url = Url::parse(tower_url).unwrap();
        }

        config
    }
}
