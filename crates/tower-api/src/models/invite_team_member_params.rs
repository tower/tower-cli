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
pub struct InviteTeamMemberParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// The email addresses of the people to invite. It can be a list in any format (comma separated, newline separated, etc.) and it will be parsed into individual addresses
    #[serde(rename = "emails")]
    pub emails: String,
}

impl InviteTeamMemberParams {
    pub fn new(emails: String) -> InviteTeamMemberParams {
        InviteTeamMemberParams {
            schema: None,
            emails,
        }
    }
}

