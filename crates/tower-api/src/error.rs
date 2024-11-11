use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct DetailedString {
    pub friendly: String,
    pub technical: String,
}

impl DetailedString {
    pub fn new(friendly: &str, technical: &str) -> Self {
        Self {
            friendly: friendly.to_string(),
            technical: technical.to_string(),
        }
    }

    pub fn from_string(s: &str) -> Self {
        Self {
            friendly: s.to_string(),
            technical: s.to_string(),
        }
    }
}

#[derive(Serialize, Deserialize)]
pub struct TowerError {
    pub code: String,
    pub domain: String,
    pub description: DetailedString,
    pub formatted: DetailedString,
}

impl From<reqwest::Error> for TowerError {
    fn from(err: reqwest::Error) -> Self {
        if err.is_redirect() {
            Self {
                code: "tower_api_client_redirect_error".to_string(),
                domain: "tower_api_client".to_string(),
                description: DetailedString::from_string("The Tower API is redirecting your request in a way that Tower CLI cannot handle"),
                formatted: DetailedString::from_string("The Tower API is redirecting your request in a way that Tower CLI cannot handle"),
            }
        } else if err.is_status() {
            let line = format!("An unexpected status code (status code: {}) was returned from the Tower API", err.status().unwrap());

            Self {
                code: "tower_api_client_status_error".to_string(),
                domain: "tower_api_client".to_string(),
                description: DetailedString::from_string(&line),
                formatted: DetailedString::from_string(&line),
            }
        } else if err.is_connect() {
            Self {
                code: "tower_api_client_connect_error".to_string(),
                domain: "tower_api_client".to_string(),
                description: DetailedString::from_string("A connection to the Tower API could not be established"),
                formatted: DetailedString::from_string("A connection to the Tower API could not be established"),
            }
        } else if err.is_body() {
            Self {
                code: "tower_api_client_body_error".to_string(),
                domain: "tower_api_client".to_string(),
                description: DetailedString::from_string("There was something wrong with the body of the response from the Tower API"),
                formatted: DetailedString::from_string("There was something wrong with the body of the response from the Tower API"),
            }
        } else if err.is_decode() {
            log::debug!("failed to decode the body: {:?}", err);

            // TODO: This means there was something critically wrong with how we're using the API.
            // Perhaps this should be a more serious error?
            Self {
                code: "tower_api_client_decode_error".to_string(),
                domain: "tower_api_client".to_string(),
                description: DetailedString::from_string("There was an error decoding the response from the Tower API"),
                formatted: DetailedString::from_string("There was an error decoding the response from the Tower API"),
            }
        } else if err.is_builder() {
            Self {
                code: "tower_api_client_builder_error".to_string(),
                domain: "tower_api_client".to_string(),
                description: DetailedString::from_string("There was an unexpected internal error in the Tower CLI request builder"),
                formatted: DetailedString::from_string("There was an unexpected internal error in the Tower CLI request builder"),
            }
        } else if err.is_timeout() {
            Self {
                code: "tower_api_client_timeout_error".to_string(),
                domain: "tower_api_client".to_string(),
                description: DetailedString::from_string("A request to the Tower API timed out"),
                formatted: DetailedString::from_string("A request to the Tower API timed out"),
            }
        } else {
            log::debug!("Unexpected error: {:?}", err);

            Self {
                code: "tower_api_client_error".to_string(),
                domain: "tower_api_client".to_string(),
                description: DetailedString::from_string("An unexpected or unknown error occured!"),
                formatted: DetailedString::from_string("An unexpected or unknown error occured!"),
            }   
        }
    }
}

impl From<pem::PemError> for TowerError {
    fn from(err: pem::PemError) -> Self {
        log::debug!("Error decoding PEM: {:?}", err);

        Self {
            code: "tower_api_client_error".to_string(),
            domain: "tower_api_client".to_string(),
            description: DetailedString::from_string("An unexpected or unknown error occured!"),
            formatted: DetailedString::from_string("An unexpected or unknown error occured!"),
        }   
    }
}

impl From<rsa::pkcs1::Error> for TowerError {
    fn from(err: rsa::pkcs1::Error) -> Self {
        log::debug!("Error parsing RSA public key: {:?}", err);

        Self {
            code: "tower_api_client_error".to_string(),
            domain: "tower_api_client".to_string(),
            description: DetailedString::from_string("An unexpected or unknown error occured!"),
            formatted: DetailedString::from_string("An unexpected or unknown error occured!"),
        }   
    }
}

impl From<serde_json::Error> for TowerError {
    fn from(err: serde_json::Error) -> Self {
        log::debug!("error decoding JSON: {:?}", err);

        Self {
            code: "tower_api_client_error".to_string(),
            domain: "tower_api_client".to_string(),
            description: DetailedString::from_string("An unexpected or unknown error occured!"),
            formatted: DetailedString::from_string("An unexpected or unknown error occured!"),
        }   
    }
}

impl From<std::io::Error> for TowerError {
    fn from(err: std::io::Error) -> Self {
        log::debug!("error reading a file: {:?}", err);

        Self {
            code: "tower_api_client_error".to_string(),
            domain: "tower_api_client".to_string(),
            description: DetailedString::from_string("An unexpected or unknown error occured!"),
            formatted: DetailedString::from_string("An unexpected or unknown error occured!"),
        }   
    }
}

impl std::fmt::Display for TowerError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result{
        write!(f, "TowerError (code: {}) {}", self.code, self.description.technical)
    }
}
