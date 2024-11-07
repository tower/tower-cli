use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

use crate::error::Error;

#[derive(Clone, Serialize, Deserialize)]
pub struct User {
    pub email: String,
    pub created_at: String,
}

#[derive(Clone, Serialize, Deserialize)]
pub struct Token {
    pub jwt: String,
}

#[derive(Clone, Serialize, Deserialize)]
pub struct Session {
    pub user: User,
    pub token: Token,
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
    pub fn new(user: User, token: Token) -> Self {
        Self {
            user,
            token,
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
}
