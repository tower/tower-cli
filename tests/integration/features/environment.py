import asyncio
import os
from mcp_client import MCPTestHelper

def before_all(context):
    context.mcp_helper = None
    context.tower_url = os.environ.get("TOWER_MOCK_API_URL")
    print(f"TOWER_MOCK_API_URL: {context.tower_url}")

def before_scenario(context, scenario):
    context.mcp_helper = MCPTestHelper(tower_url=context.tower_url)
    asyncio.run(context.mcp_helper.setup())
    context.mcp_client = context.mcp_helper.client

def after_scenario(context, scenario):
    if context.mcp_helper:
        asyncio.run(context.mcp_helper.teardown())

def after_all(context):
    pass
