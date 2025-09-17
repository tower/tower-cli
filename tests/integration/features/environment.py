import os
import subprocess
import time
import tempfile
import socket
from pathlib import Path

def before_all(context):
    context.tower_url = os.environ.get("TOWER_API_URL")
    print(f"TOWER_API_URL: {context.tower_url}")

def before_scenario(context, scenario):
    # Create a temporary working directory for this scenario
    context.temp_dir = tempfile.mkdtemp(prefix="tower_test_")
    context.original_cwd = os.getcwd()
    os.chdir(context.temp_dir)

    # Start tower mcp-server synchronously
    tower_binary = _find_tower_binary()
    if not tower_binary:
        raise RuntimeError("Could not find tower binary. Run 'cargo build' first.")
    
    # Set up environment
    test_env = os.environ.copy()
    test_env["TOWER_RUN_TIMEOUT"] = "3"

    if context.tower_url:
        test_env["TOWER_URL"] = context.tower_url
        test_env["TOWER_JWT"] = "mock_jwt_token"
    
    # Find a free port for this test scenario
    mcp_port = _find_free_port()
    
    # Start the server process
    context.tower_process = subprocess.Popen(
        [tower_binary, "mcp-server", "--port", str(mcp_port)],
        env=test_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True
    )
    
    # Give server time to start
    time.sleep(2)
    
    # Check if process is still running
    if context.tower_process.poll() is not None:
        stderr_output = context.tower_process.stderr.read()
        if stderr_output:
            print(f"DEBUG: MCP server stderr: {stderr_output}")
        raise RuntimeError(f"MCP server exited with code {context.tower_process.returncode}")
    
    context.mcp_server_url = f"http://127.0.0.1:{mcp_port}"

def after_scenario(context, scenario):
    if hasattr(context, 'tower_process') and context.tower_process:
        try:
            context.tower_process.terminate()
            context.tower_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            context.tower_process.kill()
            context.tower_process.wait()

    # Clean up temp directory
    if hasattr(context, 'original_cwd'):
        os.chdir(context.original_cwd)
    if hasattr(context, 'temp_dir'):
        import shutil
        shutil.rmtree(context.temp_dir, ignore_errors=True)

def after_all(context):
    pass

def _find_free_port():
    """Find a free port for the MCP server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


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
