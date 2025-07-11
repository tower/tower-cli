/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: v0.6.14
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct DeleteCatalogResponse {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    #[serde(rename = "catalog")]
    pub catalog: Box<models::Catalog>,
}

impl DeleteCatalogResponse {
    pub fn new(catalog: models::Catalog) -> DeleteCatalogResponse {
        DeleteCatalogResponse {
            schema: None,
            catalog: Box::new(catalog),
        }
    }
}

