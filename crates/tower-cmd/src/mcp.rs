use clap::Command;
use crate::{Config, api, deploy, run};
use rmcp::{ServerHandler, ServiceExt, transport::stdio, model::{CallToolResult, Content, CallToolRequestParam, ListToolsResult}, ErrorData as McpError, service::RequestContext, service::RoleServer};
use tower_telemetry::tracing;
use anyhow::Result;
use serde_json::{json, Value, Map};
use std::sync::Arc;
use futures_util::FutureExt;

struct Param {
    name: &'static str,
    description: &'static str,
    required: bool,
}

struct ToolDef {
    name: &'static str,
    description: &'static str,
    params: &'static [Param],
}

const TOOLS: &[ToolDef] = &[
    ToolDef {
        name: "tower_apps_list",
        description: "List all Tower apps in your account",
        params: &[],
    },
    ToolDef {
        name: "tower_apps_create", 
        description: "Create a new Tower app",
        params: &[Param { name: "name", description: "App name", required: true }],
    },
    ToolDef {
        name: "tower_apps_show",
        description: "Show details for a Tower app and its recent runs", 
        params: &[Param { name: "name", description: "App name", required: true }],
    },
    ToolDef {
        name: "tower_apps_logs",
        description: "Get logs for a specific Tower app run",
        params: &[
            Param { name: "name", description: "App name", required: true },
            Param { name: "seq", description: "Run sequence number", required: true },
        ],
    },
    ToolDef {
        name: "tower_deploy",
        description: "Deploy your app to Tower cloud",
        params: &[Param { name: "path", description: "Directory containing your Tower app", required: false }],
    },
    ToolDef {
        name: "tower_run",
        description: "Run your app locally",
        params: &[Param { name: "path", description: "Directory containing your Tower app", required: false }],
    },
];

fn build_tools() -> Vec<rmcp::model::Tool> {
    TOOLS.iter().map(|def| {
        let properties: Map<String, Value> = def.params.iter()
            .map(|p| (p.name.to_string(), json!({"type": "string", "description": p.description})))
            .collect();
        
        let required = def.params.iter()
            .filter(|p| p.required)
            .map(|p| json!(p.name))
            .collect::<Vec<_>>();

        let schema = Arc::new(vec![
            ("type".to_string(), json!("object")),
            ("properties".to_string(), json!(properties)),
            ("required".to_string(), json!(required)),
        ].into_iter().collect());

        rmcp::model::Tool {
            name: def.name.into(),
            description: Some(def.description.into()),
            input_schema: schema,
            annotations: None,
            output_schema: None,
        }
    }).collect()
}


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

        fn get_param<'a>(&self, request: &'a CallToolRequestParam, name: &str) -> Result<&'a str, McpError> {
            request.arguments.as_ref()
                .and_then(|args| args.get(name))
                .and_then(|v| v.as_str())
                .ok_or_else(|| McpError::invalid_params("parameter missing", None))
        }

        fn success<T: serde::Serialize>(data: T) -> Result<CallToolResult, McpError> {
            let text = serde_json::to_string_pretty(&data)
                .map_err(|_| McpError::invalid_params("serialization failed", None))?;
            Ok(CallToolResult::success(vec![Content::text(text)]))
        }

        fn error(message: &str) -> Result<CallToolResult, McpError> {
            Ok(CallToolResult::error(vec![Content::text(message.to_string())]))
        }

        async fn handle_apps_list(&self, _request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
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
                    Self::success(json!({"apps": apps}))
                },
                Err(e) => Self::error(&format!("Failed to list apps: {}", e)),
            }
        }

        async fn handle_apps_create(&self, request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let name = self.get_param(request, "name")?;

            match api::create_app(&self.config, name, "").await {
                Ok(response) => Ok(CallToolResult::success(vec![Content::text(
                    format!("Created app '{}'", response.app.name)
                )])),
                Err(e) => Self::error(&format!("Failed to create app: {}", e)),
            }
        }

        async fn handle_apps_show(&self, request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let name = self.get_param(request, "name")?;

            match api::describe_app(&self.config, name).await {
                Ok(response) => {
                    let app = response.app;
                    let runs = response.runs;
                    
                    let data = json!({
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
                    Self::success(data)
                },
                Err(e) => Self::error(&format!("Failed to show app: {}", e)),
            }
        }

        async fn handle_apps_logs(&self, request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let name = self.get_param(request, "name")?;
            let seq_str = self.get_param(request, "seq")?;
            let seq: i64 = seq_str.parse()
                .map_err(|_| McpError::invalid_params("seq must be a number", None))?;

            match api::describe_run_logs(&self.config, name, seq).await {
                Ok(response) => {
                    let logs = response.log_lines.into_iter()
                        .map(|log| format!("{}: {}", log.timestamp, log.message))
                        .collect::<Vec<_>>()
                        .join("\n");
                    
                    Ok(CallToolResult::success(vec![Content::text(
                        format!("Logs for app '{}' run {}:\n\n{}", name, seq, logs)
                    )]))
                },
                Err(e) => Self::error(&format!("Failed to get logs: {}", e)),
            }
        }

        async fn handle_deploy(&self, _request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let config = self.config.clone();
            let matches = clap::ArgMatches::default();
            
            let result = std::panic::AssertUnwindSafe(async move {
                deploy::do_deploy(config, &matches).await
            });
            
            match result.catch_unwind().await {
                Ok(_) => Ok(CallToolResult::success(vec![Content::text("App deployed".to_string())])),
                Err(_) => Self::error("Deploy failed - check Towerfile and login status"),
            }
        }

        async fn handle_run(&self, _request: &CallToolRequestParam) -> Result<CallToolResult, McpError> {
            let config = self.config.clone();
            let matches = clap::ArgMatches::default();
            
            let result = std::panic::AssertUnwindSafe(async move {
                run::do_run(config, &matches, None).await
            });
            
            match result.catch_unwind().await {
                Ok(_) => Ok(CallToolResult::success(vec![Content::text("App ran locally".to_string())])),
                Err(_) => Self::error("Local run failed - check Towerfile and login status"),
            }
        }
    }

    impl ServerHandler for TowerService {
        fn list_tools(&self, _: Option<rmcp::model::PaginatedRequestParam>, _: RequestContext<RoleServer>)
            -> impl std::future::Future<Output = Result<ListToolsResult, McpError>> + Send + '_
        {
            async { Ok(ListToolsResult { tools: build_tools(), next_cursor: None }) }
        }

        fn call_tool(&self, request: CallToolRequestParam, _: RequestContext<RoleServer>)
            -> impl std::future::Future<Output = Result<CallToolResult, McpError>> + Send + '_
        {
            async move {
                match request.name.as_ref() {
                    "tower_apps_list" => self.handle_apps_list(&request).await,
                    "tower_apps_create" => self.handle_apps_create(&request).await,
                    "tower_apps_show" => self.handle_apps_show(&request).await,
                    "tower_apps_logs" => self.handle_apps_logs(&request).await,
                    "tower_deploy" => self.handle_deploy(&request).await,
                    "tower_run" => self.handle_run(&request).await,
                    _ => Self::error(&format!("Unknown tool: {}", request.name))
                }
            }
        }
    }

    let service = TowerService::new(config);
    let server = service.serve(stdio()).await?;
    server.waiting().await?;
    Ok(())
}