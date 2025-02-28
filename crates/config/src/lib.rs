use serde::{Deserialize, Serialize};
use tower_api::apis::configuration::Configuration;
use tower_api::apis::configuration::Configuration;
use url::Url;
use url::Url;

mod error;
mod session;
mod towerfile;

pub use session::{default_tower_url, Session, Team, Token, User};
pub use session::{default_tower_url, Session, Team, Token, User};

pub use error::Error;
pub use towerfile::Towerfile;

#[derive(Serialize, Deserialize)]
pub struct Config {
    pub debug: bool,
    pub tower_url: Url,
    #[serde(skip_serializing, skip_deserializing)]
    pub api_configuration: Option<Configuration>,
    #[serde(skip_serializing, skip_deserializing)]
    pub api_configuration: Option<Configuration>,
}

impl Config {
    pub fn default() -> Self {
        Self {
            debug: false,
            tower_url: default_tower_url(),
            api_configuration: None,
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

    /// Gets the currently active team from the session
    /// Returns None if there's no session
    pub fn get_active_team(&self) -> Result<Option<Team>, Error> {
        // Get the session, return None if no session exists
        let mut session = match Session::from_config_dir() {
            Ok(session) => session,
            Err(Error::NoSession) => return Ok(None),
            Err(e) => return Err(e),
        };

        // If there's no active team, try to find and set a personal team
        if session.active_team.is_none() {
            if let Some(personal_team) = session
                .teams
                .iter()
                .find(|team| team.team_type == "personal")
            {
                session.active_team = Some(personal_team.clone());
            }
        }

        // Return the active team
        Ok(session.active_team)
    }

    pub fn get_teams(&self) -> Result<Vec<Team>, Error> {
        // Get the session
        let session = Session::from_config_dir()?;

        // Return the active team
        Ok(session.teams)
    }

    /// Gets the JWT token for the active team
    /// Returns None if there's no session or no active team
    pub fn get_active_team_token(&self) -> Result<Option<String>, Error> {
        // Get the session
        let session = Session::from_config_dir()?;

        // Return the active team's JWT token
        Ok(session.active_team.map(|team| team.token.jwt.clone()))
    }
}
