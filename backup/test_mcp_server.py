#!/usr/bin/env python3
"""
Minimal MCP server test to isolate connection issues
"""

import asyncio
import logging
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server
server = Server("test-mcp-server")

@server.list_tools()
async def list_tools():
    """List available tools"""
    return [
        Tool(
            name="test_tool",
            description="A simple test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Test message"
                    }
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    if name == "test_tool":
        message = arguments.get("message", "No message provided")
        return [TextContent(type="text", text=f"Test response: {message}")]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Run the server"""
    try:
        logger.info("Starting test MCP server...")
        async with stdio_server(server) as (read_stream, write_stream):
            logger.info("Test MCP server started successfully")
            await server.run(read_stream, write_stream, server.create_initialization_options())
    except Exception as e:
        logger.error(f"Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())