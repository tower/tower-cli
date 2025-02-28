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
pub struct CreateAccountParamsFlagsStruct {
    #[serde(rename = "is_test_account")]
    pub is_test_account: bool,
}

impl CreateAccountParamsFlagsStruct {
    pub fn new(is_test_account: bool) -> CreateAccountParamsFlagsStruct {
        CreateAccountParamsFlagsStruct {
            is_test_account,
        }
    }
}

