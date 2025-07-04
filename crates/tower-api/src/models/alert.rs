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
pub struct Alert {
    #[serde(rename = "acked")]
    pub acked: bool,
    #[serde(rename = "alert_type")]
    pub alert_type: String,
    #[serde(rename = "created_at")]
    pub created_at: String,
    #[serde(rename = "detail")]
    pub detail: Box<models::RunFailureAlert>,
    #[serde(rename = "seq")]
    pub seq: i64,
    #[serde(rename = "status")]
    pub status: String,
}

impl Alert {
    pub fn new(acked: bool, alert_type: String, created_at: String, detail: models::RunFailureAlert, seq: i64, status: String) -> Alert {
        Alert {
            acked,
            alert_type,
            created_at,
            detail: Box::new(detail),
            seq,
            status,
        }
    }
}

