use anyhow::Result;
use clap::Command;
use crate::{Config, api, deploy, run};
use rmcp::{
    ErrorData as McpError, ServerHandler, ServiceExt,
    handler::server::{tool::{Parameters, ToolRouter}},
    model::*,
    schemars::{self, JsonSchema},
    tool, tool_handler, tool_router,
    transport::stdio,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::future::Future;
use futures_util::FutureExt;
use crypto;
use rsa::pkcs1::DecodeRsaPublicKey;

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
    #[serde(default)]
    environment: Option<String>,
    #[serde(default)]
    all: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct CreateSecretRequest {
    name: String,
    value: String,
    #[serde(default)]
    environment: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct DeleteSecretRequest {
    name: String,
    environment: String,
}

pub fn mcp_cmd() -> Command {
    Command::new("mcp-server")
        .about("Runs a local MCP server for LLM interaction")
}

pub async fn do_mcp_server(config: Config, _args: &clap::ArgMatches) -> Result<()> {
    let service = TowerService::new(config);
    let server = service.serve(stdio()).await?;
    server.waiting().await?;
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
            config,
            tool_router: Self::tool_router(),
        }
    }

    fn json_success<T: serde::Serialize>(data: T) -> Result<CallToolResult, McpError> {
        let text = serde_json::to_string_pretty(&data)
            .map_err(|e| McpError::internal_error("Serialization failed", Some(json!({"error": e.to_string()}))))?;
        Ok(CallToolResult::success(vec![Content::text(text)]))
    }

    fn text_success(message: String) -> Result<CallToolResult, McpError> {
        Ok(CallToolResult::success(vec![Content::text(message)]))
    }

    fn error_result(prefix: &str, error: impl std::fmt::Display) -> Result<CallToolResult, McpError> {
        Ok(CallToolResult::error(vec![Content::text(format!("{}: {}", prefix, error))]))
    }

    async fn run_with_panic_handling<F, Fut>(operation: F, success_msg: &str, error_msg: &str) -> Result<CallToolResult, McpError>
    where
        F: FnOnce() -> Fut + Send + 'static,
        Fut: std::future::Future<Output = Result<(), anyhow::Error>> + Send + 'static,
    {
        match std::panic::AssertUnwindSafe(operation()).catch_unwind().await {
            Ok(_) => Ok(CallToolResult::success(vec![Content::text(success_msg.to_string())])),
            Err(_) => Ok(CallToolResult::error(vec![Content::text(error_msg.to_string())])),
        }
    }

    #[tool(description = "List all Tower apps in your account")]
    async fn tower_apps_list(&self) -> Result<CallToolResult, McpError> {
        match api::list_apps(&self.config).await {
            Ok(response) => {
                let apps: Vec<Value> = response.apps.into_iter()
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
            },
            Err(e) => Self::error_result("Failed to list apps", e),
        }
    }

    #[tool(description = "Create a new Tower app")]
    async fn tower_apps_create(&self, Parameters(request): Parameters<NameRequest>) -> Result<CallToolResult, McpError> {
        match api::create_app(&self.config, &request.name, "").await {
            Ok(response) => Self::text_success(format!("Created app '{}'", response.app.name)),
            Err(e) => Self::error_result("Failed to create app", e)
        }
    }

    #[tool(description = "Show details for a Tower app and its recent runs")]
    async fn tower_apps_show(&self, Parameters(request): Parameters<NameRequest>) -> Result<CallToolResult, McpError> {
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
            },
            Err(e) => Self::error_result("Failed to show app", e),
        }
    }

    #[tool(description = "Get logs for a specific Tower app run")]
    async fn tower_apps_logs(&self, Parameters(request): Parameters<AppLogsRequest>) -> Result<CallToolResult, McpError> {
        let seq: i64 = request.seq.parse()
            .map_err(|_| McpError::invalid_params("seq must be a number", None))?;

        match api::describe_run_logs(&self.config, &request.name, seq).await {
            Ok(response) => {
                let logs = response.log_lines.into_iter()
                    .map(|log| format!("{}: {}", log.timestamp, log.message))
                    .collect::<Vec<_>>()
                    .join("\n");
                
                let msg = format!("Logs for app '{}' run {}:\n\n{}", request.name, seq, logs);
                Self::text_success(msg)
            },
            Err(e) => Self::error_result("Failed to get logs", e),
        }
    }

    #[tool(description = "Delete a Tower app")]
    async fn tower_apps_delete(&self, Parameters(request): Parameters<NameRequest>) -> Result<CallToolResult, McpError> {
        match api::delete_app(&self.config, &request.name).await {
            Ok(_) => Self::text_success(format!("Deleted app '{}'", request.name)),
            Err(e) => Self::error_result("Failed to delete app", e)
        }
    }

    #[tool(description = "List secrets in your Tower account (shows only previews for security)")]
    async fn tower_secrets_list(&self, Parameters(request): Parameters<ListSecretsRequest>) -> Result<CallToolResult, McpError> {
        let environment = request.environment.as_deref().unwrap_or("default");
        let all = request.all.as_deref() == Some("true");
        
        match api::list_secrets(&self.config, environment, all).await {
            Ok(response) => Self::json_success(json!({"secrets": response.secrets})),
            Err(e) => Self::error_result("Failed to list secrets", e),
        }
    }

    #[tool(description = "Create a new secret in Tower")]
    async fn tower_secrets_create(&self, Parameters(request): Parameters<CreateSecretRequest>) -> Result<CallToolResult, McpError> {
        let environment = request.environment.as_deref().unwrap_or("default");

        let key_response = api::describe_secrets_key(&self.config).await
            .map_err(|e| McpError::internal_error("Failed to get key", Some(json!({"error": e.to_string()}))))?;
        
        let public_key = rsa::RsaPublicKey::from_pkcs1_pem(&key_response.public_key)
            .map_err(|e| McpError::internal_error("Invalid public key", Some(json!({"error": e.to_string()}))))?;

        let encrypted_value = crypto::encrypt(public_key, request.value.clone())
            .map_err(|e| McpError::internal_error("Encryption failed", Some(json!({"error": e.to_string()}))))?;
        
        let preview = if request.value.len() <= 10 { "XXXXXXXXXX".to_string() } 
                     else { format!("XXXXXX{}", &request.value[request.value.len()-4..]) };

        match api::create_secret(&self.config, &request.name, environment, &encrypted_value, &preview).await {
            Ok(_) => Self::text_success(format!("Created secret '{}' in environment '{}'", request.name, environment)),
            Err(e) => Self::error_result("Failed to create secret", e),
        }
    }

    #[tool(description = "Delete a secret from Tower")]
    async fn tower_secrets_delete(&self, Parameters(request): Parameters<DeleteSecretRequest>) -> Result<CallToolResult, McpError> {
        match api::delete_secret(&self.config, &request.name, &request.environment).await {
            Ok(_) => Self::text_success(format!("Deleted secret '{}' from environment '{}'", request.name, request.environment)),
            Err(e) => Self::error_result("Failed to delete secret", e),
        }
    }

    #[tool(description = "List teams you belong to")]
    async fn tower_teams_list(&self) -> Result<CallToolResult, McpError> {
        let response = api::refresh_session(&self.config).await
            .map_err(|e| McpError::internal_error("Failed to refresh session", Some(json!({"error": e.to_string()}))))?;
        
        let mut session = self.config.get_current_session()
            .map_err(|e| McpError::internal_error("No valid session", Some(json!({"error": e.to_string()}))))?;
        
        session.update_from_api_response(&response)
            .map_err(|e| McpError::internal_error("Failed to update session", Some(json!({"error": e.to_string()}))))?;

        let active_team_name = session.active_team.as_ref().map(|t| &t.name);
        let teams: Vec<Value> = session.teams.into_iter()
            .map(|team| json!({"name": team.name, "active": Some(&team.name) == active_team_name}))
            .collect();
        
        Self::json_success(json!({"teams": teams}))
    }

    #[tool(description = "Switch context to a different team")]
    async fn tower_teams_switch(&self, Parameters(request): Parameters<NameRequest>) -> Result<CallToolResult, McpError> {
        match self.config.set_active_team_by_name(&request.name) {
            Ok(_) => Self::text_success(format!("Switched to team: {}", request.name)),
            Err(e) => Self::error_result("Failed to switch team", e)
        }
    }

    #[tool(description = "Deploy your app to Tower cloud")]
    async fn tower_deploy(&self) -> Result<CallToolResult, McpError> {
        let config = self.config.clone();
        Self::run_with_panic_handling(
            move || async move {
                let matches = clap::ArgMatches::default();
                deploy::do_deploy(config, &matches).await;
                Ok(())
            },
            "App deployed",
            "Deploy failed - check Towerfile and login status"
        ).await
    }

    #[tool(description = "Run your app locally")]
    async fn tower_run(&self) -> Result<CallToolResult, McpError> {
        let config = self.config.clone();
        let matches = clap::ArgMatches::default();
        match run::do_run_inner(config, &matches, None).await {
            Ok(_) => Self::text_success("App ran locally".to_string()),
            Err(e) => Self::error_result("Local run failed", e),
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

#[cfg(test)]
mod tests;
