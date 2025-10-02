use serde::{Deserialize, Serialize};
use tower_api::apis::configuration::Configuration;
use url::Url;

mod error;
mod session;
mod towerfile;

pub use error::Error;
pub use session::{default_tower_url, Session, Team, Token, User};
pub use towerfile::Towerfile;

pub use session::{get_last_version_check_timestamp, set_last_version_check_timestamp};

#[derive(Clone, Serialize, Deserialize)]
pub struct Config {
    pub debug: bool,
    pub tower_url: Url,
    pub json: bool,

    #[serde(skip_serializing, skip_deserializing)]
    pub session: Option<Session>,
}

impl Config {
    pub fn default() -> Self {
        Self {
            debug: false,
            tower_url: default_tower_url(),
            json: false,
            session: None,
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
            json: false,
            session: None,
        }
    }

    pub fn from_arg_matches(matches: &clap::ArgMatches) -> Self {
        let mut config = Config::from_env();

        if matches.get_flag("debug") {
            config.debug = true;
        }

        if matches.get_flag("json") {
            config.json = true;
        }

        if let Some(tower_url) = matches.get_one::<String>("tower_url") {
            config.tower_url = Url::parse(tower_url).unwrap();
        }

        config
    }

    pub fn with_session(self, sess: Session) -> Config {
        Self {
            debug: self.debug,
            tower_url: sess.tower_url.clone(),
            json: self.json,
            session: Some(sess),
        }
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
                session.save()?;
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

    /// Sets the active team in the session and saves it
    pub fn set_active_team(&self, team: Team) -> Result<(), Error> {
        // Get the current session
        let mut session = Session::from_config_dir()?;

        // Set the active team
        session.active_team = Some(team);

        // Save the updated session
        session.save()?;

        Ok(())
    }

    /// Sets the active team in the session by team slug and saves it
    pub fn set_active_team_by_name(&self, name: &str) -> Result<(), Error> {
        // Get the current session
        let mut session = Session::from_config_dir()?;

        // Find the team with the matching slug
        let team = session
            .teams
            .iter()
            .find(|team| team.name == name)
            .cloned()
            .ok_or(Error::TeamNotFound {
                team_name: name.to_string(),
            })?;

        // Set the active team
        session.active_team = Some(team);

        // Save the updated session
        session.save()?;

        Ok(())
    }

    /// Gets the current session from the config directory
    /// Returns Error if no session exists or there's an issue loading it
    pub fn get_current_session(&self) -> Result<Session, Error> {
        Session::from_config_dir()
    }

    /// make_api_configuration takes the current Tower configuration and returns a configuration
    /// that can be used by the API. It's mostly just used in converting to/from a Configuration.
    fn make_api_configuration(&self) -> Configuration {
        let mut configuration = Configuration::new();

        // Set the base path from tower_url
        let mut base_path = self.tower_url.clone();
        base_path.set_path("/v1");

        configuration.base_path = base_path.to_string();

        if let Some(session) = &self.session {
            if let Some(active_team) = &session.active_team {
                // Use the active team's JWT token
                configuration.bearer_access_token = Some(active_team.token.jwt.clone());
            } else {
                // Fall back to session token if no active team
                configuration.bearer_access_token = Some(session.token.jwt.clone());
            }
        }

        // Store the configuration in self
        configuration
    }
}

impl From<Config> for Configuration {
    fn from(config: Config) -> Configuration {
        config.make_api_configuration()
    }
}

impl From<&Config> for Configuration {
    fn from(config: &Config) -> Configuration {
        config.make_api_configuration()
    }
}
