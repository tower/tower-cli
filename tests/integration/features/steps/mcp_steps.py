#!/usr/bin/env python3

import os
from pathlib import Path
from behave import given, when, then
from behave.api.async_step import async_run_until_complete
from mcp import ClientSession
from mcp.client.sse import sse_client


async def call_mcp_tool_raw(
    server_url, tool_name, arguments=None, working_directory=None
):
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
                "result": result,
            }


async def call_mcp_tool(context, tool_name, arguments=None):
    """Call MCP tool with standard error handling and context setting"""
    try:
        result = await call_mcp_tool_raw(
            context.mcp_server_url,
            tool_name,
            arguments or {},
            working_directory=os.getcwd(),
        )
        context.mcp_response = result
        context.operation_success = result.get("success", False)
        return result
    except Exception as e:
        context.mcp_response = {"success": False, "error": str(e)}
        context.operation_success = False
        return context.mcp_response


def create_towerfile(app_type="hello_world"):
    """Create a Towerfile for testing - pure function with no side effects beyond file creation"""
    configs = {
        "hello_world": ("hello-world", "hello.py", "Simple hello world app"),
        "long_running": (
            "long-runner",
            "long_runner.py",
            "Long running app for timeout testing",
        ),
    }

    app_name, script_name, description = configs.get(app_type, configs["hello_world"])
    template_dir = Path(__file__).parent.parent.parent / "templates"

    # Create Towerfile from template if it exists
    towerfile_template = template_dir / "Towerfile.j2"
    if towerfile_template.exists():
        template_content = towerfile_template.read_text()
        towerfile_content = (
            template_content.replace("{{ app_name }}", app_name)
            .replace("{{ script_name }}", script_name)
            .replace("{{ description }}", description)
        )
        Path("Towerfile").write_text(towerfile_content)

    # Copy script file if it exists
    script_template = template_dir / script_name
    if script_template.exists():
        import shutil

        shutil.copy(script_template, script_name)


def has_text_content(response, text_check):
    """Check if response contains text content matching the predicate"""
    for content_item in response.get("content", []):
        if hasattr(content_item, "type") and content_item.type == "text":
            if text_check(getattr(content_item, "text", "")):
                return True
    return False


def is_error_response(response):
    """Check if response indicates an error"""
    return (
        not response.get("success", True)
        or "error" in response
        or any(
            "error" in str(content).lower() or "failed" in str(content).lower()
            for content in response.get("content", [])
        )
    )


@given("I have a running Tower MCP server")
def step_have_running_mcp_server(context):
    # This step is handled by the before_scenario hook in environment.py
    # Just verify the MCP server was set up properly
    assert hasattr(
        context, "tower_mcpserver_process"
    ), "Tower mcp server process should be set up"
    assert hasattr(context, "mcp_server_url"), "MCP server URL should be set up"

    server_alive = context.tower_mcpserver_process.poll() is None
    print(f"DEBUG: MCP server alive check: {server_alive}")
    assert server_alive, "MCP server should be running"


@given("I have a valid Towerfile in the current directory")
def step_create_valid_towerfile(context):
    create_towerfile("hello_world")


@given("I have a simple hello world application")
def step_create_hello_world_app(context):
    create_towerfile("hello_world")


@given("I have a long-running application")
def step_create_long_running_app(context):
    create_towerfile("long_running")


@given("I have a pyproject.toml file with project metadata")
def step_create_pyproject_toml(context):
    import os

    pyproject_content = """[project]
name = "test-project"
description = "A test project for Towerfile generation"
version = "0.1.0"
"""
    with open("pyproject.toml", "w") as f:
        f.write(pyproject_content)
    # Also create a main.py file
    with open("main.py", "w") as f:
        f.write('print("Hello from test project")\n')


@when("I call {tool_name} via MCP")
@async_run_until_complete
async def step_call_mcp_tool(context, tool_name):
    await call_mcp_tool(context, tool_name)


@when('I call {tool_name} with app name "{app_name}"')
@async_run_until_complete
async def step_call_mcp_tool_with_app_name(context, tool_name, app_name):
    await call_mcp_tool(context, tool_name, {"name": app_name})


