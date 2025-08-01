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
pub struct RunnerCredentials {
    /// The signed certificate used by the runner to authenticate itself to Tower.
    #[serde(rename = "certificate")]
    pub certificate: String,
    /// The private key used by the runner to authenticate itself to Tower.
    #[serde(rename = "private_key")]
    pub private_key: String,
    /// The PEM encoded root CA certificate that is used to verify the runner's certificate when Tower is responsible for signing server certs.
    #[serde(rename = "root_ca", deserialize_with = "Option::deserialize")]
    pub root_ca: Option<String>,
    /// The host of the runner service that this runner will connect to. This is typically the Tower service host.
    #[serde(rename = "runner_service_url")]
    pub runner_service_url: String,
}

impl RunnerCredentials {
    pub fn new(certificate: String, private_key: String, root_ca: Option<String>, runner_service_url: String) -> RunnerCredentials {
        RunnerCredentials {
            certificate,
            private_key,
            root_ca,
            runner_service_url,
        }
    }
}

