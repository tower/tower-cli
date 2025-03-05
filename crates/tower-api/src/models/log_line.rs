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
pub struct LogLine {
    /// Contents of the log message.
    #[serde(rename = "content")]
    pub content: String,
    /// Line number.
    #[serde(rename = "line_num")]
    pub line_num: i64,
    /// Timestamp of the log line.
    #[serde(rename = "reported_at")]
    pub reported_at: String,
    /// The uuid of the Run.
    #[serde(rename = "run_id")]
    pub run_id: String,
}

impl LogLine {
    pub fn new(content: String, line_num: i64, reported_at: String, run_id: String) -> LogLine {
        LogLine {
            content,
            line_num,
            reported_at,
            run_id,
        }
    }
}

