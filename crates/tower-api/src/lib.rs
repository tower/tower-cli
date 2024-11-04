use serde::{Deserialize, Serialize};
use url::Url;
use reqwest::{
    Client as ReqwestClient,
    StatusCode,
    Method,
};
use serde_json::Value;
use std::convert::From;
use config::Config;

mod types;
mod error;

// TowerError is the main error type of Tower errors. We export it here for convenience to crate
// users.
pub use error::TowerError;

// All types get exported to make our lives easier, too.
pub use types::*;

#[derive(Serialize, Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}


#[derive(Serialize, Deserialize)]
struct ListAppsResponse {
    apps: Vec<AppSummary>,
}

pub type Result<T> = std::result::Result<T, TowerError>;

pub struct Client {
    // domain is the URL that we use to connect to the client.
    domain: Url,

    // session is the current session that will be used for making subsequent requests.
    session: Option<Session>,
}

impl Client {
    pub fn default() -> Self {
        Self {
            domain: Url::parse("https://services.tower.dev").unwrap(),
            session: None,
        }
    }

    pub fn new(domain: Url) -> Self {
        Self {
            domain,
            session: None,
        }
    }

    pub fn from_config(config: &Config) -> Self {
        Self {
            session: None,
            domain: Url::parse(&config.tower_url).unwrap(),
        }
    }

    pub fn with_optional_session(&self, sess: Option<Session>) -> Self {
        Self {
            domain: self.domain.clone(),
            session: sess,
        }
    }

    pub async fn login(&self, username: &str, password: &str) -> Result<Session> {
        let data = LoginRequest { 
            username: String::from(username),
            password: String::from(password),
        };

        let body = serde_json::to_value(data).unwrap();
        self.request(Method::POST, "/api/session", Some(body)).await
    }

    pub async fn list_apps(&self) -> Result<Vec<AppSummary>> {
        let res = self.request::<ListAppsResponse>(Method::GET, "/api/apps", None).await?;
        Ok(res.apps)
    }

    async fn request<T>(&self, method: Method, path: &str, body: Option<Value>) -> Result<T>
    where
        T: for<'de> Deserialize<'de>,
    {
        let client = ReqwestClient::new();
        let url = self.url_from_path(path);
        let mut req = client.request(method, url);

        if let Some(obj) = body {
            req = req.json(&obj);
        }

        if let Some(sess) = &self.session {
            req = req.header("Authorization", format!("Bearer {}", sess.token.jwt))
        }

        let res = req.send().await?;

        match res.status() {
            StatusCode::OK | StatusCode::CREATED => {
                res.json::<T>().await.map_err(Into::into)
            }
            _ => Err(res.json::<TowerError>().await?),
        }
    }


    fn url_from_path(&self, path: &str) -> Url {
        self.domain.join(path).unwrap()
    }
}
