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
pub struct ListAppsResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    #[serde(rename = "apps")]
    pub apps: Vec<models::AppSummary>,
    #[serde(rename = "pages")]
    pub pages: Box<models::Pagination>,
}

impl ListAppsResponse {
    pub fn new(apps: Vec<models::AppSummary>, pages: models::Pagination) -> ListAppsResponse {
        ListAppsResponse {
            schema: None,
            apps,
            pages: Box::new(pages),
        }
    }
}

