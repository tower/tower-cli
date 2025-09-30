use chrono::{DateTime, TimeZone, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::future::Future;
use std::path::PathBuf;
use url::Url;

use crate::error::Error;
use tower_api::apis::default_api::describe_session;
use tower_telemetry::debug;

const DEFAULT_TOWER_URL: &str = "https://api.tower.dev";

pub fn default_tower_url() -> Url {
    Url::parse(DEFAULT_TOWER_URL).unwrap()
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct User {
    pub email: String,
    pub first_name: String,
    pub last_name: String,
    pub created_at: String,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Token {
    pub jwt: String,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Team {
    pub name: String,
    pub token: Token,
    pub team_type: String,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Session {
    // tower_url is the URL of the Tower API that this session was created with. This is useful
    // when the user is using multiple Tower instances. We don't want people to modify these on
    // their own, really.
    #[serde(default = "default_tower_url")]
    pub tower_url: Url,

    pub user: User,
    pub token: Token,

    // The currently active team
    pub active_team: Option<Team>,

    // List of teams the user belongs to
    #[serde(default)]
    pub teams: Vec<Team>,
}

fn find_or_create_config_dir() -> Result<PathBuf, Error> {
    let home = dirs::home_dir().ok_or(Error::NoHomeDir)?;
    let config_dir = home.join(".config").join("tower");

    // if this does exist, but it's a file, let's clean up. this will upgrade legacy users.
    if config_dir.is_file() {
        fs::remove_file(&config_dir)?;
    }

    if !config_dir.exists() {
        fs::create_dir_all(&config_dir)?;
    }

    Ok(config_dir)
}

pub fn get_last_version_check_timestamp() -> DateTime<Utc> {
    let default: DateTime<Utc> = Utc.timestamp_opt(0, 0).unwrap();

    // Look up (in the config dir) when the last version check was done. It's stored in a file
    // called last_version_check.txt and contains a chrono::DateTime timestamp in ISO 8601 format.
    match find_or_create_config_dir() {
        Ok(path) => {
            if let Ok(last_version_check) = fs::read_to_string(path.join("last_version_check.txt"))
            {
                if let Ok(dt) = DateTime::parse_from_rfc3339(&last_version_check) {
                    dt.into()
                } else {
                    debug!(
                        "Error parsing last version check timestamp: {}",
                        last_version_check
                    );
                    default
                }
            } else {
                debug!("Error reading last version check timestamp");
                default
            }
        }
        Err(err) => {
            debug!("Error finding config dir: {}", err);
            default
        }
    }
}

pub fn set_last_version_check_timestamp(dt: DateTime<Utc>) {
    match find_or_create_config_dir() {
        Ok(path) => {
            let dt_str = dt.to_rfc3339();

            if let Err(err) = fs::write(path.join("last_version_check.txt"), dt_str) {
                debug!("Error writing last version check timestamp: {}", err);
            }
        }
        Err(err) => {
            debug!("Error finding config dir: {}", err);
        }
    }
}

impl Session {
    pub fn new(user: User, token: Token, teams: Vec<Team>) -> Self {
        Self {
            tower_url: default_tower_url(),
            user,
            token,
            active_team: None,
            teams,
        }
    }

    pub fn from_config_dir() -> Result<Self, Error> {
        let config_dir = find_or_create_config_dir()?;
        let session_file = config_dir.join("session.json");

        if !session_file.exists() {
            return Err(Error::NoSession);
        }

        let session = fs::read_to_string(session_file)?;
        let session: Session = serde_json::from_str(&session)?;

        Ok(session)
    }

    pub fn save(&self) -> Result<(), Error> {
        let config_dir = find_or_create_config_dir()?;
        let session_file = config_dir.join("session.json");

        let session = serde_json::to_string(self)?;

        fs::write(session_file, session)?;

        Ok(())
    }

    /// Sets the active team based on a JWT token
    /// Returns true if a matching team was found and set as active, false otherwise
    pub fn set_active_team_by_jwt(&mut self, jwt: &str) -> bool {
        // Find the team with the matching JWT
        if let Some(team) = self.teams.iter().find(|team| team.token.jwt == jwt) {
            self.active_team = Some(team.clone());
            true
        } else {
            false
        }
    }

    /// Updates the session with data from the API response
    pub fn update_from_api_response(
        &mut self,
        refresh_response: &tower_api::models::RefreshSessionResponse,
    ) -> Result<(), Error> {
        // The session data is inside the session field of the refresh response
        let session_response = &refresh_response.session;

        // Update user information
        self.user = User {
            email: session_response.user.email.clone(),
            first_name: session_response.user.first_name.clone(),
            last_name: session_response.user.last_name.clone(),
            created_at: session_response.user.created_at.clone(),
        };

        // Update token
        self.token = Token {
            jwt: session_response.token.jwt.clone(),
        };

        // Remember the current active team's JWT if there is one
        let active_team_jwt = self.active_team.as_ref().map(|team| team.token.jwt.clone());

        // Update teams
        self.teams = session_response
            .teams
            .iter()
            .map(|team_api| Team {
                name: team_api.name.clone(),
                token: if let Some(token) = &team_api.token {
                    Token {
                        jwt: token.jwt.clone(),
                    }
                } else {
                    // Handle the None case: skip the team or provide a default token
                    Token {
                        jwt: String::new(), // Default to an empty string or handle as needed
                    }
                },
                team_type: team_api.r#type.clone(),
            })
            .collect();

        // Try to restore the active team based on the JWT
        let jwt_match_found = if let Some(jwt) = active_team_jwt {
            self.set_active_team_by_jwt(&jwt)
        } else {
            false
        };

        // If no active team was set by JWT, fall back to a personal team
        if !jwt_match_found && self.active_team.is_none() {
            // Find a team with team_type="personal"
            if let Some(personal_team) = self.teams.iter().find(|team| team.team_type == "personal")
            {
                self.active_team = Some(personal_team.clone());
            }
        }

        // Save the updated session
        self.save()?;

        Ok(())
    }

    pub fn from_api_session(session: &tower_api::models::Session) -> Self {
        let teams = session
            .teams
            .iter()
            .map(|t| Team {
                name: t.name.clone(),
                team_type: t.r#type.clone(),
                token: Token {
                    jwt: t.token.clone().unwrap().jwt.clone(),
                },
            })
            .collect();

        // Create and save the session
        let mut next_session = Session::new(
            User {
                email: session.user.email.clone(),
                created_at: session.user.created_at.clone(),
                first_name: session.user.first_name.clone(),
                last_name: session.user.last_name.clone(),
            },
            Token {
                jwt: session.token.jwt.clone(),
            },
            teams,
        );

        // Set the active team to the one matching the main session JWT
        let _ = next_session.set_active_team_by_jwt(&session.token.jwt);

        return next_session;
    }

    pub fn from_jwt(jwt: &str) -> Result<Self, Error> {
        // We need to instantiate our own configuration object here, instead of the typical thing
        // that we do which is turn a Config into a Configuration.
        let mut config = tower_api::apis::configuration::Configuration::new();
        config.bearer_access_token = Some(jwt.to_string());

        // We only pull TOWER_URL out of the environment here because we only ever use the JWT and
        // all that in programmatic contexts (when TOWER_URL is set).
        let tower_url = if let Ok(val) = std::env::var("TOWER_URL") {
            val
        } else {
            DEFAULT_TOWER_URL.to_string()
        };

        // Setup the base path to point to the /v1 API endpoint as expected.
        let mut base_path = Url::parse(&tower_url).unwrap();
        base_path.set_path("/v1");

        config.base_path = base_path.to_string();

        // This is a bit of a hairy thing: I didn't want to pull in too much from the Tower API
        // client, so we're using the raw bindings here.
        match run_future_sync(describe_session(&config)) {
            Ok(resp) => {
                // Now we need to extract the session from the response.
                let entity = resp.entity.unwrap();

                match entity {
                    tower_api::apis::default_api::DescribeSessionSuccess::Status200(resp) => {
                        let mut session = Session::from_api_session(&resp.session);
                        session.tower_url = base_path;
                        Ok(session)
                    }
                    tower_api::apis::default_api::DescribeSessionSuccess::UnknownValue(val) => {
                        debug!("Unknown value while describing session: {}", val);
                        Err(Error::UnknownDescribeSessionValue { value: val })
                    }
                }
            }
            Err(err) => {
                debug!("Error describing session: {}", err);
                Err(Error::DescribeSessionError { err })
            }
        }
    }
}

// This hairy little function is a workaround for the fact that we can't use async/await in the
// context of some of the functions in this file.
fn run_future_sync<F, T>(future: F) -> T
where
    F: Future<Output = T>,
{
    tokio::task::block_in_place(|| tokio::runtime::Handle::current().block_on(future))
}
