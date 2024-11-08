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
use rsa::{
    RsaPublicKey,
    pkcs1::DecodeRsaPublicKey,
};

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

#[derive(Serialize, Deserialize)]
struct CreateAppRequest {
    name: String,
    short_description: String,
}

#[derive(Serialize, Deserialize)]
struct CreateAppResponse {
    app: App,
}

#[derive(Serialize, Deserialize)]
struct DeleteAppResponse {
    app: App,
}

#[derive(Serialize, Deserialize)]
struct ListSecretsResponse {
    secrets: Vec<Secret>,
}

#[derive(Serialize, Deserialize)]
struct DeleteSecretRequest {
    name: String
}

#[derive(Serialize, Deserialize)]
struct DeleteSecretResponse {
    secret: Secret,
}

#[derive(Serialize, Deserialize)]
struct SecretsKeyResponse {
    /// public_key is a PEM-encoded RSA public key that can be used to encrypt secrets.
    public_key: String,
}

#[derive(Serialize, Deserialize)]
struct CreateSecretRequest {
    name: String,
    encrypted_value: String,
    preview: String,
}

#[derive(Serialize, Deserialize)]
struct CreateSecretResponse {
    secret: Secret,
}

#[derive(Serialize, Deserialize)]
struct ExportSecretsRequest {
    public_key: String,
}

#[derive(Serialize, Deserialize)]
struct ExportSecretsResponse {
    #[serde(deserialize_with="parse_nullable_sequence")]
    secrets: Vec<EncryptedSecret>,
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

    pub async fn delete_app(&self, name: &str) -> Result<App> {
        let path = format!("/api/apps/{}", name);
        let res = self.request::<DeleteAppResponse>(Method::DELETE, &path, None).await?;
        Ok(res.app)
    }

    pub async fn create_app(&self, name: &str, description: &str) -> Result<App> {
        let data = CreateAppRequest {
            name: String::from(name),
            short_description: String::from(description),
        };

        let body = serde_json::to_value(data).unwrap();
        let res = self.request::<CreateAppResponse>(Method::POST, "/api/apps", Some(body)).await?;
        Ok(res.app)
    }

    pub async fn list_secrets(&self) -> Result<Vec<Secret>> {
        let res = self.request::<ListSecretsResponse>(Method::GET, "/api/secrets", None).await?;
        Ok(res.secrets)
    }

    pub async fn delete_secret(&self, name: &str) -> Result<Secret> {
        let data = DeleteSecretRequest {
            name: String::from(name),
        };

        let body = serde_json::to_value(data).unwrap();
        let res = self.request::<DeleteSecretResponse>(Method::DELETE, "/api/secrets", Some(body)).await?;
        Ok(res.secret)
    }

    pub async fn secrets_key(&self) -> Result<RsaPublicKey> {
        let res = self.request::<SecretsKeyResponse>(Method::GET, "/api/secrets/key", None).await?;
        let decoded = pem::parse(res.public_key)?;
        let public_key = RsaPublicKey::from_pkcs1_der(&decoded.contents())?;
        Ok(public_key)
    }

    pub async fn create_secret(&self, name: &str, encrypted_value: &str, preview: &str) -> Result<Secret> {
        let data = CreateSecretRequest {
            name: String::from(name),
            encrypted_value: String::from(encrypted_value),
            preview: String::from(preview),
        };

        let body = serde_json::to_value(data).unwrap();
        let res = self.request::<CreateSecretResponse>(Method::POST, "/api/secrets", Some(body)).await?;
        Ok(res.secret)
    }

    pub async fn export_secrets(&self) -> Result<Vec<ExportedSecret>> {
        let (private_key, public_key) = crypto::generate_key_pair();

        let data = ExportSecretsRequest {
            public_key: crypto::serialize_public_key(public_key),
        };

        let body = serde_json::to_value(data).unwrap();
        let res = self.request::<ExportSecretsResponse>(Method::POST, "/api/secrets/export", Some(body)).await?;

        let secrets = res.secrets.iter().map(|secret| {
            let encrypted_value = secret.encrypted_value.clone();
            let decrypted = crypto::decrypt(private_key.clone(), encrypted_value);

            ExportedSecret {
                name: secret.name.clone(),
                value: decrypted,
                created_at: secret.created_at,
            }
        }).collect();

        Ok(secrets)
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
            _ => {
                Err(res.json::<TowerError>().await?)
            }
        }
    }


    fn url_from_path(&self, path: &str) -> Url {
        self.domain.join(path).unwrap()
    }
}
