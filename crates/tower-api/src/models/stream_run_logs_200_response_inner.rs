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

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum StreamRunLogs200ResponseInner {
    EventLog(models::EventLog),
    EventWarning(models::EventWarning),
}

impl Default for StreamRunLogs200ResponseInner {
    fn default() -> Self {
        Self::EventLog(Default::default())
    }
}
/// The event name.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd, Hash, Serialize)]
pub enum Event {
    #[serde(rename = "warning")]
    Warning,
}

impl Default for Event {
    fn default() -> Event {
        Self::Warning
    }
}

impl<'de> Deserialize<'de> for Event {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        match s.to_lowercase().as_str() {
            "warning" => Ok(Self::Warning),
            _ => Err(serde::de::Error::unknown_variant(
                &s,
                &["warning"],
            )),
        }
    }
}