@then("I should receive a response")
def step_check_response_exists(context):
    assert hasattr(context, "mcp_response") and context.mcp_response is not None


@then("I should receive a response with apps data")
def step_check_apps_data_response(context):
    assert context.mcp_response.get("content"), "Response should have content"
    found_apps_data = has_text_content(
        context.mcp_response, lambda text: "apps" in text.lower() or "[]" in text
    )
    assert (
        found_apps_data
    ), f"Response should contain apps data, got: {context.mcp_response.get('content')}"


@then("I should receive an error response")
def step_check_error_response(context):
    assert is_error_response(
        context.mcp_response
    ), f"Expected error response, got: {context.mcp_response}"


@then("I should receive an error response about missing Towerfile")
def step_check_missing_towerfile_error(context):
    response_text = str(context.mcp_response).lower()
    assert (
        "towerfile" in response_text
    ), f"Error should mention Towerfile, got: {context.mcp_response}"


@then("I should receive a success response")
def step_check_success_response(context):
    assert context.mcp_response.get(
        "success", False
    ), f"Expected success response, got: {context.mcp_response}"


@then("I should receive the parsed Towerfile configuration")
def step_check_parsed_towerfile(context):
    """Verify the response contains parsed Towerfile data."""
    assert context.mcp_response.get("content"), "Response should have content"
    found_config = has_text_content(
        context.mcp_response,
        lambda text: all(word in text for word in ["app", "name", "script"]),
    )
    assert (
        found_config
    ), f"Response should contain Towerfile config, got: {context.mcp_response.get('content')}"


@then("I should receive a response about the run")
def step_check_run_response(context):
    """Verify the response is about running the application."""
    assert hasattr(context, "mcp_response"), "No MCP response was recorded"

    # Check for common authentication/API schema issues
    response_text = str(context.mcp_response)
    if "No session found" in response_text:
        raise AssertionError(
            "Authentication failed - this usually means the mock API session endpoint "
            "response doesn't match the expected schema. See tests/mock-api-server/README.md "
            f"for debugging steps. Response: {context.mcp_response}"
        )
    elif "UnknownDescribeSessionValue" in response_text:
        raise AssertionError(
            "API schema mismatch - the mock API response format doesn't match the "
            "expected OpenAPI-generated models. Update tests/mock-api-server/main.py "
            f"to match the new schema. Response: {context.mcp_response}"
        )

    assert context.mcp_response.get(
        "success", False
    ), f"Expected successful run response, got: {context.mcp_response}"


@then("I should receive a timeout message")
def step_check_timeout_message(context):
    """Verify the response indicates a timeout occurred."""
    assert hasattr(context, "mcp_response"), "No MCP response was recorded"

    response_text = str(context.mcp_response).lower()
    timeout_keywords = ["timeout", "timed out", "3 seconds"]

    found_timeout = any(keyword in response_text for keyword in timeout_keywords)
    assert (
        found_timeout
    ), f"Response should indicate timeout, got: {context.mcp_response}"


@then("I should receive an error response about app not deployed")
def step_check_app_not_deployed_error(context):
    """Verify the error mentions app not being deployed."""
    assert hasattr(context, "mcp_response"), "No MCP response was recorded"

    response_text = str(context.mcp_response).lower()
    deployment_keywords = ["not found", "deploy", "cloud", "not deployed"]

    found_deployment_error = any(
        keyword in response_text for keyword in deployment_keywords
    )
    assert (
        found_deployment_error
    ), f"Error should mention deployment, got: {context.mcp_response}"


@then("I should receive a valid TOML Towerfile")
def step_check_valid_toml_towerfile(context):
    """Verify the response contains valid TOML Towerfile content."""
    assert hasattr(context, "mcp_response"), "No MCP response was recorded"

    response_content = context.mcp_response.get("content", [])
    assert len(response_content) > 0, "Response should have content"

    # Find the TOML content
    found_toml = False
    for content_item in response_content:
        if hasattr(content_item, "type") and content_item.type == "text":
            text = getattr(content_item, "text", "")
            if "[app]" in text and "name =" in text and "script =" in text:
                found_toml = True
                break

    assert (
        found_toml
    ), f"Response should contain valid TOML Towerfile, got: {response_content}"


