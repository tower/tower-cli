import os
import sys
import platform


def test_environment_variables():
    """Test to show environment variable values during test execution."""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")
    print(f"Virtual environment: {os.getenv('VIRTUAL_ENV', 'Not in virtual env')}")
    print(f"PYENV_VERSION: {os.getenv('PYENV_VERSION', 'Not set')}")
    print("-" * 50)
    
    # Check if environment variables from pytest.ini are available
    router_key = os.getenv("TOWER_INFERENCE_ROUTER_API_KEY")
    
    # Check if pytest-env is working
    if router_key is not None:
        assert router_key.startswith("hf_"), f"Expected router key to start with 'hf_', got {router_key}"
