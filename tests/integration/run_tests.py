#!/usr/bin/env python3
"""
Simple test runner for Tower MCP integration tests.
Assumes dependencies are already installed via nix devShell.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the integration tests."""
    
    # Check if tower binary exists
    project_root = Path(__file__).parent.parent.parent
    debug_binary = project_root / "target" / "debug" / "tower"
    release_binary = project_root / "target" / "release" / "tower"
    
    if not debug_binary.exists() and not release_binary.exists():
        print("ERROR: Tower binary not found. Please run 'cargo build' first.")
        print(f"Looked for: {debug_binary} or {release_binary}")
        return 1
    
    binary_path = debug_binary if debug_binary.exists() else release_binary
    print(f"Using tower binary: {binary_path}")
    
    # Check if behave is available
    try:
        subprocess.check_output(["behave", "--version"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: behave not found. Please run 'nix develop' to enter the dev environment.")
        return 1
    
    # Run behave tests
    test_dir = Path(__file__).parent / "features"
    cmd = ["behave", str(test_dir), "-v"]
    
    print(f"Running integration tests...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)