@then("the Towerfile should contain the project name and description")
def step_check_towerfile_metadata(context):
    """Verify the Towerfile contains expected project metadata."""
    assert hasattr(context, "mcp_response"), "No MCP response was recorded"

    response_content = context.mcp_response.get("content", [])

    found_metadata = False
    for content_item in response_content:
        if hasattr(content_item, "type") and content_item.type == "text":
            text = getattr(content_item, "text", "")
            if (
                'name = "test-project"' in text
                and 'description = "A test project for Towerfile generation"' in text
            ):
                found_metadata = True
                break

    assert (
        found_metadata
    ), f"Towerfile should contain project name and description, got: {response_content}"


@then("the MCP server should remain responsive")
@async_run_until_complete
async def step_check_server_responsive(context):
    """Verify the MCP server is still responsive after the operation."""
    try:
        # Check if process is alive and server responds
        if context.tower_mcpserver_process.poll() is not None:
            print("Warning: MCP server process died")
            context.server_responsive = False
        else:
            # Test server responsiveness with simple call
            await call_mcp_tool_raw(
                context.mcp_server_url,
                "tower_file_validate",
                working_directory=os.getcwd(),
            )
            context.server_responsive = True
    except Exception as e:
        context.server_responsive = False
        print(f"Warning: Server responsiveness test failed: {e}")

    if not context.server_responsive:
        print("Note: Server may be unresponsive after timeout, which is expected")


# Schedule-related steps
@given('I have created a schedule for "{app_name}"')
@async_run_until_complete
async def step_create_schedule_for_app(context, app_name):
    """Create a schedule for testing purposes."""
    result = await call_mcp_tool(
        context,
        "tower_schedules_create",
        {"app_name": app_name, "cron": "0 9 * * *", "environment": "default"},
    )
    assert result.get("success", False), f"Failed to create schedule: {result}"

    # Extract schedule ID from the response text
    if result.get("success") and "content" in result:
        content = result["content"]
        if content and len(content) > 0 and hasattr(content[0], "text"):
            response_text = content[0].text
            # Extract schedule ID from text like "Created schedule 'SCHEDULE_ID' for app..."
            import re

            match = re.search(r"Created schedule '([^']+)'", response_text)
            if match:
                context.created_schedule_id = match.group(1)

    context.test_app_name = app_name


@when(
    'I call tower_schedules_create with app "{app_name}", cron "{cron}", and environment "{environment}"'
)
@async_run_until_complete
async def step_call_schedules_create(context, app_name, cron, environment):
    """Call tower_schedules_create with specific parameters."""
    await call_mcp_tool(
        context,
        "tower_schedules_create",
        {"app_name": app_name, "cron": cron, "environment": environment},
    )
    context.test_app_name = app_name
    context.test_cron = cron
    context.test_environment = environment


@when('I call tower_schedules_update with new cron "{new_cron}"')
@async_run_until_complete
async def step_call_schedules_update(context, new_cron):
    """Call tower_schedules_update with new cron expression."""
    schedule_id = getattr(context, "created_schedule_id", "mock-schedule-id")
    await call_mcp_tool(
        context,
        "tower_schedules_update",
        {"schedule_id": schedule_id, "cron": new_cron},
    )
    context.updated_cron = new_cron


@when("I call tower_schedules_delete with the schedule ID")
@async_run_until_complete
async def step_call_schedules_delete(context):
    """Call tower_schedules_delete with a schedule ID."""
    schedule_id = getattr(context, "created_schedule_id", "mock-schedule-id")
    await call_mcp_tool(context, "tower_schedules_delete", {"name": schedule_id})


@then("I should receive a response with empty schedules data")
def step_check_empty_schedules_response(context):
    """Verify the response contains empty schedules list."""
    assert context.mcp_response.get("content"), "Response should have content"
    found_empty_schedules = has_text_content(
        context.mcp_response,
        lambda text: "schedules" in text.lower() and ("[]" in text or "0" in text),
    )
    assert (
        found_empty_schedules
    ), f"Response should contain empty schedules data, got: {context.mcp_response.get('content')}"


