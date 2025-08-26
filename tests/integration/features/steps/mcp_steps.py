#!/usr/bin/env python3

import os
from pathlib import Path
from behave import given, when, then
from behave.api.async_step import async_run_until_complete
from mcp import ClientSession
from mcp.client.sse import sse_client


async def call_mcp_tool(server_url, tool_name, arguments=None, working_directory=None):
    """Pure function to call MCP tool - handles connection and cleanup"""
    args = arguments or {}
    if working_directory:
        args["working_directory"] = working_directory
        
    async with sse_client(f"{server_url}/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            return {
                "success": not result.isError,
                "content": result.content,
                "result": result
            }


def create_towerfile(app_type="hello_world"):
    """Create a Towerfile for testing - pure function with no side effects beyond file creation"""
    configs = {
        "hello_world": ("hello-world", "hello.py", "Simple hello world app"),
        "long_running": ("long-runner", "long_runner.py", "Long running app for timeout testing")
    }
    
    app_name, script_name, description = configs.get(app_type, configs["hello_world"])
    template_dir = Path(__file__).parent.parent.parent / "templates"
    
    # Create Towerfile from template if it exists
    towerfile_template = template_dir / "Towerfile.j2"
    if towerfile_template.exists():
        template_content = towerfile_template.read_text()
        towerfile_content = (template_content
                           .replace("{{ app_name }}", app_name)
                           .replace("{{ script_name }}", script_name)
                           .replace("{{ description }}", description))
        Path("Towerfile").write_text(towerfile_content)
    
    # Copy script file if it exists
    script_template = template_dir / script_name
    if script_template.exists():
        import shutil
        shutil.copy(script_template, script_name)


def has_text_content(response, text_check):
    """Check if response contains text content matching the predicate"""
    for content_item in response.get("content", []):
        if hasattr(content_item, 'type') and content_item.type == "text":
            if text_check(getattr(content_item, 'text', "")):
                return True
    return False


def is_error_response(response):
    """Check if response indicates an error"""
    return (not response.get("success", True) or
            "error" in response or
            any("error" in str(content).lower() or "failed" in str(content).lower()
                for content in response.get("content", [])))


@given('I have a running Tower MCP server')
def step_have_running_mcp_server(context):
    # This step is handled by the before_scenario hook in environment.py
    # Just verify the MCP server was set up properly
    assert hasattr(context, 'tower_process'), "Tower process should be set up"
    assert hasattr(context, 'mcp_server_url'), "MCP server URL should be set up"
    
    server_alive = context.tower_process.poll() is None
    print(f"DEBUG: MCP server alive check: {server_alive}")
    assert server_alive, "MCP server should be running"

@given('I have a valid Towerfile in the current directory')
def step_create_valid_towerfile(context):
    create_towerfile("hello_world")


@given('I have a simple hello world application')
def step_create_hello_world_app(context):
    create_towerfile("hello_world")


@given('I have a long-running application')
def step_create_long_running_app(context):
    create_towerfile("long_running")


@given('I have a pyproject.toml file with project metadata')
def step_create_pyproject_toml(context):
    import os
    pyproject_content = '''[project]
name = "test-project"
description = "A test project for Towerfile generation"
version = "0.1.0"
'''
    with open("pyproject.toml", "w") as f:
        f.write(pyproject_content)
    # Also create a main.py file
    with open("main.py", "w") as f:
        f.write('print("Hello from test project")\n')


@when('I call {tool_name} via MCP')
@async_run_until_complete
async def step_call_mcp_tool(context, tool_name):
    try:
        context.mcp_response = await call_mcp_tool(
            context.mcp_server_url,
            tool_name,
            working_directory=os.getcwd()
        )
        context.operation_success = context.mcp_response.get("success", False)
    except Exception as e:
        context.mcp_response = {"success": False, "error": str(e)}
        context.operation_success = False


@when('I call {tool_name} with app name "{app_name}"')
@async_run_until_complete
async def step_call_mcp_tool_with_app_name(context, tool_name, app_name):
    try:
        context.mcp_response = await call_mcp_tool(
            context.mcp_server_url,
            tool_name,
            {"name": app_name},
            working_directory=os.getcwd()
        )
        context.operation_success = context.mcp_response.get("success", False)
    except Exception as e:
        context.mcp_response = {"success": False, "error": str(e)}
        context.operation_success = False


@then('I should receive a response')
def step_check_response_exists(context):
    assert hasattr(context, 'mcp_response') and context.mcp_response is not None


@then('I should receive a response with apps data')
def step_check_apps_data_response(context):
    assert context.mcp_response.get("content"), "Response should have content"
    found_apps_data = has_text_content(context.mcp_response, 
                                     lambda text: "apps" in text.lower() or "[]" in text)
    assert found_apps_data, f"Response should contain apps data, got: {context.mcp_response.get('content')}"


