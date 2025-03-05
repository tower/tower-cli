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
pub struct RunAppParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    #[serde(rename = "environment")]
    pub environment: String,
    #[serde(rename = "parameters")]
    pub parameters: std::collections::HashMap<String, String>,
}

impl RunAppParams {
    pub fn new(environment: String, parameters: std::collections::HashMap<String, String>) -> RunAppParams {
        RunAppParams {
            schema: None,
            environment,
            parameters,
        }
    }
}