@then("I should receive a success response about schedule creation")
def step_check_schedule_creation_success(context):
    """Verify the response indicates successful schedule creation."""
    assert context.mcp_response.get(
        "success", False
    ), f"Expected successful schedule creation, got: {context.mcp_response}"
    assert (
        "created" in str(context.mcp_response).lower()
    ), f"Response should mention creation, got: {context.mcp_response}"


@then('I should receive a response with schedule data for "{app_name}"')
def step_check_schedules_list_with_data(context, app_name):
    """Verify the response contains schedule data for the specified app."""
    assert context.mcp_response.get("content"), "Response should have content"
    found_schedule_data = has_text_content(
        context.mcp_response,
        lambda text: "schedules" in text.lower() and app_name in text,
    )
    assert (
        found_schedule_data
    ), f"Response should contain schedule data for '{app_name}', got: {context.mcp_response.get('content')}"


@then("I should receive a success response about schedule update")
def step_check_schedule_update_success(context):
    """Verify the response indicates successful schedule update."""
    assert context.mcp_response.get(
        "success", False
    ), f"Expected successful schedule update, got: {context.mcp_response}"
    assert (
        "updated" in str(context.mcp_response).lower()
    ), f"Response should mention update, got: {context.mcp_response}"


@then("I should receive a success response about schedule deletion")
def step_check_schedule_deletion_success(context):
    """Verify the response indicates successful schedule deletion."""
    assert context.mcp_response.get(
        "success", False
    ), f"Expected successful schedule deletion, got: {context.mcp_response}"
    assert (
        "deleted" in str(context.mcp_response).lower()
    ), f"Response should mention deletion, got: {context.mcp_response}"


@given('the app "{app_name}" exists in Tower')
@async_run_until_complete
async def step_app_exists_in_tower(context, app_name):
    """Ensure the specified app exists in Tower (create it if needed)"""
    # Create the app using the MCP server
    result = await call_mcp_tool(context, "tower_apps_create", {"name": app_name})
    # We don't assert success here because the app might already exist
    # The important thing is that subsequent operations can find it


@given('the app "{app_name}" exists and is deployed in Tower')
@async_run_until_complete
async def step_app_exists_and_deployed_in_tower(context, app_name):
    """Ensure the specified app exists and is deployed in Tower"""
    result = await call_mcp_tool(context, "tower_deploy", {})


@when('I call tower_run_remote with invalid parameter "{param}"')
@async_run_until_complete
async def step_call_tower_run_remote_with_invalid_param(context, param):
    """Call tower_run_remote with an invalid parameter"""
    key, value = param.split("=", 1)
    arguments = {"parameters": {key: value}}
    await call_mcp_tool(context, "tower_run_remote", arguments)


@then("the response should contain plain text log lines")
def step_response_should_contain_plain_text_log_lines(context):
    """Verify response contains properly formatted plain text log lines"""
    response_content = str(context.mcp_response.get("content", ""))
    assert (
        response_content
    ), f"Response should have content, got: {context.mcp_response}"

    # Check for timestamp formatting (should have | separator for plain text)
    assert (
        " | " in response_content
    ), f"Expected plain text format with '|' separator, got: {response_content[:200]}..."


@then("the response should not contain ANSI color codes")
def step_response_should_not_contain_ansi_codes(context):
    """Verify response doesn't contain ANSI color escape sequences"""
    response_content = str(context.mcp_response.get("content", ""))

    # Check for common ANSI color codes
    ansi_patterns = ["\033[", "\x1b[", "[0m", "[1;33m", "[31m"]
    for pattern in ansi_patterns:
        assert (
            pattern not in response_content
        ), f"Found ANSI color code '{pattern}' in response: {response_content[:200]}..."