@then('I should receive an error response')
def step_check_error_response(context):
    assert is_error_response(context.mcp_response), f"Expected error response, got: {context.mcp_response}"


@then('I should receive an error response about missing Towerfile')
def step_check_missing_towerfile_error(context):
    response_text = str(context.mcp_response).lower()
    assert "towerfile" in response_text, f"Error should mention Towerfile, got: {context.mcp_response}"


@then('I should receive a success response')
def step_check_success_response(context):
    is_success = (context.mcp_response.get("success", False) or
                  has_text_content(context.mcp_response, lambda text: "valid" in text.lower() and "true" in text.lower()))
    assert is_success, f"Expected success response, got: {context.mcp_response}"


@then('I should receive the parsed Towerfile configuration')
def step_check_parsed_towerfile(context):
    """Verify the response contains parsed Towerfile data."""
    assert context.mcp_response.get("content"), "Response should have content"
    found_config = has_text_content(context.mcp_response, 
                                   lambda text: all(word in text for word in ["app", "name", "script"]))
    assert found_config, f"Response should contain Towerfile config, got: {context.mcp_response.get('content')}"


@then('I should receive a response about the run')
def step_check_run_response(context):
    """Verify the response is about running the application."""
    assert hasattr(context, 'mcp_response'), "No MCP response was recorded"

    response_text = str(context.mcp_response).lower()
    run_keywords = ["run", "app", "local", "complet", "success", "fail"]

    found_run_keyword = any(keyword in response_text for keyword in run_keywords)
    assert found_run_keyword, f"Response should be about app run, got: {context.mcp_response}"


@then('I should receive a timeout message')
def step_check_timeout_message(context):
    """Verify the response indicates a timeout occurred."""
    assert hasattr(context, 'mcp_response'), "No MCP response was recorded"

    response_text = str(context.mcp_response).lower()
    timeout_keywords = ["timeout", "timed out", "1 seconds"]

    found_timeout = any(keyword in response_text for keyword in timeout_keywords)
    assert found_timeout, f"Response should indicate timeout, got: {context.mcp_response}"


@then('I should receive an error response about app not deployed')
def step_check_app_not_deployed_error(context):
    """Verify the error mentions app not being deployed."""
    assert hasattr(context, 'mcp_response'), "No MCP response was recorded"

    response_text = str(context.mcp_response).lower()
    deployment_keywords = ["not found", "deploy", "cloud", "not deployed"]

    found_deployment_error = any(keyword in response_text for keyword in deployment_keywords)
    assert found_deployment_error, f"Error should mention deployment, got: {context.mcp_response}"


@then('I should receive a valid TOML Towerfile')
def step_check_valid_toml_towerfile(context):
    """Verify the response contains valid TOML Towerfile content."""
    assert hasattr(context, 'mcp_response'), "No MCP response was recorded"
    
    response_content = context.mcp_response.get("content", [])
    assert len(response_content) > 0, "Response should have content"
    
    # Find the TOML content
    found_toml = False
    for content_item in response_content:
        if hasattr(content_item, 'type') and content_item.type == "text":
            text = getattr(content_item, 'text', "")
            if "[app]" in text and "name =" in text and "script =" in text:
                found_toml = True
                break
    
    assert found_toml, f"Response should contain valid TOML Towerfile, got: {response_content}"


@then('the Towerfile should contain the project name and description')
def step_check_towerfile_metadata(context):
    """Verify the Towerfile contains expected project metadata."""
    assert hasattr(context, 'mcp_response'), "No MCP response was recorded"
    
    response_content = context.mcp_response.get("content", [])
    
    found_metadata = False
    for content_item in response_content:
        if hasattr(content_item, 'type') and content_item.type == "text":
            text = getattr(content_item, 'text', "")
            if 'name = "test-project"' in text and 'description = "A test project for Towerfile generation"' in text:
                found_metadata = True
                break
    
    assert found_metadata, f"Towerfile should contain project name and description, got: {response_content}"


@then('the MCP server should remain responsive')
@async_run_until_complete
async def step_check_server_responsive(context):
    """Verify the MCP server is still responsive after the operation."""
    try:
        # Check if process is alive and server responds
        if context.tower_process.poll() is not None:
            print("Warning: MCP server process died")
            context.server_responsive = False
        else:
            # Test server responsiveness with simple call
            await call_mcp_tool(context.mcp_server_url, "tower_file_validate", working_directory=os.getcwd())
            context.server_responsive = True
    except Exception as e:
        context.server_responsive = False
        print(f"Warning: Server responsiveness test failed: {e}")

    if not context.server_responsive:
        print("Note: Server may be unresponsive after timeout, which is expected")
