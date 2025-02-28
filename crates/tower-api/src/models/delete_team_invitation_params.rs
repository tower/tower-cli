/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: development
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct DeleteTeamInvitationParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// The email address of the team member to remove
    #[serde(rename = "email")]
    pub email: String,
}

impl DeleteTeamInvitationParams {
    pub fn new(email: String) -> DeleteTeamInvitationParams {
        DeleteTeamInvitationParams {
            schema: None,
            email,
        }
    }
}

