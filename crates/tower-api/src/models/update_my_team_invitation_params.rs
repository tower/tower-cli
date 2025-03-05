/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: v0.3.2
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct UpdateMyTeamInvitationParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// Whether or not the invitation was accepted. If false, it's considered rejected.
    #[serde(rename = "accepted")]
    pub accepted: bool,
    /// The slug of the team invitation to update
    #[serde(rename = "slug")]
    pub slug: String,
}

impl UpdateMyTeamInvitationParams {
    pub fn new(accepted: bool, slug: String) -> UpdateMyTeamInvitationParams {
        UpdateMyTeamInvitationParams {
            schema: None,
            accepted,
            slug,
        }
    }
}

