/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: development
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct RunResults {
    #[serde(rename = "cancelled")]
    pub cancelled: i64,
    #[serde(rename = "crashed")]
    pub crashed: i64,
    #[serde(rename = "errored")]
    pub errored: i64,
    #[serde(rename = "exited")]
    pub exited: i64,
    #[serde(rename = "pending")]
    pub pending: i64,
    #[serde(rename = "running")]
    pub running: i64,
}

impl RunResults {
    pub fn new(cancelled: i64, crashed: i64, errored: i64, exited: i64, pending: i64, running: i64) -> RunResults {
        RunResults {
            cancelled,
            crashed,
            errored,
            exited,
            pending,
            running,
        }
    }
}

