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
pub struct Pagination {
    #[serde(rename = "num_pages")]
    pub num_pages: i64,
    #[serde(rename = "page")]
    pub page: i64,
    #[serde(rename = "page_size")]
    pub page_size: i64,
    #[serde(rename = "total")]
    pub total: i64,
}

impl Pagination {
    pub fn new(num_pages: i64, page: i64, page_size: i64, total: i64) -> Pagination {
        Pagination {
            num_pages,
            page,
            page_size,
            total,
        }
    }
}

