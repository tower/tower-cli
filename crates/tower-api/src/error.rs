use serde::{Deserialize, Serialize};
use reqwest::Error;

#[derive(Serialize, Deserialize)]
pub struct TowerError {
    pub code: String,
    pub domain: String
}

impl From<Error> for TowerError {
    fn from(_: Error) -> Self {
        todo!()
    }
}
