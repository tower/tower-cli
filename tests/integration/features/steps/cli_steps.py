#!/usr/bin/env python3

import subprocess
import os
import tempfile
import shutil
from pathlib import Path
from behave import given, when, then


@step('I run "{command}" via CLI')
def step_run_cli_command(context, command):
    """Run a Tower CLI command and capture output"""
    cli_path = context.tower_binary

    # Run the CLI command in the current directory (where environment.py set up the temp dir)
    # The MCP steps have already created the necessary files in the current directory

    # Run the CLI command
    cmd_parts = command.split()
    full_command = [cli_path] + cmd_parts[1:]  # Skip 'tower' prefix

    try:
        # Force colored output by setting environment variables
        test_env = os.environ.copy()
        test_env["FORCE_COLOR"] = "1"  # Force colored output
        test_env["CLICOLOR_FORCE"] = "1"  # Force colored output
        test_env["TOWER_URL"] = context.tower_url  # Use mock API
        test_env["TOWER_JWT"] = "mock_jwt_token"

        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout
            env=test_env,
        )
        context.cli_output = result.stdout + result.stderr
        context.cli_return_code = result.returncode
    except subprocess.TimeoutExpired:
        context.cli_output = "Command timed out"
        context.cli_return_code = 124
    except Exception as e:
        print(f"DEBUG: Exception in CLI command: {type(e).__name__}: {e}")
        print(f"DEBUG: Command was: {full_command}")
        print(f"DEBUG: Working directory: {os.getcwd()}")
        raise


@step("timestamps should be yellow colored")
def step_timestamps_should_be_yellow(context):
    """Verify timestamps are colored yellow (ANSI code 33)"""
    output = context.cli_output
    # Yellow is ANSI code 33, bold yellow is 1;33
    assert (
        "\x1b[1;33m" in output or "\x1b[33m" in output
    ), f"Expected yellow color codes in output, got: {output[:300]}..."


@step("timestamps should be green colored")
def step_timestamps_should_be_green(context):
    """Verify timestamps are colored green (ANSI code 32)"""
    output = context.cli_output
    # Green is ANSI code 32, bold green is 1;32
    assert (
        "\x1b[1;32m" in output or "\x1b[32m" in output
    ), f"Expected green color codes in output, got: {output[:300]}..."


@step("each log line should be on a separate line")
def step_log_lines_should_be_separate(context):
    """Verify log lines are properly separated with newlines"""
    output = context.cli_output
    lines = output.split("\n")

    # Should have multiple lines
    assert len(lines) > 3, f"Expected multiple lines of output, got: {len(lines)} lines"

    # Lines with timestamps should not be concatenated
    timestamp_lines = [
        line
        for line in lines
        if "2025-" in line and ("Hello" in line or "Creating" in line)
    ]
    assert (
        len(timestamp_lines) > 1
    ), f"Expected multiple timestamped lines, got: {timestamp_lines}"


red_color_code = "\x1b[31m"


@step('the final crash status should show red "Error:"')
def step_final_crash_status_should_show_error(context):
    """Verify crash status shows red 'Error:' message"""
    output = context.cli_output
    # Red is ANSI code 31
    assert (
        red_color_code in output
    ), f"Expected red color codes in output, got: {output}"
    assert "Error:" in output, f"Expected 'Error:' in crash message, got: {output}"


@step('the final status should show "Your app crashed!" in red')
def step_final_status_should_show_crashed_in_red(context):
    """Verify local run shows 'Your app crashed!' in red"""
    output = context.cli_output
    assert (
        red_color_code in output
    ), f"Expected red color codes in output, got: {output}"
    assert (
        "Your app crashed!" in output
    ), f"Expected 'Your app crashed!' message, got: {output}"


@step('the output should show "{expected_text}"')
def step_output_should_show_text(context, expected_text):
    """Verify output contains expected text"""
    output = context.cli_output
    assert (
        expected_text in output
    ), f"Expected '{expected_text}' in output, got: {output}"


@step('the output should not just show "{forbidden_text}"')
def step_output_should_not_just_show_text(context, forbidden_text):
    """Verify output is not just the forbidden text (e.g., not just '422')"""
    output = context.cli_output.strip()
    assert (
        output != forbidden_text
    ), f"Output should not be just '{forbidden_text}', got: {output}"
    if forbidden_text in output:
        assert (
            len(output) > len(forbidden_text) + 10
        ), f"Output should have more than just '{forbidden_text}', got: {output}"


@step('the output should show "{spinner_text}" spinner')
def step_output_should_show_spinner(context, spinner_text):
    """Verify spinner text appears in output"""
    output = context.cli_output
    assert (
        spinner_text in output
    ), f"Expected spinner text '{spinner_text}' in output, got: {output[:500]}..."


@step("both spinners should complete successfully")
def step_both_spinners_should_complete(context):
    """Verify spinners show completion"""
    output = context.cli_output
    # Look for spinner completion indicators (✔ or "Done!")
    completion_indicators = ["✔", "Done!", "success"]
    found_completion = any(indicator in output for indicator in completion_indicators)
    assert (
        found_completion
    ), f"Expected spinner completion indicators in output, got: {output[:500]}..."