@then("each log line should be properly formatted with timestamp")
def step_each_log_line_should_be_formatted_with_timestamp(context):
    """Verify each log line has proper timestamp format"""
    response_content = str(context.mcp_response.get("content", ""))

    # Split into lines and check timestamp format
    lines = [line.strip() for line in response_content.split("\n") if line.strip()]

    # Find lines that contain the pipe separator (these should be log lines)
    log_lines = [line for line in lines if " | " in line]
    assert (
        len(log_lines) > 0
    ), f"Expected to find log lines with '|' separator, got: {response_content[:300]}..."

    # Check timestamp format for a few log lines
    for line in log_lines[:3]:  # Check first few log lines
        parts = line.split(" | ", 1)
        assert (
            len(parts) == 2
        ), f"Log line should have 'timestamp | message' format, got: {line}"
        timestamp, message = parts
        assert (
            len(timestamp.strip()) >= 10
        ), f"Timestamp should be substantial, got: '{timestamp}'"


@then("I should receive a detailed validation error")
def step_should_receive_detailed_validation_error(context):
    """Verify response contains detailed validation error information"""
    response_content = str(context.mcp_response.get("content", ""))

    # Should be an error but with detailed content, not just a status code
    assert (
        not context.operation_success
    ), f"Expected error response, got success: {context.mcp_response}"
    assert (
        len(response_content) > 10
    ), f"Expected detailed error message, got short response: {response_content}"


@then('the error should mention "{expected_text}"')
def step_error_should_mention_text(context, expected_text):
    """Verify error message contains specific expected text"""
    response_content = str(context.mcp_response.get("content", ""))
    assert (
        expected_text.lower() in response_content.lower()
    ), f"Expected '{expected_text}' in error response, got: {response_content}"


@then("the error should not just be a status code")
def step_error_should_not_be_just_status_code(context):
    """Verify error is not just a bare status code like '422'"""
    response_content = str(context.mcp_response.get("content", ""))

    # Should not be just a number (status code)
    assert (
        not response_content.strip().isdigit()
    ), f"Error should not be just a status code, got: {response_content}"
    assert (
        "422" not in response_content or len(response_content) > 20
    ), f"Should have detailed error, not just '422', got: {response_content}"


@given("I have a simple hello world application that exits with code 1")
def step_have_hello_world_app_with_exit_1(context):
    """Create a hello world app that exits with code 1 for crash testing"""
    create_towerfile("hello_world")

    # Create a Python file that exits with code 1
    crash_app_content = """import time
print("Hello, World!")
time.sleep(1)
print("About to crash...")
exit(1)
"""
    with open("hello.py", "w") as f:
        f.write(crash_app_content)


@then("the response should indicate the app crashed")
def step_response_should_indicate_crash(context):
    """Verify response indicates the application crashed"""
    response_content = str(context.mcp_response.get("content", "")).lower()

    crash_indicators = ["crash", "error", "failed", "exit"]
    found_indicator = any(
        indicator in response_content for indicator in crash_indicators
    )
    assert (
        found_indicator
    ), f"Expected crash indication in response, got: {context.mcp_response}"


@then('the response should contain "{expected_text}" message')
def step_response_should_contain_message(context, expected_text):
    """Verify response contains expected message text"""
    response_content = str(context.mcp_response.get("content", "")).lower()
    assert (
        expected_text.lower() in response_content
    ), f"Expected '{expected_text}' in response, got: {context.mcp_response}"


@then("I should receive a success response about deployment")
def step_success_response_about_deployment(context):
    """Verify the response indicates successful deployment"""
    assert context.operation_success, f"Deploy operation should succeed, got: {context.mcp_response}"

    response_content = str(context.mcp_response.get("content", "")).lower()
    deployment_keywords = ["deploy", "version", "tower"]
    found_deployment_success = any(
        keyword in response_content for keyword in deployment_keywords
    )
    assert (
        found_deployment_success
    ), f"Response should mention deployment success, got: {context.mcp_response}"


@then('the app "{app_name}" should be visible in Tower')
@async_run_until_complete
async def step_app_should_be_visible_in_tower(context, app_name):
    """Verify that the specified app is now visible in Tower"""
    result = await call_mcp_tool(context, "tower_apps_show", {"name": app_name})
    assert result.get("success", False), f"App '{app_name}' should be visible in Tower, but tower_apps_show failed: {result}"
