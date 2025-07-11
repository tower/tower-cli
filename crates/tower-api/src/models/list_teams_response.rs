/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: v0.6.14
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct ListTeamsResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// List of teams
    #[serde(rename = "teams")]
    pub teams: Vec<models::Team>,
}

impl ListTeamsResponse {
    pub fn new(teams: Vec<models::Team>) -> ListTeamsResponse {
        ListTeamsResponse {
            schema: None,
            teams,
        }
    }
}

