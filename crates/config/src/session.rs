use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use url::Url;

use crate::error::Error;

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
    pub slug: String,
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
}
