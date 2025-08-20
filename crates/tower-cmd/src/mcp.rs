use clap::Command;
use crate::{Config, api, deploy, run};
use rmcp::{ServerHandler, ServiceExt, transport::stdio, model::{CallToolResult, Content, CallToolRequestParam, Tool, ListToolsResult}, ErrorData as McpError, service::RequestContext, service::RoleServer};
use tower_telemetry::tracing;
use anyhow::Result;
use serde_json::{json, Value, Map};
use std::sync::Arc;
use futures::FutureExt;

pub fn mcp_cmd() -> Command {
    Command::new("mcp-server")
        .about("Runs a local MCP server for LLM interaction")
}

pub async fn do_mcp_server(config: Config, _args: &clap::ArgMatches) -> Result<()> {
    tracing::info!("Starting Tower CLI MCP server");

    #[derive(Clone)]
    struct TowerService {
        config: Config,
    }

    impl TowerService {
        fn new(config: Config) -> Self {
            Self { config }
        }

        async fn handle_apps_list(&self) -> Result<CallToolResult, McpError> {
            match api::list_apps(&self.config).await {
                Ok(response) => {
                    let apps: Vec<Value> = response.apps.into_iter().map(|app_summary| {
                        let app = app_summary.app;
                        json!({
                            "name": app.name,
                            "description": app.short_description,
                            "created_at": app.created_at,
                            "status": format!("{:?}", app.status)
                        })
                    }).collect();
                    
                    match serde_json::to_string_pretty(&json!({"apps": apps})) {
                        Ok(text) => Ok(CallToolResult::success(vec![Content::text(text)])),
                        Err(e) => Ok(CallToolResult::error(vec![Content::text(format!("JSON serialization error: {}", e))]))
                    }
                },
                Err(e) => Ok(CallToolResult::error(vec![Content::text(format!("Failed to list apps: {}", e))]))
            }
        }

        async fn handle_apps_create(&self, request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let name = request.arguments.as_ref()
                .and_then(|args| args.get("name"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| McpError::invalid_params("name parameter is required", None))?;

            match api::create_app(&self.config, name, "").await {
                Ok(response) => Ok(CallToolResult::success(vec![Content::text(
                    format!("Successfully created app '{}'", response.app.name)
                )])),
                Err(e) => Ok(CallToolResult::error(vec![Content::text(format!("Failed to create app: {}", e))]))
            }
        }

        async fn handle_apps_show(&self, request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let name = request.arguments.as_ref()
                .and_then(|args| args.get("name"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| McpError::invalid_params("name parameter is required", None))?;

            match api::describe_app(&self.config, name).await {
                Ok(response) => {
                    let app = response.app;
                    let runs = response.runs;
                    
                    let app_json = json!({
                        "app": {
                            "name": app.name,
                            "description": app.short_description,
                            "created_at": app.created_at,
                            "status": format!("{:?}", app.status)
                        },
                        "recent_runs": runs.iter().map(|run| {
                            json!({
                                "number": run.number,
                                "status": format!("{:?}", run.status),
                                "scheduled_at": run.scheduled_at,
                                "started_at": run.started_at,
                                "ended_at": run.ended_at
                            })
                        }).collect::<Vec<_>>()
                    });
                    
                    match serde_json::to_string_pretty(&app_json) {
                        Ok(text) => Ok(CallToolResult::success(vec![Content::text(text)])),
                        Err(e) => Ok(CallToolResult::error(vec![Content::text(format!("JSON serialization error: {}", e))]))
                    }
                },
                Err(e) => Ok(CallToolResult::error(vec![Content::text(format!("Failed to show app: {}", e))]))
            }
        }

        async fn handle_apps_logs(&self, request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let name = request.arguments.as_ref()
                .and_then(|args| args.get("name"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| McpError::invalid_params("name parameter is required", None))?;

            let seq_str = request.arguments.as_ref()
                .and_then(|args| args.get("seq"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| McpError::invalid_params("seq parameter is required", None))?;

            let seq: i64 = seq_str.parse()
                .map_err(|_| McpError::invalid_params("seq must be a valid integer", None))?;

            match api::describe_run_logs(&self.config, name, seq).await {
                Ok(response) => {
                    let logs: Vec<String> = response.log_lines.into_iter()
                        .map(|log| format!("{}: {}", log.timestamp, log.message))
                        .collect();
                    
                    Ok(CallToolResult::success(vec![Content::text(
                        format!("Logs for app '{}' run {}:\n\n{}", name, seq, logs.join("\n"))
                    )]))
                },
                Err(e) => Ok(CallToolResult::error(vec![Content::text(format!("Failed to get logs: {}", e))]))
            }
        }

        async fn handle_deploy(&self, request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let _path = request.arguments.as_ref()
                .and_then(|args| args.get("path"))
                .and_then(|v| v.as_str())
                .unwrap_or(".");

            // Create minimal ArgMatches for deploy command
            let matches = clap::ArgMatches::default();
            
            // Tower CLI deploy functions typically exit on error, so we catch panics
            let result = std::panic::AssertUnwindSafe(deploy::do_deploy(self.config.clone(), &matches)).catch_unwind().await;
            
            match result {
                Ok(_) => Ok(CallToolResult::success(vec![Content::text(
                    "Successfully deployed app".to_string()
                )])),
                Err(_) => Ok(CallToolResult::error(vec![Content::text(
                    "Failed to deploy - check that you have a valid Towerfile and are logged in".to_string()
                )]))
            }
        }

        async fn handle_run(&self, request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let _path = request.arguments.as_ref()
                .and_then(|args| args.get("path"))
                .and_then(|v| v.as_str())
                .unwrap_or(".");

            // Create minimal ArgMatches for run command  
            let matches = clap::ArgMatches::default();
            
            // Tower CLI run functions typically exit on error, so we catch panics
            let result = std::panic::AssertUnwindSafe(run::do_run(self.config.clone(), &matches, None)).catch_unwind().await;
            
            match result {
                Ok(_) => Ok(CallToolResult::success(vec![Content::text(
                    "Successfully ran app locally".to_string()
                )])),
                Err(_) => Ok(CallToolResult::error(vec![Content::text(
                    "Failed to run locally - check that you have a valid Towerfile and are logged in".to_string()
                )]))
            }
        }
    }

    impl ServerHandler for TowerService {
        fn list_tools(
            &self,
            _request: Option<rmcp::model::PaginatedRequestParam>,
            _context: RequestContext<RoleServer>,
        ) -> impl std::future::Future<Output = Result<ListToolsResult, McpError>> + Send + '_ {
            async {
                let mut schema1 = Map::new();
                schema1.insert("type".to_string(), json!("object"));
                schema1.insert("properties".to_string(), json!({}));
                schema1.insert("required".to_string(), json!([]));

                let mut schema2 = Map::new();
                schema2.insert("type".to_string(), json!("object"));
                schema2.insert("properties".to_string(), json!({
                    "name": {
                        "type": "string",
                        "description": "App name"
                    }
                }));
                schema2.insert("required".to_string(), json!(["name"]));

                let mut schema3 = Map::new();
                schema3.insert("type".to_string(), json!("object"));
                schema3.insert("properties".to_string(), json!({
                    "name": {
                        "type": "string",
                        "description": "App name"
                    }
                }));
                schema3.insert("required".to_string(), json!(["name"]));

                let mut schema4 = Map::new();
                schema4.insert("type".to_string(), json!("object"));
                schema4.insert("properties".to_string(), json!({
                    "name": {
                        "type": "string",
                        "description": "App name"
                    },
                    "seq": {
                        "type": "string",
                        "description": "Run sequence number"
                    }
                }));
                schema4.insert("required".to_string(), json!(["name", "seq"]));

                let mut schema5 = Map::new();
                schema5.insert("type".to_string(), json!("object"));
                schema5.insert("properties".to_string(), json!({
                    "path": {
                        "type": "string",
                        "description": "Path to the directory containing your Tower app (optional, defaults to current directory)"
                    }
                }));
                schema5.insert("required".to_string(), json!([]));

                let tools = vec![
                    Tool {
                        name: "tower_apps_list".into(),
                        description: Some("List all Tower apps in your account".into()),
                        input_schema: Arc::new(schema1),
                        annotations: None,
                        output_schema: None,
                    },
                    Tool {
                        name: "tower_apps_create".into(),
                        description: Some("Create a new Tower app".into()),
                        input_schema: Arc::new(schema2),
                        annotations: None,
                        output_schema: None,
                    },
                    Tool {
                        name: "tower_apps_show".into(),
                        description: Some("Show details for a Tower app and its recent runs".into()),
                        input_schema: Arc::new(schema3.clone()),
                        annotations: None,
                        output_schema: None,
                    },
                    Tool {
                        name: "tower_apps_logs".into(),
                        description: Some("Get logs for a specific Tower app run".into()),
                        input_schema: Arc::new(schema4),
                        annotations: None,
                        output_schema: None,
                    },
                    Tool {
                        name: "tower_deploy".into(),
                        description: Some("Deploy your app to Tower cloud".into()),
                        input_schema: Arc::new(schema5.clone()),
                        annotations: None,
                        output_schema: None,
                    },
                    Tool {
                        name: "tower_run".into(),
                        description: Some("Run your app locally".into()),
                        input_schema: Arc::new(schema5),
                        annotations: None,
                        output_schema: None,
                    },
                ];
                Ok(ListToolsResult { 
                    tools,
                    next_cursor: None,
                })
            }
        }

        fn call_tool(
            &self,
            request: CallToolRequestParam,
            _context: RequestContext<RoleServer>,
        ) -> impl std::future::Future<Output = Result<CallToolResult, McpError>> + Send + '_ {
            async move {
                match request.name.as_ref() {
                    "tower_apps_list" => self.handle_apps_list().await,
                    "tower_apps_create" => self.handle_apps_create(&request).await,
                    "tower_apps_show" => self.handle_apps_show(&request).await,
                    "tower_apps_logs" => self.handle_apps_logs(&request).await,
                    "tower_deploy" => self.handle_deploy(&request).await,
                    "tower_run" => self.handle_run(&request).await,
                    _ => Ok(CallToolResult::error(vec![Content::text(format!("Unknown tool: {}", request.name))]))
                }
            }
        }
    }

    let service = TowerService::new(config);
    let server = service.serve(stdio()).await?;
    server.waiting().await?;
    Ok(())
}