#!/usr/bin/env -S uv run python
"""
Simple test runner for Tower MCP integration tests.
Assumes dependencies are already installed via nix devShell.

Supports two modes:
1. Mock mode (default): Starts local mock server at http://127.0.0.1:8000
2. Real server mode: Set TOWER_URL env var to use external server
   - Skips mock server startup
   - Preserves externally configured session.json
"""

import os
import subprocess
import sys
import time
import socket
import requests
from pathlib import Path


def log(msg):
    """Print with test runner prefix and basic formatting."""
    print(f"\033[36m[test-runner]\033[0m {msg}")


def is_session_externally_configured(test_home):
    """Check if session.json has been externally configured.

    Returns True if session.json is newer than the git HEAD version,
    indicating it was set up by external orchestration (e.g., from monorepo).
    """
    session_file = test_home / ".config" / "tower" / "session.json"
    if not session_file.exists():
        return False

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", str(session_file)],
            capture_output=True,
            text=True,
            check=True,
        )
        git_mtime = int(result.stdout.strip())
        file_mtime = int(session_file.stat().st_mtime)
        return file_mtime > git_mtime
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return False


def reset_session_fixture(test_home):
    """Reset the session.json fixture to its committed state before tests.

    The CLI may modify session.json during MCP operations (like team switching),
    so we restore it to the canonical committed version before each test run.
    Skips reset if session appears to be externally configured.
    """
    if is_session_externally_configured(test_home):
        log("Skipping session.json reset (externally configured)")
        return

    session_file = test_home / ".config" / "tower" / "session.json"
    subprocess.run(
        ["git", "checkout", str(session_file)],
        capture_output=True,
    )


def check_mock_server_health(url):
    """Check if the mock server is running and responding."""
    try:
        response = requests.get(f"{url}/", timeout=5)
        return response.status_code == 200 and "Tower Mock API" in response.json().get(
            "message", ""
        )
    except requests.RequestException:
        return False


def start_mock_server():
    """Start the mock API server and wait for it to be healthy."""
    mock_server_dir = Path(__file__).parent.parent / "mock-api-server"
    if not mock_server_dir.exists():
        raise RuntimeError(f"Mock server directory not found: {mock_server_dir}")

    log("Starting mock API server...")
    process = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=mock_server_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(30):
        if check_mock_server_health("http://127.0.0.1:8000"):
            log("Mock API server started successfully")
            return process
        time.sleep(1)

    process.terminate()
    raise RuntimeError("Mock server failed to start within 30 seconds")


def main():
    """Run the integration tests."""
    # Check prerequisites - look for tower binary from env, cargo build, or PATH
    has_env_binary = bool(os.environ.get("TOWER_CLI_BINARY") and Path(os.environ["TOWER_CLI_BINARY"]).exists())
    project_root = Path(__file__).parent.parent.parent
    has_cargo_binary = any(
        (project_root / "target" / build / "tower").exists()
        for build in ["debug", "release"]
    )
    has_path_binary = (
        subprocess.run(["which", "tower"], capture_output=True).returncode == 0
        if not has_cargo_binary
        else False
    )

    if not has_env_binary and not has_cargo_binary and not has_path_binary:
        log(
            "ERROR: Tower binary not found. Please run 'cargo build' or 'maturin develop' first."
        )
        return 1

    try:
        subprocess.check_output(["behave", "--version"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        log(
            "ERROR: behave not found. Please run 'nix develop' to enter the dev environment."
        )
        return 1

    # Set up environment
    env = os.environ.copy()

    # Set HOME to test-home directory to isolate session from user's real config
    test_home = Path(__file__).parent / "test-home"
    env["HOME"] = str(test_home.absolute())

    # Determine if we're using external configuration or mock server
    tower_url_preset = "TOWER_URL" in os.environ
    if tower_url_preset:
        server_url = env["TOWER_URL"]
        mock_process = None
        log(f"Using externally configured API URL: \033[1m{server_url}\033[0m")
    else:
        server_url = "http://127.0.0.1:8000"
        env["TOWER_URL"] = server_url
        log(f"Using mock server API URL: \033[1m{server_url}\033[0m")

        # Ensure mock server is running
        mock_process = None
        if not check_mock_server_health(server_url):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            port_in_use = sock.connect_ex(("127.0.0.1", 8000)) == 0
            sock.close()

            if port_in_use:
                log(
                    "ERROR: Port 8000 is in use but not responding to health check (some unrelated server?)."
                )
                return 1

            mock_process = start_mock_server()
        else:
            log("Mock server already running and healthy")

    log(f"Using test HOME: \033[1m{env['HOME']}\033[0m")

    # Actually run tests
    try:
        test_dir = Path(__file__).parent / "features"

        args = sys.argv[1:]

        # Enable parallel execution by default unless single test is specified
        single_test_mode = any(arg.startswith("-n") or arg in ["-n"] for arg in args)

        # defaulting to 2 workers if user doesn't override
        if not single_test_mode and "--jobs" not in " ".join(args) and "-j" not in args:
            args = ["--jobs", "2"] + args
            log("Running tests in parallel (2 workers)")
        elif single_test_mode:
            log("Running single test (no parallelization)")
        else:
            log("Running integration tests...")

        result = subprocess.run(
            ["behave", str(test_dir)] + args, cwd=Path(__file__).parent, env=env
        )
        return result.returncode

    except KeyboardInterrupt:
        log("Tests interrupted by user")
        return 1

    finally:
        reset_session_fixture(test_home)

        if mock_process:
            log("Stopping mock server...")
            mock_process.terminate()
            try:
                mock_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                mock_process.kill()
                mock_process.wait()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
