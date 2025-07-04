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
pub struct CreateCatalogParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    #[serde(rename = "environment")]
    pub environment: String,
    #[serde(rename = "name")]
    pub name: String,
    #[serde(rename = "properties")]
    pub properties: Vec<models::EncryptedCatalogProperty>,
    #[serde(rename = "slug")]
    pub slug: String,
    #[serde(rename = "type")]
    pub r#type: Type,
}

impl CreateCatalogParams {
    pub fn new(environment: String, name: String, properties: Vec<models::EncryptedCatalogProperty>, slug: String, r#type: Type) -> CreateCatalogParams {
        CreateCatalogParams {
            schema: None,
            environment,
            name,
            properties,
            slug,
            r#type,
        }
    }
}
/// 
#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd, Hash, Serialize, Deserialize)]
pub enum Type {
    #[serde(rename = "snowflake-open-catalog")]
    SnowflakeOpenCatalog,
    #[serde(rename = "apache-polaris")]
    ApachePolaris,
    #[serde(rename = "cloudflare-r2-catalog")]
    CloudflareR2Catalog,
    #[serde(rename = "lakekeeper")]
    Lakekeeper,
}

impl Default for Type {
    fn default() -> Type {
        Self::SnowflakeOpenCatalog
    }
}

