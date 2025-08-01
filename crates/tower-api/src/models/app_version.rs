/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: v0.6.27
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize, Deserializer};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct AppVersion {
    #[serde(rename = "created_at")]
    pub created_at: String,
    #[serde(rename = "parameters")]
    pub parameters: Vec<models::Parameter>,
    /// The Towerfile that this version was created from.
    #[serde(rename = "towerfile")]
    pub towerfile: String,
    #[serde(rename = "version")]
    pub version: String,
}

impl AppVersion {
    pub fn new(created_at: String, parameters: Vec<models::Parameter>, towerfile: String, version: String) -> AppVersion {
        AppVersion {
            created_at,
            parameters,
            towerfile,
            version,
        }
    }
}

