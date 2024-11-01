use serde::{Deserialize, Serialize};
pub use chrono::{DateTime, Utc};

pub use config::{
    User,
    Token,
    Session,
};

#[derive(Serialize, Deserialize)]
pub struct App{
    pub name: String,
    pub short_description: String,
    pub owner: String,
    pub created_at: DateTime<Utc>,
}
