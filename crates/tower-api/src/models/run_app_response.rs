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
pub struct RunAppResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    #[serde(rename = "run")]
    pub run: Box<models::Run>,
}

impl RunAppResponse {
    pub fn new(run: models::Run) -> RunAppResponse {
        RunAppResponse {
            schema: None,
            run: Box::new(run),
        }
    }
}

