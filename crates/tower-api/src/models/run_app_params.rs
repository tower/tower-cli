/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: v0.6.27
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize, Deserializer};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct RunAppParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// The environment to run this app in.
    #[serde(rename = "environment")]
    pub environment: String,
    /// The parameters to pass into this app.
    #[serde(rename = "parameters")]
    pub parameters: std::collections::HashMap<String, String>,
    /// The ID of the run that invoked this run, if relevant. Should be null, if none.
    #[serde(rename = "parent_run_id", default, with = "::serde_with::rust::double_option", skip_serializing_if = "Option::is_none")]
    pub parent_run_id: Option<Option<String>>,
}

impl RunAppParams {
    pub fn new(environment: String, parameters: std::collections::HashMap<String, String>) -> RunAppParams {
        RunAppParams {
            schema: None,
            environment,
            parameters,
            parent_run_id: None,
        }
    }
}

