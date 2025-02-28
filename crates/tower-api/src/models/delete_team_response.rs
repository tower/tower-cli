/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: v0.3.0
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct DeleteTeamResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// The team that was just created
    #[serde(rename = "team")]
    pub team: Box<models::Team>,
}

impl DeleteTeamResponse {
    pub fn new(team: models::Team) -> DeleteTeamResponse {
        DeleteTeamResponse {
            schema: None,
            team: Box::new(team),
        }
    }
}

