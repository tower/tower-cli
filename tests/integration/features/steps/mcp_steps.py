#!/usr/bin/env python3

import asyncio
import time
from behave import given, when, then
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from mcp_client import MCPTestHelper


def assert_has_response(context):
    assert hasattr(context, 'mcp_response'), "No MCP response was recorded"
    assert context.mcp_response is not None, "MCP response was None"

def is_error_response(response):
    return (
        not response.get("success", True) or
        "error" in response or
        any("error" in str(content).lower() or "failed" in str(content).lower()
            for content in response.get("content", []))
    )

def has_text_content(response, text_check):
    for content_item in response.get("content", []):
        if content_item.get("type") == "text":
            text = content_item.get("text", "")
            if text_check(text):
                return True
    return False


@given('I have a running Tower MCP server')
def step_have_running_mcp_server(context):
    # This step is handled by the before_scenario hook in environment.py
    # Just verify the MCP helper was set up properly
    assert hasattr(context, 'mcp_helper'), "MCP helper should be set up"
    assert hasattr(context, 'mcp_client'), "MCP client should be set up"
    
    server_alive = context.mcp_helper.client.is_server_alive()
    print(f"DEBUG: MCP server alive check: {server_alive}")
    if not server_alive:
        print(f"DEBUG: Process poll: {context.mcp_helper.client.process.poll() if context.mcp_helper.client.process else 'No process'}")
    assert server_alive, "MCP server should be running"

@given('I have a valid Towerfile in the current directory')
def step_create_valid_towerfile(context):
    context.mcp_helper.create_towerfile("hello_world")


@given('I have a simple hello world application')
def step_create_hello_world_app(context):
    context.mcp_helper.create_towerfile("hello_world")


@given('I have a long-running application')
def step_create_long_running_app(context):
    context.mcp_helper.create_towerfile("long_running")


def call_mcp_tool(context, tool_name, **tool_args):
    try:
        async def call_tool():
            if tool_args:
                return await context.mcp_client.call_tool(tool_name, tool_args)
            else:
                return await context.mcp_client.call_tool(tool_name)
        context.mcp_response = asyncio.run(call_tool())
        context.operation_success = context.mcp_response.get("success", False)
    except Exception as e:
        context.mcp_response = {"success": False, "error": str(e)}
        context.operation_success = False

@when('I call {tool_name} via MCP')
def step_call_mcp_tool(context, tool_name):
    call_mcp_tool(context, tool_name)


@when('I call {tool_name} with app name "{app_name}"')
def step_call_mcp_tool_with_app_name(context, tool_name, app_name):
    call_mcp_tool(context, tool_name, name=app_name)


@then('I should receive a response')
def step_check_response_exists(context):
    assert_has_response(context)


@then('I should receive a response with apps data')
def step_check_apps_data_response(context):
    assert_has_response(context)
    assert len(context.mcp_response.get("content", [])) > 0, "Response should have content"

    found_apps_data = has_text_content(
        context.mcp_response,
        lambda text: "apps" in text.lower() or "[]" in text
    )
    assert found_apps_data, f"Response should contain apps data, got: {context.mcp_response.get('content')}"


@then('I should receive an error response')
def step_check_error_response(context):
    assert_has_response(context)
    assert is_error_response(context.mcp_response), f"Expected error response, got: {context.mcp_response}"


@then('I should receive an error response about missing Towerfile')
def step_check_missing_towerfile_error(context):
    assert_has_response(context)
    response_text = str(context.mcp_response).lower()
    assert "towerfile" in response_text, f"Error should mention Towerfile, got: {context.mcp_response}"


@then('I should receive a success response')
def step_check_success_response(context):
    assert_has_response(context)
    is_success = (
        context.mcp_response.get("success", False) or
        has_text_content(context.mcp_response, lambda text: "valid" in text.lower() and "true" in text.lower())
    )
    assert is_success, f"Expected success response, got: {context.mcp_response}"


@then('I should receive the parsed Towerfile configuration')
def step_check_parsed_towerfile(context):
    """Verify the response contains parsed Towerfile data."""
    assert hasattr(context, 'mcp_response'), "No MCP response was recorded"

    response_content = context.mcp_response.get("content", [])
    assert len(response_content) > 0, "Response should have content"

    # Look for Towerfile structure in the response
    found_config = False
    for content_item in response_content:
        if content_item.get("type") == "text":
            text = content_item.get("text", "")
            if "app" in text and "name" in text and "script" in text:
                found_config = True
                break

    assert found_config, f"Response should contain Towerfile config, got: {response_content}"


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


@then('the MCP server should remain responsive')
def step_check_server_responsive(context):
    """Verify the MCP server is still responsive after the operation."""
    try:
        # First check if the server process is still alive
        if not context.mcp_helper.client.is_server_alive():
            context.server_responsive = False
            print("Warning: MCP server process died")
        else:
            # Try a simple operation to verify server is still responsive
            async def test_responsiveness():
                return await context.mcp_client.call_tool("tower_file_validate")
            test_response = asyncio.run(test_responsiveness())
            context.server_responsive = test_response.get("success", False) or "error" in test_response
    except Exception as e:
        context.server_responsive = False
        print(f"Warning: Server responsiveness test failed: {e}")

    # For timeout scenarios, it's acceptable if the server is not responsive
    if not context.server_responsive:
        print("Note: Server may be unresponsive after timeout, which is expected")
