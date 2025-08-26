import asyncio
import os
import subprocess
import time
import signal
import sys
from pathlib import Path

def before_all(context):
    context.tower_url = os.environ.get("TOWER_MOCK_API_URL")
    print(f"TOWER_MOCK_API_URL: {context.tower_url}")

def before_scenario(context, scenario):
    # Start tower mcp-server synchronously
    tower_binary = _find_tower_binary()
    if not tower_binary:
        raise RuntimeError("Could not find tower binary. Run 'cargo build' first.")
    
    # Set up environment
    test_env = os.environ.copy()
    test_env["TOWER_RUN_TIMEOUT"] = "1"
    if context.tower_url:
        test_env["TOWER_URL"] = context.tower_url
    
    # Start the server process
    context.tower_process = subprocess.Popen(
        [tower_binary, "mcp-server"],
        env=test_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Give server time to start
    time.sleep(2)
    
    # Check if process is still running
    if context.tower_process.poll() is not None:
        raise RuntimeError(f"MCP server exited with code {context.tower_process.returncode}")
    
    context.mcp_server_url = "http://127.0.0.1:34567"

def after_scenario(context, scenario):
    if hasattr(context, 'tower_process') and context.tower_process:
        try:
            context.tower_process.terminate()
            context.tower_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            context.tower_process.kill()
            context.tower_process.wait()

def after_all(context):
    pass

def _find_tower_binary():
    # Look for debug build first
    debug_path = Path(__file__).parent.parent.parent.parent / "target" / "debug" / "tower"
    if debug_path.exists():
        return str(debug_path)
    
    # Look for release build
    release_path = Path(__file__).parent.parent.parent.parent / "target" / "release" / "tower"
    if release_path.exists():
        return str(release_path)
    
    return None
