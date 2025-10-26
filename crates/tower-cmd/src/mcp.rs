use std::future::Future;

use axum::Router;
use clap::Command;
use config::{Session, Towerfile};
use crypto;
use rmcp::{
    handler::server::tool::{Parameters, ToolRouter},
    model::{
        CallToolResult, Content, Implementation, LoggingLevel, LoggingMessageNotificationParam,
        ProtocolVersion, ServerCapabilities, ServerInfo,
    },
    schemars::{self, JsonSchema},
    service::RequestContext,
    tool, tool_handler, tool_router,
    transport::{
        sse_server::SseServer,
        stdio,
        streamable_http_server::{
            session::local::LocalSessionManager, StreamableHttpServerConfig, StreamableHttpService,
        },
    },
    ErrorData as McpError, RoleServer, ServerHandler, ServiceExt,
};
use rsa::pkcs1::DecodeRsaPublicKey;
use serde::Deserialize;
use serde_json::{json, Value};
use tokio::net::TcpListener;
use tower_api::apis::Error as ApiError;

use crate::{api, deploy, run, towerfile_gen::TowerfileGenerator, Config, Error};

struct StreamingOutput {
    sender: tokio::sync::mpsc::UnboundedSender<String>,
    collected: std::sync::Arc<std::sync::Mutex<Vec<String>>>,
    task: tokio::task::JoinHandle<()>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct CommonParams {
    /// Optional working directory path. If not specified, uses the current directory.
    working_directory: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct NameRequest {
    name: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct AppLogsRequest {
    name: String,
    seq: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct ListSecretsRequest {
    environment: Option<String>,
    all: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct CreateSecretRequest {
    name: String,
    value: String,
    environment: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct DeleteSecretRequest {
    name: String,
    environment: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct UpdateTowerfileRequest {
    #[serde(flatten)]
    common: CommonParams,
    app_name: Option<String>,
    script: Option<String>,
    description: Option<String>,
    source: Option<Vec<String>>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct AddParameterRequest {
    #[serde(flatten)]
    common: CommonParams,
    name: String,
    description: String,
    default: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct GenerateTowerfileRequest {
    #[serde(flatten)]
    common: CommonParams,
    script_path: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct ScheduleRequest {
    app_name: String,
    environment: Option<String>,
    cron: String,
    parameters: Option<std::collections::HashMap<String, String>>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct UpdateScheduleRequest {
    schedule_id: String,
    cron: Option<String>,
    parameters: Option<std::collections::HashMap<String, String>>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct EmptyRequest {
    #[serde(flatten)]
    common: CommonParams,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct RunRequest {
    #[serde(flatten)]
    common: CommonParams,
    parameters: Option<std::collections::HashMap<String, String>>,
}

pub fn mcp_cmd() -> Command {
    Command::new("mcp-server")
        .about("Runs an MCP server for LLM interaction")
        .arg(
            clap::Arg::new("transport")
                .long("transport")
                .short('t')
                .help("Transport mode")
                .value_parser(["stdio", "sse", "http"])
                .default_value("stdio"),
        )
        .arg(
            clap::Arg::new("port")
                .long("port")
                .short('p')
                .help("Port for HTTP/SSE server (default: 34567)")
                .default_value("34567")
                .value_parser(clap::value_parser!(u16)),
        )
}

pub async fn do_mcp_server(config: Config, args: &clap::ArgMatches) -> Result<(), Error> {
    let transport = args.get_one::<String>("transport").unwrap();
    let port = *args.get_one::<u16>("port").unwrap();

    match transport.as_str() {
        "stdio" => run_stdio_server(config).await,
        "sse" => run_sse_server(config, port).await,
        "http" => run_http_server(config, port).await,
        _ => Err(Error::from(std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            format!("Unknown transport: {}", transport),
        ))),
    }
}

async fn run_stdio_server(config: Config) -> Result<(), Error> {
    // Set stdio MCP mode to prevent any non-JSON-RPC output from corrupting the protocol
    crate::output::set_output_mode(crate::output::OutputMode::McpStdio);

    let (stdin, stdout) = stdio();
    let service = TowerService::new(config);
    let server = service.serve((stdin, stdout)).await.map_err(|e| {
        Error::from(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("Failed to start stdio server: {}", e),
        ))
    })?;
    let _ = server.waiting().await;
    Ok(())
}

async fn run_sse_server(config: Config, port: u16) -> Result<(), Error> {
    let bind_addr = format!("127.0.0.1:{}", port);
    crate::output::write(&format!("SSE MCP server running on http://{}\n", bind_addr));

    // Set streaming MCP mode to enable logging notifications
    crate::output::set_output_mode(crate::output::OutputMode::McpStreaming);

    let ct = SseServer::serve(bind_addr.parse()?)
        .await?
        .with_service_directly(move || TowerService::new(config.clone()));

    tokio::signal::ctrl_c().await?;
    ct.cancel();
    Ok(())
}

async fn run_http_server(config: Config, port: u16) -> Result<(), Error> {
    let bind_addr = format!("127.0.0.1:{}", port);
    crate::output::write(&format!(
        "Streamable HTTP MCP server running on http://{}\n",
        bind_addr
    ));

    // Set streaming MCP mode to enable logging notifications
    crate::output::set_output_mode(crate::output::OutputMode::McpStreaming);

    let service = StreamableHttpService::new(
        move || Ok(TowerService::new(config.clone())),
        LocalSessionManager::default().into(),
        StreamableHttpServerConfig::default(),
    );

    let router = Router::new().nest_service("/mcp", service);
    let listener = TcpListener::bind(&bind_addr).await?;
    axum::serve(listener, router)
        .with_graceful_shutdown(async {
            tokio::signal::ctrl_c().await.unwrap();
        })
        .await?;
    Ok(())
}

#[derive(Clone)]
pub struct TowerService {
    config: Config,
    tool_router: ToolRouter<Self>,
}

#[tool_router]
impl TowerService {
    pub fn new(config: Config) -> Self {
        Self {
            config: std::env::var("TOWER_JWT")
                .ok()
                .and_then(|token| Session::from_jwt(&token).ok())
                .map(|session| config.clone().with_session(session))
                .unwrap_or(config),
            tool_router: Self::tool_router(),
        }
    }

    fn json_success<T: serde::Serialize>(data: T) -> Result<CallToolResult, McpError> {
        let text = serde_json::to_string_pretty(&data).map_err(|e| {
            McpError::internal_error(
                "Serialization failed",
                Some(json!({"error": e.to_string()})),
            )
        })?;
        Ok(CallToolResult::success(vec![Content::text(text)]))
    }

    fn text_success(message: String) -> Result<CallToolResult, McpError> {
        Ok(CallToolResult::success(vec![Content::text(message)]))
    }

    fn error_result(
        prefix: &str,
        error: impl std::fmt::Display + std::fmt::Debug,
    ) -> Result<CallToolResult, McpError> {
        Ok(CallToolResult::error(vec![Content::text(format!(
            "{}: {:#?}",
            prefix, error
        ))]))
    }

    fn resolve_working_directory(common: &CommonParams) -> std::path::PathBuf {
        common
            .working_directory
            .as_ref()
            .map(std::path::PathBuf::from)
            .unwrap_or_else(|| {
                std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."))
            })
    }

    fn extract_api_error_message(error: &crate::Error) -> String {
        let crate::Error::ApiRunError { source } = error else {
            return error.to_string();
        };

        let ApiError::ResponseError(resp) = source else {
            return source.to_string();
        };

        Self::parse_error_response(resp)
            .or_else(|| Self::status_code_message(resp))
            .unwrap_or_else(|| format!("API error ({}): {}", resp.status, resp.content))
    }

    fn parse_error_response<T>(resp: &tower_api::apis::ResponseContent<T>) -> Option<String> {
        let error_model: tower_api::models::ErrorModel =
            serde_json::from_str(&resp.content).ok()?;

        error_model
            .detail
            .or_else(|| error_model.errors?.first()?.message.clone())
    }

    fn status_code_message<T>(resp: &tower_api::apis::ResponseContent<T>) -> Option<String> {
        match resp.status.as_u16() {
            404 => Some("App not found or not deployed".to_string()),
            422 => Some(format!("Validation error: {}", resp.content)),
            _ => None,
        }
    }

    fn is_deployment_error(message: &str) -> bool {
        message.contains("404")
            || message.contains("not found")
            || message.contains("not deployed")
            || (message.contains("API error occurred") && !message.contains("422"))
    }

    fn setup_output_capture(
        ctx: &RequestContext<RoleServer>,
        send_notifications: bool,
    ) -> StreamingOutput {
        let (tx, mut rx) = tokio::sync::mpsc::unbounded_channel::<String>();
        let collected = std::sync::Arc::new(std::sync::Mutex::new(Vec::new()));
        let collected_clone = collected.clone();

        let task = if send_notifications {
            let peer = ctx.peer.clone();
            tokio::spawn(async move {
                while let Some(message) = rx.recv().await {
                    if let Ok(mut output) = collected_clone.lock() {
                        output.push(message.clone());
                    }
                    let _ = peer.notify_logging_message(LoggingMessageNotificationParam {
                        level: LoggingLevel::Info,
                        data: serde_json::json!({"message": message, "timestamp": chrono::Utc::now().to_rfc3339()}),
                        logger: Some("tower-process".to_string()),
                    }).await;
                }
            })
        } else {
            tokio::spawn(async move {
                while let Some(message) = rx.recv().await {
                    if let Ok(mut output) = collected_clone.lock() {
                        output.push(message);
                    }
                }
            })
        };

        StreamingOutput {
            sender: tx,
            collected,
            task,
        }
    }

    async fn execute_with_streaming<F, Fut, T>(
        ctx: &RequestContext<RoleServer>,
        operation: F,
    ) -> (Result<T, crate::Error>, String)
    where
        F: FnOnce() -> Fut,
        Fut: std::future::Future<Output = Result<T, crate::Error>>,
    {
        // Check if we're in streaming mode (SSE/HTTP) where we send notifications
        // vs stdio mode where we don't
        let mode = crate::output::get_output_mode();
        let send_notifications = mode == crate::output::OutputMode::McpStreaming;
        let streaming = Self::setup_output_capture(ctx, send_notifications);

        crate::output::set_current_sender(streaming.sender.clone());

        let result = operation().await;

        crate::output::clear_current_sender();
        drop(streaming.sender);
        streaming.task.await.ok();

        let output = streaming
            .collected
            .lock()
            .ok()
            .map(|output| output.join("\n"))
            .unwrap_or_default();

        (result, output)
    }

    #[tool(description = "List all Tower apps in your account")]
    async fn tower_apps_list(&self) -> Result<CallToolResult, McpError> {
        match api::list_apps(&self.config).await {
            Ok(response) => {
                let apps: Vec<Value> = response
                    .apps
                    .into_iter()
                    .map(|app_summary| {
                        let app = app_summary.app;
                        json!({
                            "name": app.name,
                            "description": app.short_description,
                            "created_at": app.created_at,
                            "status": format!("{:?}", app.status)
                        })
                    })
                    .collect();
                Self::json_success(json!({"apps": apps}))
            }
            Err(e) => Self::error_result("Failed to list apps", e),
        }
    }

    #[tool(description = "Create a new Tower app")]
    async fn tower_apps_create(
        &self,
        Parameters(request): Parameters<NameRequest>,
    ) -> Result<CallToolResult, McpError> {
        match api::create_app(&self.config, &request.name, "").await {
            Ok(response) => Self::text_success(format!("Created app '{}'", response.app.name)),
            Err(e) => Self::error_result("Failed to create app", e),
        }
    }

    #[tool(description = "Show details for a Tower app and its recent runs")]
    async fn tower_apps_show(
        &self,
        Parameters(request): Parameters<NameRequest>,
    ) -> Result<CallToolResult, McpError> {
        match api::describe_app(&self.config, &request.name).await {
            Ok(response) => {
                let data = json!({
                    "app": {
                        "name": response.app.name,
                        "description": response.app.short_description,
                        "created_at": response.app.created_at,
                        "status": format!("{:?}", response.app.status)
                    },
                    "recent_runs": response.runs.iter().map(|run| json!({
                        "number": run.number,
                        "status": format!("{:?}", run.status),
                        "scheduled_at": run.scheduled_at,
                        "started_at": run.started_at,
                        "ended_at": run.ended_at
                    })).collect::<Vec<_>>()
                });
                Self::json_success(data)
            }
            Err(e) => Self::error_result("Failed to show app", e),
        }
    }

    #[tool(description = "Get logs for a specific Tower app run")]
    async fn tower_apps_logs(
        &self,
        Parameters(request): Parameters<AppLogsRequest>,
    ) -> Result<CallToolResult, McpError> {
        let seq: i64 = request
            .seq
            .parse()
            .map_err(|_| McpError::invalid_params("seq must be a number", None))?;

        match api::describe_run_logs(&self.config, &request.name, seq).await {
            Ok(response) => {
                let logs = response
                    .log_lines
                    .into_iter()
                    .map(|log| format!("{}: {}", log.reported_at, log.content))
                    .collect::<Vec<_>>()
                    .join("\n");

                let msg = format!("Logs for app '{}' run {}:\n\n{}", request.name, seq, logs);
                Self::text_success(msg)
            }
            Err(e) => Self::error_result("Failed to get logs", e),
        }
    }

    #[tool(description = "Delete a Tower app")]
    async fn tower_apps_delete(
        &self,
        Parameters(request): Parameters<NameRequest>,
    ) -> Result<CallToolResult, McpError> {
        match api::delete_app(&self.config, &request.name).await {
            Ok(_) => Self::text_success(format!("Deleted app '{}'", request.name)),
            Err(e) => Self::error_result("Failed to delete app", e),
        }
    }

    #[tool(description = "List secrets in your Tower account (shows only previews for security)")]
    async fn tower_secrets_list(
        &self,
        Parameters(request): Parameters<ListSecretsRequest>,
    ) -> Result<CallToolResult, McpError> {
        let environment = request.environment.as_deref().unwrap_or("default");
        let all = request.all.as_deref() == Some("true");

        match api::list_secrets(&self.config, environment, all).await {
            Ok(response) => Self::json_success(json!({"secrets": response.secrets})),
            Err(e) => Self::error_result("Failed to list secrets", e),
        }
    }

    #[tool(description = "Create a new secret in Tower")]
    async fn tower_secrets_create(
        &self,
        Parameters(request): Parameters<CreateSecretRequest>,
    ) -> Result<CallToolResult, McpError> {
        let environment = request.environment.as_deref().unwrap_or("default");

        let key_response = api::describe_secrets_key(&self.config).await.map_err(|e| {
            McpError::internal_error("Failed to get key", Some(json!({"error": e.to_string()})))
        })?;

        let public_key =
            rsa::RsaPublicKey::from_pkcs1_pem(&key_response.public_key).map_err(|e| {
                McpError::internal_error(
                    "Invalid public key",
                    Some(json!({"error": e.to_string()})),
                )
            })?;

        let encrypted_value = crypto::encrypt(public_key, request.value.clone()).map_err(|e| {
            McpError::internal_error("Encryption failed", Some(json!({"error": e.to_string()})))
        })?;

        let preview = if request.value.len() <= 10 {
            "XXXXXXXXXX".to_string()
        } else {
            format!("XXXXXX{}", &request.value[request.value.len() - 4..])
        };

        match api::create_secret(
            &self.config,
            &request.name,
            environment,
            &encrypted_value,
            &preview,
        )
        .await
        {
            Ok(_) => Self::text_success(format!(
                "Created secret '{}' in environment '{}'",
                request.name, environment
            )),
            Err(e) => Self::error_result("Failed to create secret", e),
        }
    }

    #[tool(description = "Delete a secret from Tower")]
    async fn tower_secrets_delete(
        &self,
        Parameters(request): Parameters<DeleteSecretRequest>,
    ) -> Result<CallToolResult, McpError> {
        match api::delete_secret(&self.config, &request.name, &request.environment).await {
            Ok(_) => Self::text_success(format!(
                "Deleted secret '{}' from environment '{}'",
                request.name, request.environment
            )),
            Err(e) => Self::error_result("Failed to delete secret", e),
        }
    }

    #[tool(description = "List teams you belong to")]
    async fn tower_teams_list(&self) -> Result<CallToolResult, McpError> {
        let response = api::refresh_session(&self.config).await.map_err(|e| {
            McpError::internal_error(
                "Failed to refresh session",
                Some(json!({"error": e.to_string()})),
            )
        })?;

        let mut session = self.config.get_current_session().map_err(|e| {
            McpError::internal_error("No valid session", Some(json!({"error": e.to_string()})))
        })?;

        session.update_from_api_response(&response).map_err(|e| {
            McpError::internal_error(
                "Failed to update session",
                Some(json!({"error": e.to_string()})),
            )
        })?;

        let active_team_name = session.active_team.as_ref().map(|t| &t.name);
        let teams: Vec<Value> = session
            .teams
            .into_iter()
            .map(|team| json!({"name": team.name, "active": Some(&team.name) == active_team_name}))
            .collect();

        Self::json_success(json!({"teams": teams}))
    }

    #[tool(description = "Switch context to a different team")]
    async fn tower_teams_switch(
        &self,
        Parameters(request): Parameters<NameRequest>,
    ) -> Result<CallToolResult, McpError> {
        match self.config.set_active_team_by_name(&request.name) {
            Ok(_) => Self::text_success(format!("Switched to team: {}", request.name)),
            Err(e) => Self::error_result("Failed to switch team", e),
        }
    }

    #[tool(
        description = "Deploy your app to Tower cloud. Prerequisites: 1) Create Towerfile, 2) Create app with tower_apps_create. Optional working_directory parameter specifies which project directory to deploy from."
    )]
    async fn tower_deploy(
        &self,
        Parameters(request): Parameters<EmptyRequest>,
    ) -> Result<CallToolResult, McpError> {
        let working_dir = Self::resolve_working_directory(&request.common);

        match deploy::deploy_from_dir(self.config.clone(), working_dir, true).await {
            Ok(_) => Self::text_success("Deploy completed successfully".to_string()),
            Err(e) => Self::error_result("Deploy failed", e),
        }
    }

    #[tool(
        description = "Run your app locally using the local Towerfile and source files. Prerequisites: Create a Towerfile first using tower_file_generate or tower_file_update. Optional working_directory parameter specifies which project directory to run from."
    )]
    async fn tower_run_local(
        &self,
        Parameters(request): Parameters<EmptyRequest>,
        ctx: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        let working_dir = Self::resolve_working_directory(&request.common);
        let config = self.config.clone();

        let (result, output) = Self::execute_with_streaming(&ctx, || {
            run::do_run_local(
                config,
                working_dir,
                "default",
                std::collections::HashMap::new(),
            )
        })
        .await;
        match result {
            Ok(_) => {
                if output.trim().is_empty() {
                    Self::text_success("App completed successfully".to_string())
                } else {
                    Self::text_success(format!("App completed successfully\n\n{}", output))
                }
            }
            Err(e) => {
                let error_text = if output.trim().is_empty() {
                    e.to_string()
                } else {
                    output
                };
                Self::error_result("Local run failed", error_text)
            }
        }
    }

    #[tool(
        description = "Run your app remotely on Tower cloud. Prerequisites: 1) Create Towerfile, 2) Create app with tower_apps_create, 3) Deploy with tower_deploy"
    )]
    async fn tower_run_remote(
        &self,
        Parameters(request): Parameters<RunRequest>,
        ctx: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        use config::Towerfile;

        let config = self.config.clone();
        let working_dir = Self::resolve_working_directory(&request.common);
        let path = working_dir;
        let env = "default";
        let params = request.parameters.unwrap_or_default();

        // Load Towerfile to get app name
        let towerfile = match Towerfile::from_dir_str(path.to_str().unwrap()) {
            Ok(tf) => tf,
            Err(e) => return Self::error_result("Failed to read Towerfile", e),
        };

        let app_name = towerfile.app.name.clone();

        let (result, output) = Self::execute_with_streaming(&ctx, || {
            run::do_run_remote(config, path, env, params, None, true)
        })
        .await;
        match result {
            Ok(_) => {
                if output.trim().is_empty() {
                    Self::text_success("Remote run completed successfully".to_string())
                } else {
                    Self::text_success(format!("Remote run completed successfully\n\n{}", output))
                }
            }
            Err(e) => {
                let error_text = if output.trim().is_empty() {
                    let api_error = Self::extract_api_error_message(&e);
                    if Self::is_deployment_error(&api_error) {
                        format!(
                            "App '{}' not deployed. Try running tower_deploy first.",
                            app_name
                        )
                    } else {
                        api_error
                    }
                } else {
                    output
                };
                Self::error_result("Remote run failed", error_text)
            }
        }
    }

    #[tool(
        description = "Read and parse the current Towerfile configuration. Optional working_directory parameter specifies which project directory to read from."
    )]
    async fn tower_file_read(
        &self,
        Parameters(request): Parameters<EmptyRequest>,
    ) -> Result<CallToolResult, McpError> {
        let working_dir = Self::resolve_working_directory(&request.common);
        match Towerfile::from_dir_str(working_dir.to_str().unwrap()) {
            Ok(towerfile) => Self::json_success(serde_json::to_value(&towerfile).unwrap()),
            Err(e) => Self::error_result("Failed to read Towerfile", e),
        }
    }

    #[tool(
        description = "Update Towerfile app configuration. Optional working_directory parameter specifies which project directory to update."
    )]
    async fn tower_file_update(
        &self,
        Parameters(request): Parameters<UpdateTowerfileRequest>,
    ) -> Result<CallToolResult, McpError> {
        let working_dir = Self::resolve_working_directory(&request.common);
        let mut towerfile = match Towerfile::from_dir_str(working_dir.to_str().unwrap()) {
            Ok(tf) => tf,
            Err(e) => return Self::error_result("Failed to read Towerfile", e),
        };

        if let Some(name) = request.app_name {
            towerfile.app.name = name;
        }
        if let Some(script) = request.script {
            towerfile.app.script = script;
        }
        if let Some(description) = request.description {
            towerfile.app.description = description;
        }
        if let Some(source) = request.source {
            towerfile.app.source = source;
        }

        let towerfile_path = working_dir.join("Towerfile");
        match towerfile.save(Some(&towerfile_path)) {
            Ok(_) => {
                Self::text_success(format!("Towerfile updated at {}", towerfile_path.display()))
            }
            Err(e) => Self::error_result("Failed to save Towerfile", e),
        }
    }

    #[tool(
        description = "Add a new parameter to the Towerfile. Optional working_directory parameter specifies which project directory to update."
    )]
    async fn tower_file_add_parameter(
        &self,
        Parameters(request): Parameters<AddParameterRequest>,
    ) -> Result<CallToolResult, McpError> {
        let working_dir = Self::resolve_working_directory(&request.common);
        let mut towerfile = match Towerfile::from_dir_str(working_dir.to_str().unwrap()) {
            Ok(tf) => tf,
            Err(e) => return Self::error_result("Failed to read Towerfile", e),
        };

        let param_name = request.name.clone();
        towerfile.add_parameter(request.name, request.description, request.default);

        let towerfile_path = working_dir.join("Towerfile");
        match towerfile.save(Some(&towerfile_path)) {
            Ok(_) => Self::text_success(format!(
                "Added parameter '{}' to {}",
                param_name,
                towerfile_path.display()
            )),
            Err(e) => Self::error_result("Failed to save Towerfile", e),
        }
    }

    #[tool(
        description = "Validate the current Towerfile configuration. Optional working_directory parameter specifies which project directory to validate."
    )]
    async fn tower_file_validate(
        &self,
        Parameters(request): Parameters<EmptyRequest>,
    ) -> Result<CallToolResult, McpError> {
        let working_dir = Self::resolve_working_directory(&request.common);
        match Towerfile::from_dir_str(working_dir.to_str().unwrap()) {
            Ok(_) => Self::json_success(json!({"valid": true})),
            Err(e) => Self::json_success(json!({"valid": false, "error": e.to_string()})),
        }
    }

    #[tool(
        description = "Generate Towerfile from pyproject.toml. This is typically the first step in the workflow. Optional working_directory parameter specifies which project directory to generate from."
    )]
    async fn tower_file_generate(
        &self,
        Parameters(request): Parameters<GenerateTowerfileRequest>,
    ) -> Result<CallToolResult, McpError> {
        let working_dir = Self::resolve_working_directory(&request.common);
        let pyproject_path = working_dir.join("pyproject.toml");
        let content = match TowerfileGenerator::from_pyproject(
            Some(pyproject_path.to_str().unwrap()),
            request.script_path.as_deref(),
        ) {
            Ok(content) => content,
            Err(e) => return Self::error_result("Failed to generate Towerfile", e),
        };

        let towerfile_path = working_dir.join("Towerfile");
        match std::fs::write(&towerfile_path, &content) {
            Ok(_) => {
                let success_msg = format!(
                    "Generated Towerfile at {}\n\n{}",
                    towerfile_path.display(),
                    content
                );
                Self::text_success(success_msg)
            }
            Err(e) => Self::error_result("Failed to write Towerfile", e),
        }
    }

    #[tool(
        description = "Show the recommended workflow for developing and deploying Tower applications"
    )]
    async fn tower_workflow_help(&self) -> Result<CallToolResult, McpError> {
        let workflow = r#"Tower Application Development Workflow:

All commands support an optional 'working_directory' parameter to specify which project directory to operate on.

0. HAVE AN EXISTING PYTHON PROJECT:
   There are no commands for this provided with this MCP server. However, if you do not have a python project yet
   then a good start would be to make a new directory with the project name, and then call `uv init` to generate
   a pyproject.toml, main.py and README.md

1. CREATE TOWERFILE (required for all steps):
   - tower_file_generate: Generate from existing pyproject.toml
   - tower_file_update: Manually create or update configuration
   - tower_file_validate: Verify Towerfile is valid

2. LOCAL DEVELOPMENT & TESTING:
   - tower_run_local: Run your app locally to test functionality

3. CLOUD DEPLOYMENT (for remote execution):
   - tower_apps_create: Create app on Tower cloud
   - tower_deploy: Deploy your code to the cloud
   - tower_run_remote: Execute on Tower cloud infrastructure

4. SCHEDULE MANAGEMENT (for automatic recurring execution):
   - tower_schedules_list: List all schedules for apps
   - tower_schedules_create: Create a schedule to run an app automatically on a cron schedule
   - tower_schedules_update: Update an existing schedule
   - tower_schedules_delete: Delete a schedule

5. MANAGEMENT & MONITORING:
   - tower_apps_list: View your deployed apps
   - tower_apps_show: Get detailed app information and recent runs
   - tower_apps_logs: View execution logs

6. TEAM & SECRETS (optional):
   - tower_teams_list/switch: Manage team contexts
   - tower_secrets_create/list: Manage application secrets

Quick Start: tower_file_generate → tower_run_local (test locally) → tower_apps_create → tower_deploy → tower_run_remote → tower_schedules_create (for recurring runs)

Example with working_directory: {"working_directory": "/path/to/project", ...}

Consider taking database username/password/url and making them into secrets to be accessed in app code"#;

        Self::text_success(workflow.to_string())
    }

    #[tool(description = "List all schedules for apps")]
    async fn tower_schedules_list(&self) -> Result<CallToolResult, McpError> {
        match api::list_schedules(&self.config, None, None).await {
            Ok(response) => {
                Self::json_success(serde_json::json!({"schedules": response.schedules}))
            }
            Err(e) => Self::error_result("Failed to list schedules", e),
        }
    }

    #[tool(description = "Create a new schedule for an app")]
    async fn tower_schedules_create(
        &self,
        Parameters(request): Parameters<ScheduleRequest>,
    ) -> Result<CallToolResult, McpError> {
        let environment = request.environment.as_deref().unwrap_or("default");

        match api::create_schedule(
            &self.config,
            &request.app_name,
            environment,
            &request.cron,
            request.parameters,
        )
        .await
        {
            Ok(response) => Self::text_success(format!(
                "Created schedule '{}' for app '{}' with cron '{}' in environment '{}'",
                response.schedule.id, request.app_name, request.cron, environment
            )),
            Err(e) => Self::error_result("Failed to create schedule", e),
        }
    }

    #[tool(description = "Update an existing schedule")]
    async fn tower_schedules_update(
        &self,
        Parameters(request): Parameters<UpdateScheduleRequest>,
    ) -> Result<CallToolResult, McpError> {
        match api::update_schedule(
            &self.config,
            &request.schedule_id,
            request.cron.as_ref(),
            request.parameters,
        )
        .await
        {
            Ok(_) => Self::text_success(format!("Updated schedule '{}'.", request.schedule_id)),
            Err(e) => Self::error_result("Failed to update schedule", e),
        }
    }

    #[tool(description = "Delete a schedule")]
    async fn tower_schedules_delete(
        &self,
        Parameters(schedule_id): Parameters<NameRequest>,
    ) -> Result<CallToolResult, McpError> {
        match api::delete_schedule(&self.config, &schedule_id.name).await {
            Ok(_) => Self::text_success(format!("Deleted schedule '{}'.", schedule_id.name)),
            Err(e) => Self::error_result("Failed to delete schedule", e),
        }
    }
}

#[tool_handler]
impl ServerHandler for TowerService {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .build(),
            server_info: Implementation {
                name: "tower-cli".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
            },
            instructions: Some("Tower CLI MCP Server - Manage Tower apps, secrets, teams, and deployments through conversational AI. Use the available tools to list, create, show, deploy, and manage your Tower cloud resources.".to_string()),
        }
    }
}
