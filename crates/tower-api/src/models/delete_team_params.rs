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
pub struct DeleteTeamParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// The slug of the team to delete
    #[serde(rename = "slug")]
    pub slug: String,
}

impl DeleteTeamParams {
    pub fn new(slug: String) -> DeleteTeamParams {
        DeleteTeamParams {
            schema: None,
            slug,
        }
    }
}

