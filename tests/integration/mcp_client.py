#!/usr/bin/env python3
"""
Real MCP client for integration testing Tower CLI MCP server.
"""

import asyncio
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
import os


class MCPClient:
    """A simple MCP client that talks to the Tower CLI MCP server over stdio."""
    
    def __init__(self, tower_binary_path: str):
        self.tower_binary_path = tower_binary_path
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        
    async def start_server(self) -> None:
        """Start the Tower MCP server as a subprocess."""
        cmd = [self.tower_binary_path, "mcp-server"]
        
        # Set environment variables for testing
        test_env = os.environ.copy()
        test_env["TOWER_RUN_TIMEOUT"] = "1"  # 1 second timeout - but there might be an async issue
        
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            env=test_env
        )
        
        # Wait a moment for server to start
        await asyncio.sleep(0.1)
        
        # Initialize the connection
        await self._send_initialize()
        
    async def stop_server(self) -> None:
        """Stop the MCP server."""
        if self.process:
            # First try gentle termination
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                self.process.kill()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass  # Process is really stuck, just move on
            self.process = None
            
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        if not self.process:
            raise RuntimeError("Server not started")
            
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        # Client timeout should only catch bugs/hangs, not interfere with tests
        try:
            response_line = await asyncio.wait_for(
                self._read_line(),
                timeout=30.0  # High timeout - only catches real hangs, not test interference
            )
            return json.loads(response_line)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request {method} timed out after 30 seconds - likely a bug")
            
    async def _read_line(self) -> str:
        """Read a line from the server stdout."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process.stdout.readline)
        
    async def _send_initialize(self) -> None:
        """Send the MCP initialize request."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "tower-test-client",
                "version": "1.0.0"
            }
        }
        
        response = await self._send_request("initialize", params)
        if "error" in response:
            raise RuntimeError(f"Failed to initialize: {response['error']}")
            
        # Send initialized notification
        await self._send_notification("notifications/initialized")
        
    async def _send_notification(self, method: str, params: Dict[str, Any] = None) -> None:
        """Send a JSON-RPC notification."""
        if not self.process:
            raise RuntimeError("Server not started")
            
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        notification_json = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_json)
        self.process.stdin.flush()
        
    def is_server_alive(self) -> bool:
        """Check if the server process is still running."""
        return self.process is not None and self.process.poll() is None
        
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self.is_server_alive():
            return {"success": False, "error": "MCP server is not running"}
            
        params = {
            "name": tool_name,
            "arguments": arguments or {}
        }
        
        try:
            response = await self._send_request("tools/call", params)
            
            if "error" in response:
                return {"success": False, "error": response["error"]}
                
            result = response.get("result", {})
            return {
                "success": not result.get("isError", False),
                "content": result.get("content", []),
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": f"Communication error: {str(e)}"}


class MCPTestHelper:
    """Helper class for MCP integration tests."""
    
    def __init__(self):
        self.client: Optional[MCPClient] = None
        self.temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self.original_cwd: Optional[str] = None
        
    async def setup(self) -> None:
        """Set up the test environment."""
        # Find the tower binary
        tower_binary = self._find_tower_binary()
        if not tower_binary:
            raise RuntimeError("Could not find tower binary. Run 'cargo build' first.")
            
        # Create temporary directory and change to it
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        # Start MCP client
        self.client = MCPClient(tower_binary)
        await self.client.start_server()
        
    async def teardown(self) -> None:
        """Clean up the test environment."""
        if self.client:
            await self.client.stop_server()
            
        if self.original_cwd:
            os.chdir(self.original_cwd)
            
        if self.temp_dir:
            self.temp_dir.cleanup()
            
    def _find_tower_binary(self) -> Optional[str]:
        """Find the tower binary in the target directory."""
        # Look for debug build first
        debug_path = Path(__file__).parent.parent.parent / "target" / "debug" / "tower"
        if debug_path.exists():
            return str(debug_path)
            
        # Look for release build
        release_path = Path(__file__).parent.parent.parent / "target" / "release" / "tower"
        if release_path.exists():
            return str(release_path)
            
        return None
        
    def create_towerfile(self, app_type: str = "hello_world") -> None:
        """Create a test Towerfile in the current directory."""
        towerfiles = {
            "hello_world": '''
[app]
name = "hello-world"
script = "./hello.py"
description = "Simple hello world app"
source = ["./hello.py"]

[build]
python = "3.11"
''',
            "long_running": '''
[app]
name = "long-runner"
script = "./long_runner.py"
description = "Long running app for timeout testing"
source = ["./long_runner.py"]

[build]
python = "3.11"
''',
            "invalid": '''
[app]
name = 
script = "./missing.py"
description = "Invalid Towerfile"
'''
        }
        
        scripts = {
            "hello_world": 'print("Hello, World!")',
            "long_running": '''
import time
print("Starting guaranteed-slow script (will timeout)...")
time.sleep(10)  # Sleep way longer than 1s timeout - guaranteed to timeout
print("This should never print")
''',
            "invalid": 'print("This script exists but Towerfile is invalid")'
        }
        
        # Write Towerfile
        with open("Towerfile", "w") as f:
            f.write(towerfiles.get(app_type, towerfiles["hello_world"]))
            
        # Write script
        script_content = scripts.get(app_type, scripts["hello_world"])
        script_name = "hello.py" if app_type == "hello_world" else "long_runner.py"
        with open(script_name, "w") as f:
            f.write(script_content)


# Test the client directly
async def main():
    """Simple test of the MCP client."""
    helper = MCPTestHelper()
    
    try:
        await helper.setup()
        print("✓ MCP server started successfully")
        
        # Test tower_apps_list
        result = await helper.client.call_tool("tower_apps_list")
        print(f"tower_apps_list result: {result}")
        
        # Test tower_file_validate (should fail since no Towerfile)
        result = await helper.client.call_tool("tower_file_validate")
        print(f"tower_file_validate result: {result}")
        
        # Create a Towerfile and test again
        helper.create_towerfile()
        result = await helper.client.call_tool("tower_file_validate")
        print(f"tower_file_validate with Towerfile: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    finally:
        await helper.teardown()
        
    print("✓ All tests completed")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)