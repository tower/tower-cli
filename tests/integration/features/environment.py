#!/usr/bin/env python3
"""
Environment setup for behave integration tests.
"""

import asyncio


def before_all(context):
    """Set up the test environment before all tests."""
    # Create a simple event loop for async operations
    context.loop = asyncio.new_event_loop()


def after_scenario(context, scenario):
    """Clean up after each scenario."""
    if hasattr(context, 'mcp_helper') and context.mcp_helper:
        # Clean up the MCP helper
        try:
            # Run cleanup in the event loop
            if hasattr(context, 'loop') and context.loop and not context.loop.is_closed():
                context.loop.run_until_complete(context.mcp_helper.teardown())
            else:
                # Fallback: create new loop for cleanup
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(context.mcp_helper.teardown())
                finally:
                    loop.close()
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")


def after_all(context):
    """Clean up after all tests."""
    if hasattr(context, 'loop') and context.loop and not context.loop.is_closed():
        context.loop.close()