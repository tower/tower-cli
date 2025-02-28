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
pub struct ListSecretEnvironmentsResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    #[serde(rename = "environments")]
    pub environments: Vec<String>,
}

impl ListSecretEnvironmentsResponse {
    pub fn new(environments: Vec<String>) -> ListSecretEnvironmentsResponse {
        ListSecretEnvironmentsResponse {
            schema: None,
            environments,
        }
    }
}

