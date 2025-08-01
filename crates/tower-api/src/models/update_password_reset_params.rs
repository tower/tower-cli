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
pub struct UpdatePasswordResetParams {
    /// A URL to the JSON Schema for this object.
    #[serde(rename = "$schema", skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,
    /// The new password that you want to set for your account
    #[serde(rename = "password")]
    pub password: String,
}

impl UpdatePasswordResetParams {
    pub fn new(password: String) -> UpdatePasswordResetParams {
        UpdatePasswordResetParams {
            schema: None,
            password,
        }
    }
}

