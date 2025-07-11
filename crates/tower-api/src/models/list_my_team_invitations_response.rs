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
pub struct ListMyTeamInvitationsResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// All of team invitations
    #[serde(rename = "team_invitations")]
    pub team_invitations: Vec<models::TeamInvitation>,
}

impl ListMyTeamInvitationsResponse {
    pub fn new(team_invitations: Vec<models::TeamInvitation>) -> ListMyTeamInvitationsResponse {
        ListMyTeamInvitationsResponse {
            schema: None,
            team_invitations,
        }
    }
}

