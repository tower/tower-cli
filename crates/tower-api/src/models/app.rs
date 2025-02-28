/*
 * Tower API
 *
 * REST API to interact with Tower Services.
 *
 * The version of the OpenAPI document: v0.3.0
 * Contact: hello@tower.dev
 * Generated by: https://openapi-generator.tech
 */

use crate::models;
use serde::{Deserialize, Serialize};

#[derive(Clone, Default, Debug, PartialEq, Serialize, Deserialize)]
pub struct App {
    /// The date and time this app was created.
    #[serde(rename = "created_at")]
    pub created_at: String,
    /// The last run of this app, null if none.
    #[serde(rename = "last_run", skip_serializing_if = "Option::is_none")]
    pub last_run: Option<Box<models::Run>>,
    /// The name of the app.
    #[serde(rename = "name")]
    pub name: String,
    /// The next time this app will run as part of it's schedule, null if none.
    #[serde(rename = "next_run_at", deserialize_with = "Option::deserialize")]
    pub next_run_at: Option<String>,
    /// The account slug that owns this app
    #[serde(rename = "owner")]
    pub owner: String,
    /// The schedule associated with this app, null if none.
    #[serde(rename = "schedule", deserialize_with = "Option::deserialize")]
    pub schedule: Option<String>,
    /// A short description of the app. Can be empty.
    #[serde(rename = "short_description")]
    pub short_description: String,
    /// The current version of this app, null if none.
    #[serde(rename = "version", deserialize_with = "Option::deserialize")]
    pub version: Option<String>,
}

impl App {
    pub fn new(created_at: String, name: String, next_run_at: Option<String>, owner: String, schedule: Option<String>, short_description: String, version: Option<String>) -> App {
        App {
            created_at,
            last_run: None,
            name,
            next_run_at,
            owner,
            schedule,
            short_description,
            version,
        }
    }
}

