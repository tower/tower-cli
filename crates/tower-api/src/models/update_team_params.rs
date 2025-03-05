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
pub struct UpdateTeamParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// The name of the team to create. This is optional, if you supply null it will not update the team name.
    #[serde(rename = "name", deserialize_with = "Option::deserialize")]
    pub name: Option<String>,
    /// The new slug that you want the team to use. This is optional, if you supply null it will not update the slug.
    #[serde(rename = "slug", deserialize_with = "Option::deserialize")]
    pub slug: Option<String>,
}

impl UpdateTeamParams {
    pub fn new(name: Option<String>, slug: Option<String>) -> UpdateTeamParams {
        UpdateTeamParams {
            schema: None,
            name,
            slug,
        }
    }
}

