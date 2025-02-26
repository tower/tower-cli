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
pub struct CreateTeamParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// The name of the team to create
    #[serde(rename = "name")]
    pub name: String,
    /// The slug of the team to create
    #[serde(rename = "slug")]
    pub slug: String,
}

impl CreateTeamParams {
    pub fn new(name: String, slug: String) -> CreateTeamParams {
        CreateTeamParams {
            schema: None,
            name,
            slug,
        }
    }
}

