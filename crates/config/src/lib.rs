use url::Url;
use serde::{Deserialize, Serialize};
use tower_api::apis::configuration::Configuration;

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
    #[serde(skip_serializing, skip_deserializing)]
    pub api_configuration: Option<Configuration>
}

impl Config {
    pub fn default() -> Self {
        Self {
            debug: false,
            tower_url: default_tower_url(),
            api_configuration: None,
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
            api_configuration: None,
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

    /// Initializes the API configuration for this Config
    /// 
    /// If a session is provided, the authentication token will be included
    /// 
    /// Stores the configuration in self.api_configuration
    pub fn init_api_configuration(&mut self, session: Option<&Session>) {
        let mut configuration = Configuration::new();
        
        // Set the base path from tower_url
        configuration.base_path = self.tower_url.clone().to_string();
        
        // Add session token if available
        if let Some(session) = session {
            configuration.bearer_access_token = Some(session.token.jwt.clone());
        }
        
        // Store the configuration in self
        self.api_configuration = Some(configuration);
    }
    
    /// Returns a reference to the current API configuration if it exists
    pub fn get_api_configuration(&self) -> Option<&Configuration> {
        self.api_configuration.as_ref()
    }
}
