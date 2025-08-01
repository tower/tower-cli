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
pub struct SseWarning {
    /// Contents of the warning.
    #[serde(rename = "content")]
    pub content: String,
    /// Timestamp of the event.
    #[serde(rename = "reported_at")]
    pub reported_at: String,
}

impl SseWarning {
    pub fn new(content: String, reported_at: String) -> SseWarning {
        SseWarning {
            content,
            reported_at,
        }
    }
}

