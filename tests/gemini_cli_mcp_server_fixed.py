#!/usr/bin/env python3
"""
Fixed Slim Gemini CLI MCP Server - Token-efficient integration
"""

import asyncio
import subprocess
import logging
import shlex
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("slim-gemini-cli-mcp")

# Configuration
MAX_FILE_SIZE = 81920  # 80KB
MAX_LINES = 800
RESPONSE_WORD_LIMIT = 800
TIMEOUT = 90

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="gemini_quick_query",
            description="Ask Gemini CLI any development question for quick answers",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question to ask Gemini CLI"
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional context to provide with the query"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="gemini_analyze_code",
            description="Analyze specific code sections with focused insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "code_content": {
                        "type": "string",
                        "description": "Code content to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["comprehensive", "security", "performance", "architecture"],
                        "default": "comprehensive",
                        "description": "Type of analysis to perform"
                    },
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific areas to focus analysis on"
                    }
                },
                "required": ["code_content"]
            }
        ),
        Tool(
            name="gemini_codebase_analysis",
            description="Analyze entire directories using Gemini CLI's 1M token context",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to directory to analyze"
                    },
                    "file_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["*.py", "*.js", "*.ts", "*.vue"],
                        "description": "File patterns to include"
                    },
                    "analysis_scope": {
                        "type": "string",
                        "enum": ["structure", "security", "performance", "patterns", "all"],
                        "default": "all",
                        "description": "Scope of analysis"
                    }
                },
                "required": ["directory_path"]
            }
        )
    ]

async def execute_gemini_cli(prompt: str, timeout: int = TIMEOUT) -> Dict[str, Any]:
    """Execute Gemini CLI with error handling"""
    try:
        escaped_prompt = shlex.quote(prompt)
        cmd = f"gemini -p {escaped_prompt}"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy()
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        stdout_str = stdout.decode('utf-8', errors='replace')
        stderr_str = stderr.decode('utf-8', errors='replace')
        
        if process.returncode == 0:
            return {"success": True, "output": stdout_str}
        else:
            return {"success": False, "error": stderr_str}
            
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Timeout after {timeout} seconds"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "gemini_quick_query":
            query = arguments["query"]
            context = arguments.get("context", "")
            
            prompt = f"Context: {context}\n\nQuestion: {query}\n\nProvide a concise answer." if context else f"Question: {query}\n\nProvide a concise answer."
            
            result = await execute_gemini_cli(prompt)
            
            if result["success"]:
                return [TextContent(type="text", text=f"**Query:** {query}\n\n{result['output']}")]
            else:
                return [TextContent(type="text", text=f"Query failed: {result['error']}")]
        
        elif name == "gemini_analyze_code":
            code_content = arguments["code_content"]
            analysis_type = arguments.get("analysis_type", "comprehensive")
            focus_areas = arguments.get("focus_areas", [])
            
            if len(code_content) > MAX_FILE_SIZE:
                return [TextContent(type="text", text=f"⚠️ Code too large ({len(code_content)} bytes). Max: {MAX_FILE_SIZE} bytes")]
            
            line_count = len(code_content.splitlines())
            if line_count > MAX_LINES:
                return [TextContent(type="text", text=f"⚠️ Too many lines ({line_count}). Max: {MAX_LINES} lines")]
            
            prompt = f"Analyze this code ({analysis_type} analysis, under {RESPONSE_WORD_LIMIT} words):\n\n{code_content}\n\nProvide focused insights."
            if focus_areas:
                prompt += f"\n\nFocus on: {', '.join(focus_areas)}"
            
            result = await execute_gemini_cli(prompt)
            
            if result["success"]:
                return [TextContent(type="text", text=f"# Code Analysis\n\n**Type:** {analysis_type}\n**Lines:** {line_count}\n\n{result['output']}")]
            else:
                return [TextContent(type="text", text=f"Analysis failed: {result['error']}")]
        
        elif name == "gemini_codebase_analysis":
            directory_path = arguments["directory_path"]
            file_patterns = arguments.get("file_patterns", ["*.py", "*.js", "*.ts", "*.vue"])
            analysis_scope = arguments.get("analysis_scope", "all")
            
            if not Path(directory_path).exists():
                return [TextContent(type="text", text=f"❌ Directory not found: {directory_path}")]
            
            prompt = f"@{directory_path} Analyze this codebase (scope: {analysis_scope}):\n\nFile patterns: {', '.join(file_patterns)}\n\nProvide analysis under {RESPONSE_WORD_LIMIT} words."
            
            result = await execute_gemini_cli(prompt, timeout=120)
            
            if result["success"]:
                return [TextContent(type="text", text=f"# Codebase Analysis\n\n**Directory:** {directory_path}\n**Scope:** {analysis_scope}\n\n{result['output']}")]
            else:
                return [TextContent(type="text", text=f"Analysis failed: {result['error']}")]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the server"""
    try:
        logger.info("Starting Slim Gemini CLI MCP Server...")
        async with stdio_server(server) as (read_stream, write_stream):
            logger.info("Server started successfully")
            await server.run(read_stream, write_stream)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())