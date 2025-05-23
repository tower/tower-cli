/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: v0.5.12
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct AlertDetail {
    #[serde(rename = "description")]
    pub description: String,
    #[serde(rename = "name")]
    pub name: String,
}

impl AlertDetail {
    pub fn new(description: String, name: String) -> AlertDetail {
        AlertDetail {
            description,
            name,
        }
    }
}

