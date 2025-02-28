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
pub struct DeployAppResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    #[serde(rename = "version")]
    pub version: Box<models::AppVersion>,
}

impl DeployAppResponse {
    pub fn new(version: models::AppVersion) -> DeployAppResponse {
        DeployAppResponse {
            schema: None,
            version: Box::new(version),
        }
    }
}

