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
pub struct ListRunsResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    #[serde(rename = "pages")]
    pub pages: Box<models::Pagination>,
    #[serde(rename = "runs")]
    pub runs: Vec<models::Run>,
}

impl ListRunsResponse {
    pub fn new(pages: models::Pagination, runs: Vec<models::Run>) -> ListRunsResponse {
        ListRunsResponse {
            schema: None,
            pages: Box::new(pages),
            runs,
        }
    }
}

