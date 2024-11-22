use serde::{Deserialize, Serialize};
use url::Url;
use reqwest::{
    Body,
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
use std::collections::HashMap;
use tokio::fs::File;
use futures_util::stream::Stream;
use tokio_util::io::ReaderStream;
use tower_package::Package;

mod types;
mod error;
mod progress_stream;

// TowerError is the main error type of Tower errors. We export it here for convenience to crate
// users.
pub use error::TowerError;

// All types get exported to make our lives easier, too.
pub use types::*;

use progress_stream::ProgressStream;
pub use progress_stream::ProgressCallback;

#[derive(Serialize, Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Serialize, Deserialize)]
struct ListAppsResponse {
    #[serde(deserialize_with="parse_nullable_sequence")]
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
    environment: Option<String>,
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
    environment: Option<String>,
    all: bool,
}

#[derive(Serialize, Deserialize)]
struct ExportSecretsResponse {
    #[serde(deserialize_with="parse_nullable_sequence")]
    secrets: Vec<EncryptedSecret>,
}

#[derive(Serialize, Deserialize)]
struct UploadCodeResponse {
    code: Code,
}

#[derive(Serialize, Deserialize)]
struct AppRunRequest {
    parameters: HashMap<String, String>,
    environment: String,
}

#[derive(Serialize, Deserialize)]
struct AppRunResponse {
    run: Run,
}

#[derive(Serialize, Deserialize)]
struct GetAppResponse {
    app: App,

    #[serde(deserialize_with="parse_nullable_sequence")]
    runs: Vec<Run>,
}

pub type Result<T> = std::result::Result<T, TowerError>;

type StreamResult<T> = std::result::Result<T, std::io::Error>;

pub struct Client {
    // tower_url is the URL that we use to connect to the client.
    tower_url: Url,

    // session is the current session that will be used for making subsequent requests.
    session: Option<Session>,
}

impl Client {
    pub fn default() -> Self {
        Self {
            tower_url: config::default_tower_url(),
            session: None,
        }
    }

    pub fn new(tower_url: Url) -> Self {
        Self {
            tower_url,
            session: None,
        }
    }

    pub fn from_config(config: &Config) -> Self {
        Self {
            session: None,
            tower_url: config.tower_url.clone(),
        }
    }

    pub fn with_optional_session(&self, sess: Option<Session>) -> Self {
        let tower_url = if let Some(sess) = &sess {
            sess.tower_url.clone()
        } else {
            self.tower_url.clone()
        };

        Self {
            tower_url,
            session: sess,
        }
    }
    
    pub fn with_tower_url(&self, tower_url: Url) -> Self {
        Self {
            tower_url,
            session: self.session.clone(),
        }
    }

    pub fn anonymous(&self) -> Self {
        Self {
            tower_url: self.tower_url.clone(),
            session: None,
        }
    }

    pub async fn device_login(&self) -> Result<DeviceLoginTicket> {
        let res = self.request_object(Method::GET, "/api/login/device", None, None).await?;
        Ok(res)
    }

    pub async fn check_device_login(&self, device_code: &str) -> Result<Session> {
        let path = format!("/api/login/device/{}", device_code);
        let res = self.request_object(Method::GET, &path, None, None).await?;
        Ok(res)
    }

    pub async fn login(&self, username: &str, password: &str) -> Result<Session> {
        let data = LoginRequest { 
            username: String::from(username),
            password: String::from(password),
        };

        let body = serde_json::to_value(data).unwrap();
        self.request_object(Method::POST, "/api/session", Some(body), None).await
    }

    pub async fn list_apps(&self) -> Result<Vec<AppSummary>> {
        let res = self.request_object::<ListAppsResponse>(Method::GET, "/api/apps", None, None).await?;
        Ok(res.apps)
    }

    pub async fn get_app(&self, name: &str) -> Result<(App, Vec<Run>)> {
        let path = format!("/api/apps/{}", name);
        let res = self.request_object::<GetAppResponse>(Method::GET, &path, None, None).await?;
        Ok((res.app, res.runs))
    }

    pub async fn delete_app(&self, name: &str) -> Result<App> {
        let path = format!("/api/apps/{}", name);
        let res = self.request_object::<DeleteAppResponse>(Method::DELETE, &path, None, None).await?;
        Ok(res.app)
    }

    pub async fn create_app(&self, name: &str, description: &str) -> Result<App> {
        let data = CreateAppRequest {
            name: String::from(name),
            short_description: String::from(description),
        };

        let body = serde_json::to_value(data).unwrap();
        let res = self.request_object::<CreateAppResponse>(Method::POST, "/api/apps", Some(body), None).await?;
        Ok(res.app)
    }

    /// list_secrets returns a list of secrets that are stored in the Tower instance. The optional
    /// `env` parameter can be used to include the secrets for a certain environment.
    pub async fn list_secrets(&self, all: bool, env: Option<String>) -> Result<Vec<Secret>> {
        let path = if all {
            "/api/secrets?all=true".to_string()
        } else if let Some(env) = env {
            format!("/api/secrets?environment={}", env)
        } else {
            "/api/secrets".to_string()
        };

        let res = self.request_object::<ListSecretsResponse>(Method::GET, &path, None, None).await?;
        Ok(res.secrets)
    }

    pub async fn delete_secret(&self, name: &str) -> Result<Secret> {
        let data = DeleteSecretRequest {
            name: String::from(name),
        };

        let body = serde_json::to_value(data).unwrap();
        let res = self.request_object::<DeleteSecretResponse>(Method::DELETE, "/api/secrets", Some(body), None).await?;
        Ok(res.secret)
    }

    pub async fn secrets_key(&self) -> Result<RsaPublicKey> {
        let res = self.request_object::<SecretsKeyResponse>(Method::GET, "/api/secrets/key", None, None).await?;
        let decoded = pem::parse(res.public_key)?;
        let public_key = RsaPublicKey::from_pkcs1_der(&decoded.contents())?;
        Ok(public_key)
    }

    pub async fn create_secret(&self, name: &str, encrypted_value: &str, preview: &str, environment: &str) -> Result<Secret> {
        let data = CreateSecretRequest {
            name: String::from(name),
            environment: Some(String::from(environment)),
            encrypted_value: String::from(encrypted_value),
            preview: String::from(preview),
        };

        let body = serde_json::to_value(data).unwrap();
        let res = self.request_object::<CreateSecretResponse>(Method::POST, "/api/secrets", Some(body), None).await?;
        Ok(res.secret)
    }

    /// export_secrets returns a list of secrets that are stored in the Tower instance. The
    /// optional `env` parameter can be used to include the secrets for a certain environment.
    pub async fn export_secrets(&self, all: bool, env: Option<String>) -> Result<Vec<ExportedSecret>> {
        let (private_key, public_key) = crypto::generate_key_pair();

        let data = ExportSecretsRequest {
            all,
            public_key: crypto::serialize_public_key(public_key),
            environment: env,
        };

        let body = serde_json::to_value(data).expect("Failed to serialize data");
        let res = self
            .request_object::<ExportSecretsResponse>(Method::POST, "/api/secrets/export", Some(body), None)
            .await?;

        // Decrypt each secret and map it to an ExportedSecret struct
        let decrypted_secrets: Vec<ExportedSecret> = res.secrets
            .iter()
            .map(|secret| {
                let decrypted_value = crypto::decrypt(private_key.clone(), secret.encrypted_value.clone());
                ExportedSecret {
                    name: secret.name.clone(),
                    environment: secret.environment.clone(),
                    value: decrypted_value,
                    created_at: secret.created_at.clone(),
                }
            })
            .collect();

        Ok(decrypted_secrets)
    }

    pub async fn upload_code(&self, name: &str, package: Package, progress_cb: Option<ProgressCallback>) -> Result<Code> {
        let path = format!("/api/apps/{}/code", name);
        let progress_cb = progress_cb.unwrap_or(Box::new(|_, _| {}));

        // get al the metadata about the file as well as a handle to the underlying data
        let file = File::open(package.package_file_path.unwrap()).await?;
        let metadata = file.metadata().await?;
        let file_size = metadata.len();

        // wrap everything in a stream so that we can stream it to the server accordingly
        let reader_stream = ReaderStream::new(file);
        let progress_stream = ProgressStream::new(reader_stream, file_size, progress_cb).await?;

        // headers that tell the server how to decode this type of file (where relevant)
        let headers = HashMap::from([
            ("Content-Type".to_string(), "application/tar".to_string()),
            //("Content-Encoding".to_string(), "gzip".to_string()),
        ]);

        let res = self
            .request_stream::<_, UploadCodeResponse>(Method::POST, &path, progress_stream, Some(headers))
            .await?;

        Ok(res.code)
    }

    pub async fn run_app(&self, name: &str, env: &str, parameters: HashMap<String, String>) -> Result<Run> {
        let data = AppRunRequest {
            parameters,
            environment: String::from(env),
        };

        let body = serde_json::to_value(data).unwrap();
        let path = format!("/api/apps/{}/runs", name);
        let res = self.request_object::<AppRunResponse>(Method::POST, &path, Some(body), None).await?;
        Ok(res.run)
    }

    pub async fn get_run_logs(&self, name: &str, num: &str) -> Result<Vec<LogLine>> {
        let path = format!("/api/apps/{}/runs/{}/logs", name, num);
        let empty_body = Body::from(Vec::new());
        let res = self.do_request(Method::GET, &path, empty_body, None).await?;
        let body = res.text().await.unwrap();
        Ok(LogLine::from_str(&body))
    }

    async fn request_stream<R, T>(
        &self,
        method: Method,
        path: &str,
        body: R,
        headers: Option<HashMap<String, String>>
    ) -> Result<T>
    where
        R: Stream<Item = StreamResult<bytes::Bytes>> + Send + Sync + 'static,
        T: for<'de> Deserialize<'de>,
    {
        let body = Body::wrap_stream(body);

        self.request(method, path, body, headers).await
    }

    async fn request_object<T>(
        &self,
        method: Method,
        path: &str,
        body: Option<Value>,
        headers: Option<HashMap<String, String>>
    ) -> Result<T>
    where
        T: for<'de> Deserialize<'de>,
    {
        let body = if let Some(obj) = body {
            Body::from(serde_json::to_vec(&obj)?)
        } else {
            // empty body
            Body::from(Vec::new())
        };

        self.request(method, path, body, headers).await
    }

    async fn request<T>(
        &self,
        method: Method,
        path: &str,
        body: Body,
        headers: Option<HashMap<String, String>>,
    ) -> Result<T>
    where
        T: for<'de> Deserialize<'de>,
    {
        let res =  self.do_request(method, path, body, headers).await?;
        res.json::<T>().await.map_err(Into::into)
    }

    async fn do_request(
        &self,
        method: Method,
        path: &str,
        body: Body,
        headers: Option<HashMap<String, String>>,
    ) -> Result<reqwest::Response>
    {
        let client = ReqwestClient::new();
        let url = self.url_from_path(path);
        let mut req = client.request(method, url).body(body);

        if let Some(headers) = headers {
            for (key, value) in headers {
                req = req.header(key, value);
            }
        }

        if let Some(sess) = &self.session {
            req = req.header("Authorization", format!("Bearer {}", sess.token.jwt));
        }

        let res = req.send().await?;

        match res.status() {
            StatusCode::OK | StatusCode::CREATED => Ok(res),
            _ => Err(res.json::<TowerError>().await?),
        }
    }


    fn url_from_path(&self, path: &str) -> Url {
        self.tower_url.join(path).unwrap()
    }
}
