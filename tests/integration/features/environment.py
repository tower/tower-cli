import os
import subprocess
import time
import tempfile
import socket
import threading
import queue
from pathlib import Path


def before_all(context):
    context.tower_url = os.environ.get("TOWER_URL", "http://127.0.0.1:8000")
    print(f"TOWER_URL: {context.tower_url}")

    tower_binary = _find_tower_binary()
    if not tower_binary:
        raise RuntimeError("Could not find tower binary. Run 'cargo build' first.")

    context.tower_binary = tower_binary

    test_env = os.environ.copy()
    test_env["TOWER_RUN_TIMEOUT"] = "3"
    if context.tower_url:
        test_env["TOWER_URL"] = context.tower_url
        test_env["TOWER_JWT"] = "mock_jwt_token"

    # Start MCP server (maybe should somehow be limited to mcp features in the future?)
    mcp_port = _find_free_port()
    context.tower_mcpserver_process = subprocess.Popen(
        [tower_binary, "mcp-server", "--transport", "sse", "--port", str(mcp_port)],
        env=test_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Set up continuous log capture to avoid accumulation
    context.mcp_stdout_queue = queue.Queue()
    context.mcp_stderr_queue = queue.Queue()

    def drain_mcp_stream(stream, output_queue, stream_name):
        try:
            for line in iter(stream.readline, ""):
                output_queue.put(
                    f"[MCP-{stream_name}] [{time.strftime('%H:%M:%S')}] {line.rstrip()}"
                )
        except:
            pass

    context.stdout_thread = threading.Thread(
        target=drain_mcp_stream,
        args=(
            context.tower_mcpserver_process.stdout,
            context.mcp_stdout_queue,
            "STDOUT",
        ),
        daemon=True,
    )
    context.stderr_thread = threading.Thread(
        target=drain_mcp_stream,
        args=(
            context.tower_mcpserver_process.stderr,
            context.mcp_stderr_queue,
            "STDERR",
        ),
        daemon=True,
    )
    context.stdout_thread.start()
    context.stderr_thread.start()

    # Give server time to start
    time.sleep(2)

    # Check if process is still running
    if context.tower_mcpserver_process.poll() is not None:
        # Collect any startup errors
        startup_errors = []
        while not context.mcp_stderr_queue.empty():
            startup_errors.append(context.mcp_stderr_queue.get_nowait())
        if startup_errors:
            print(
                f"DEBUG: Shared MCP server startup errors:\n{chr(10).join(startup_errors)}"
            )
        raise RuntimeError(
            f"Shared MCP server exited with code {context.tower_mcpserver_process.returncode}"
        )

    context.mcp_server_url = f"http://127.0.0.1:{mcp_port}"


def before_scenario(context, scenario):
    # Create a temporary working directory for this scenario
    context.temp_dir = tempfile.mkdtemp(prefix="tower_test_")
    context.original_cwd = os.getcwd()
    os.chdir(context.temp_dir)


def _flush_queue(q):
    """Flush all items from a queue and return as list."""
    items = []
    while True:
        try:
            items.append(q.get_nowait())
        except queue.Empty:
            break
    return items


def after_scenario(context, scenario):
    # Show MCP output for failed tests by flushing the queues
    if hasattr(context, "mcp_stderr_queue") and hasattr(context, "mcp_stdout_queue"):
        if scenario.status.name in ["failed", "error"] or os.environ.get(
            "DEBUG_MCP_SERVER"
        ):
            stdout_lines = _flush_queue(context.mcp_stdout_queue)
            stderr_lines = _flush_queue(context.mcp_stderr_queue)

            if stdout_lines or stderr_lines:
                print(f"\n=== MCP Server Output ===")
                for line in stdout_lines + stderr_lines:
                    print(line)

    # Clean up temp directory
    if hasattr(context, "original_cwd"):
        os.chdir(context.original_cwd)
    if hasattr(context, "temp_dir"):
        import shutil

        shutil.rmtree(context.temp_dir, ignore_errors=True)


def after_all(context):
    # Clean up shared MCP server
    if hasattr(context, "tower_mcpserver_process") and context.tower_mcpserver_process:
        try:
            context.tower_mcpserver_process.terminate()
            context.tower_mcpserver_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            context.tower_mcpserver_process.kill()
            context.tower_mcpserver_process.wait()


def _find_free_port():
    """Find a free port for the MCP server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def _find_tower_binary():
    # Look for debug build first
    debug_path = (
        Path(__file__).parent.parent.parent.parent / "target" / "debug" / "tower"
    )
    if debug_path.exists():
        return str(debug_path)

    # Look for release build
    release_path = (
        Path(__file__).parent.parent.parent.parent / "target" / "release" / "tower"
    )
    if release_path.exists():
        return str(release_path)

    return None
