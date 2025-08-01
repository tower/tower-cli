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
pub struct InviteTeamMemberResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// The team invitation that you created
    #[serde(rename = "team_invitations")]
    pub team_invitations: Vec<models::TeamInvitation>,
}

impl InviteTeamMemberResponse {
    pub fn new(team_invitations: Vec<models::TeamInvitation>) -> InviteTeamMemberResponse {
        InviteTeamMemberResponse {
            schema: None,
            team_invitations,
        }
    }
}

