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
    # Catalog scenarios hit the real attach -> Iceberg -> query path, which the
    # mock server can't stand up. Skip them unless a storage catalog is
    # configured (and rely on a real TOWER_URL + session being provided too).
    if "catalogs" in scenario.effective_tags:
        catalog = os.environ.get("TOWER_TEST_CATALOG")
        if not catalog:
            scenario.skip(
                "set TOWER_TEST_CATALOG (and a real TOWER_URL) to run catalog tests"
            )
            return
        context.test_catalog = catalog
        context.test_catalog_env = os.environ.get("TOWER_TEST_CATALOG_ENV", "default")
        context.test_catalog_table = os.environ.get("TOWER_TEST_CATALOG_TABLE")
        if "catalog-data" in scenario.effective_tags and not context.test_catalog_table:
            scenario.skip(
                "set TOWER_TEST_CATALOG_TABLE to run the catalog data query test"
            )
            return

    # Create a temporary working directory for this scenario
    context.temp_dir = tempfile.mkdtemp(prefix="tower_test_")
    context.original_cwd = os.getcwd()
    context.api_key = os.environ.get("TOWER_TEST_API_KEY", "sk-test-api-key")
    os.chdir(context.temp_dir)


def after_scenario(context, scenario):
    import shutil

    # Delete any apps created by the scenario via "I have created N apps via CLI".
    if getattr(context, "created_app_names", None):
        env = os.environ.copy()
        env["TOWER_URL"] = context.tower_url
        test_home = Path(__file__).parent.parent / "test-home"
        env["HOME"] = str(test_home.absolute())
        for name in context.created_app_names:
            try:
                subprocess.run(
                    [context.tower_binary, "apps", "delete", name],
                    env=env,
                    capture_output=True,
                    timeout=30,
                )
            except subprocess.TimeoutExpired:
                pass
        context.created_app_names = []

    # Clean up any MCP servers started by this scenario
    for attr in ["http_mcp_process", "sse_mcp_process"]:
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
    if binary := os.environ.get("TOWER_CLI_BINARY"):
        if Path(binary).exists():
            return binary

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

    # Fall back to tower on PATH (e.g. installed via maturin develop or pip)
    result = subprocess.run(["which", "tower"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()

    return None
