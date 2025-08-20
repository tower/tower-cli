#[cfg(test)]
mod tests {
    use crate::mcp::{build_tools, TOOLS};
    use serde_json::{json, Map};
    use rmcp::model::CallToolRequestParam;
    use std::borrow::Cow;

    fn create_call_tool_request(name: &'static str, arguments: Option<Map<String, serde_json::Value>>) -> CallToolRequestParam {
        CallToolRequestParam {
            name: Cow::Borrowed(name),
            arguments,
        }
    }

    #[test]
    fn test_build_tools_contains_all_expected_tools() {
        let tools = build_tools();
        let tool_names: Vec<String> = tools.iter().map(|t| t.name.to_string()).collect();
        
        let expected_tools = vec![
            "tower_apps_list",
            "tower_apps_create", 
            "tower_apps_show",
            "tower_apps_logs",
            "tower_apps_delete",
            "tower_secrets_list",
            "tower_secrets_create",
            "tower_secrets_delete",
            "tower_teams_list",
            "tower_teams_switch",
            "tower_deploy",
            "tower_run",
        ];
        
        for expected_tool in expected_tools {
            assert!(tool_names.contains(&expected_tool.to_string()), 
                   "Missing expected tool: {}", expected_tool);
        }
    }

    #[test]
    fn test_build_tools_has_correct_schemas() {
        let tools = build_tools();
        let apps_create_tool = tools.iter()
            .find(|t| t.name == "tower_apps_create")
            .expect("tower_apps_create tool not found");
        
        let schema = &apps_create_tool.input_schema;
        assert!(schema.contains_key("type"));
        assert!(schema.contains_key("properties"));
        assert!(schema.contains_key("required"));
        
        let properties = schema.get("properties").unwrap().as_object().unwrap();
        assert!(properties.contains_key("name"));
        
        let required = schema.get("required").unwrap().as_array().unwrap();
        assert!(required.contains(&json!("name")));
    }

    #[test]
    fn test_parameter_validation_with_request() {
        let mut args = Map::new();
        args.insert("name".to_string(), json!("test-app"));
        let request = create_call_tool_request("test", Some(args));
        
        let name = request.arguments.as_ref()
            .and_then(|args| args.get("name"))
            .and_then(|v| v.as_str());
        assert_eq!(name, Some("test-app"));
    }

    #[test]
    fn test_missing_parameter_handling() {
        let request = create_call_tool_request("test", None);
        
        let name = request.arguments.as_ref()
            .and_then(|args| args.get("name"))
            .and_then(|v| v.as_str());
        assert_eq!(name, None);
    }

    #[test]
    fn test_tool_definitions_have_required_fields() {
        for tool_def in TOOLS {
            assert!(!tool_def.name.is_empty(), "Tool name cannot be empty");
            assert!(!tool_def.description.is_empty(), "Tool description cannot be empty");
            
            for param in tool_def.params {
                assert!(!param.name.is_empty(), "Parameter name cannot be empty for tool {}", tool_def.name);
                assert!(!param.description.is_empty(), "Parameter description cannot be empty for tool {}", tool_def.name);
            }
        }
    }

    #[test]
    fn test_required_parameters_are_properly_marked() {
        let apps_create = TOOLS.iter().find(|t| t.name == "tower_apps_create").unwrap();
        assert_eq!(apps_create.params.len(), 1);
        assert!(apps_create.params[0].required);
        assert_eq!(apps_create.params[0].name, "name");

        let secrets_list = TOOLS.iter().find(|t| t.name == "tower_secrets_list").unwrap();
        let optional_params: Vec<_> = secrets_list.params.iter().filter(|p| !p.required).collect();
        assert!(optional_params.len() > 0, "secrets_list should have optional parameters");
    }

    #[test]
    fn test_tool_name_consistency() {
        let tools = build_tools();
        let static_tool_names: Vec<&str> = TOOLS.iter().map(|t| t.name).collect();
        let dynamic_tool_names: Vec<String> = tools.iter().map(|t| t.name.to_string()).collect();
        
        for static_name in static_tool_names {
            assert!(dynamic_tool_names.contains(&static_name.to_string()), 
                   "Tool name {} not found in built tools", static_name);
        }
    }

    #[test]
    fn test_boolean_parameter_parsing() {
        let request_true = create_call_tool_request("test", Some({
            let mut args = Map::new();
            args.insert("all".to_string(), json!("true"));
            args
        }));
        
        let request_false = create_call_tool_request("test", Some({
            let mut args = Map::new();
            args.insert("all".to_string(), json!("false"));
            args
        }));
        
        let request_missing = create_call_tool_request("test", None);
        assert_eq!(
            request_true.arguments.as_ref()
                .and_then(|args| args.get("all"))
                .and_then(|v| v.as_str())
                .map(|v| v == "true")
                .unwrap_or(false),
            true
        );
        
        assert_eq!(
            request_false.arguments.as_ref()
                .and_then(|args| args.get("all"))
                .and_then(|v| v.as_str())
                .map(|v| v == "true")
                .unwrap_or(false),
            false
        );
        
        assert_eq!(
            request_missing.arguments.as_ref()
                .and_then(|args| args.get("all"))
                .and_then(|v| v.as_str())
                .map(|v| v == "true")
                .unwrap_or(false),
            false
        );
    }

    #[test]
    fn test_data_transformation_logic() {
        let mock_app_data = json!({
            "name": "test-app",
            "short_description": "A test application", 
            "created_at": "2024-01-01T00:00:00Z",
            "status": "Running"
        });
        let transformed = json!({
            "name": mock_app_data["name"],
            "description": mock_app_data["short_description"],
            "created_at": mock_app_data["created_at"],
            "status": format!("{:?}", mock_app_data["status"].as_str().unwrap())
        });
        
        assert_eq!(transformed["name"], "test-app");
        assert_eq!(transformed["description"], "A test application");
        assert_eq!(transformed["created_at"], "2024-01-01T00:00:00Z");
        assert!(transformed["status"].as_str().unwrap().contains("Running"));
    }

    #[test]
    fn test_logs_formatting_logic() {
        let mock_log_lines = vec![
            json!({"timestamp": "2024-01-01T10:00:00Z", "message": "App started"}),
            json!({"timestamp": "2024-01-01T10:00:01Z", "message": "Processing request"}),
            json!({"timestamp": "2024-01-01T10:00:02Z", "message": "Request completed"})
        ];
        let formatted_logs: Vec<String> = mock_log_lines.into_iter()
            .map(|log| format!("{}: {}", 
                log["timestamp"].as_str().unwrap(),
                log["message"].as_str().unwrap()
            ))
            .collect();
        
        let logs_text = formatted_logs.join("\n");
        
        assert!(logs_text.contains("2024-01-01T10:00:00Z: App started"));
        assert!(logs_text.contains("2024-01-01T10:00:01Z: Processing request"));
        assert!(logs_text.contains("2024-01-01T10:00:02Z: Request completed"));
        assert_eq!(logs_text.matches('\n').count(), 2);
    }
}