import os
import subprocess
import tempfile
from pathlib import Path


def before_all(context):
    context.tower_url = os.environ.get("TOWER_URL", "http://127.0.0.1:8000")
    print(f"TOWER_URL: {context.tower_url}")

    tower_binary = _find_tower_binary()
    if not tower_binary:
        raise RuntimeError("Could not find tower binary. Run 'cargo build' first.")

    context.tower_binary = tower_binary


def before_scenario(context, scenario):
    # Create a temporary working directory for this scenario
    context.temp_dir = tempfile.mkdtemp(prefix="tower_test_")
    context.original_cwd = os.getcwd()
    os.chdir(context.temp_dir)




def after_scenario(context, scenario):
    import shutil

    # Clean up any MCP servers started by this scenario
    for attr in ['http_mcp_process', 'sse_mcp_process']:
        if hasattr(context, attr):
            process = getattr(context, attr)
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    # Clean up temp directory
    if hasattr(context, "original_cwd"):
        os.chdir(context.original_cwd)
    if hasattr(context, "temp_dir"):
        shutil.rmtree(context.temp_dir, ignore_errors=True)




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
