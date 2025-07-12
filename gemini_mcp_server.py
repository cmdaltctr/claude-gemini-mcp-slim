#!/usr/bin/env python3
"""
Slim Gemini CLI MCP Server
"""

import asyncio
import subprocess
import logging
import shlex
import os
import sys
from typing import Dict, Any, Optional, List
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

# Security functions
def sanitize_for_prompt(text: str, max_length: int = 100000) -> str:
    """Sanitize text input to prevent prompt injection attacks"""
    if not isinstance(text, str):
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove/escape potential prompt injection patterns
    dangerous_patterns = [
        "ignore all previous instructions",
        "forget everything above", 
        "new instruction:",
        "system:",
        "assistant:",
        "user:",
        "###",
        "---",
        "```",
        "<|",
        "|>",
        "[INST]",
        "[/INST]"
    ]
    
    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in text_lower:
            # Replace with safe alternative (case-insensitive)
            import re
            # Create case-insensitive regex pattern
            escaped_pattern = re.escape(pattern)
            replacement = f"[filtered:{pattern[:10]}]"
            text = re.sub(escaped_pattern, replacement, text, flags=re.IGNORECASE)
    
    # Escape potential control characters
    text = text.replace('\x00', '').replace('\x1b', '')
    
    return text

def validate_path_security(file_path: str) -> tuple[bool, str, Path]:
    """Validate path for security - prevent path traversal attacks"""
    try:
        if not isinstance(file_path, str) or not file_path.strip():
            return False, "Invalid path", None
            
        resolved_path = Path(file_path).resolve()
        current_dir = Path.cwd().resolve()
        
        # Check if the resolved path is within current directory tree
        try:
            resolved_path.relative_to(current_dir)
        except ValueError:
            return False, "Path outside allowed directory", None
        
        return True, "Valid path", resolved_path
    except Exception as e:
        return False, f"Path validation error: {str(e)}", None

# Model configuration with fallback to CLI
GEMINI_MODELS = {
    "flash": os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash"),
    "pro": os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")
}

# API key for direct API usage
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model assignment for tasks
MODEL_ASSIGNMENTS = {
    "gemini_quick_query": "flash",      # Simple Q&A
    "gemini_analyze_code": "pro",       # Deep analysis
    "gemini_codebase_analysis": "pro",  # Large context
    "pre_edit": "flash",                # Quick context
    "pre_commit": "pro",                # Thorough review
    "session_summary": "flash"          # Lightweight overview
}

async def execute_gemini_api(prompt: str, model_name: str) -> Dict[str, Any]:
    """Execute Gemini API directly with specified model"""
    try:
        # Validate API key securely
        if not GOOGLE_API_KEY or not isinstance(GOOGLE_API_KEY, str) or len(GOOGLE_API_KEY.strip()) < 10:
            return {"success": False, "error": "Invalid or missing API key"}
        
        import google.generativeai as genai
        
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(model_name)
        
        logger.info(f"Making API call to {model_name}")
        response = await model.generate_content_async(prompt)
        
        return {"success": True, "output": response.text}
        
    except ImportError:
        logger.warning("google-generativeai not installed, using CLI fallback")
        return {"success": False, "error": "API library not available"}
    except Exception as e:
        # Sanitize error message to prevent sensitive information leakage
        error_message = str(e)
        import re
        error_message = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[API_KEY_REDACTED]', error_message)
        error_message = re.sub(r'sk-[A-Za-z0-9_-]{32,}', '[API_KEY_REDACTED]', error_message)
        error_message = re.sub(r'Bearer [A-Za-z0-9_.-]{10,}', '[TOKEN_REDACTED]', error_message)
        
        logger.error(f"API call failed: {error_message}")
        return {"success": False, "error": error_message}

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

async def execute_gemini_cli_streaming(prompt: str, task_type: str = "gemini_quick_query") -> Dict[str, Any]:
    """Execute Gemini CLI with model selection and API fallback"""
    logger.info("Starting Gemini CLI execution with streaming")
    logger.info(f"Prompt length: {len(prompt)} characters")
    logger.info(f"Task type: {task_type}")
    
    # Input validation
    if not isinstance(prompt, str) or len(prompt.strip()) == 0:
        return {"success": False, "error": "Invalid prompt: must be non-empty string"}
    
    if len(prompt) > 1000000:  # 1MB limit
        return {"success": False, "error": "Prompt too large (max 1MB)"}
    
    if task_type not in MODEL_ASSIGNMENTS:
        return {"success": False, "error": "Invalid task type"}
    
    # Select appropriate model
    model_type = MODEL_ASSIGNMENTS.get(task_type, "flash")
    model_name = GEMINI_MODELS[model_type]
    
    # Validate model name
    if not isinstance(model_name, str) or not model_name.strip():
        return {"success": False, "error": "Invalid model name"}
    if not all(c.isalnum() or c in '.-' for c in model_name):
        return {"success": False, "error": "Invalid model name characters"}
    
    logger.info(f"Selected model: {model_name} ({model_type})")
    
    try:
        # Try API first if key is available
        if GOOGLE_API_KEY:
            logger.info("Attempting direct API call")
            result = await execute_gemini_api(prompt, model_name)
            if result["success"]:
                return result
            logger.warning("API call failed, falling back to CLI")
        
        # Fallback to CLI - SECURE VERSION (no shell=True)
        cmd_args = ["gemini", "-m", model_name, "-p", prompt]
        logger.info(f"Executing command: gemini -m {model_name} -p [prompt length: {len(prompt)}]")
        
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"PATH": os.environ.get("PATH", "")}  # Minimal environment
        )
        logger.info(f"Process created with PID: {process.pid}")
        
        output_lines = []
        start_time = asyncio.get_event_loop().time()
        last_progress = start_time
        
        logger.info("Streaming Gemini CLI output...")
        
        # Stream output in real-time
        while True:
            try:
                # Read line with timeout to check for progress
                line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                if line:
                    decoded_line = line.decode('utf-8', errors='replace')
                    output_lines.append(decoded_line)
                    logger.info(f"Gemini output: {decoded_line.strip()[:100]}{'...' if len(decoded_line.strip()) > 100 else ''}")
                    last_progress = asyncio.get_event_loop().time()
                elif process.returncode is not None:
                    break
            except asyncio.TimeoutError:
                # Check if process is still running and show progress
                if process.returncode is None:
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_progress > 15:
                        elapsed = int(current_time - start_time)
                        logger.info(f"Analysis in progress... {elapsed}s elapsed")
                        last_progress = current_time
                else:
                    break
        
        # Get any remaining output
        remaining_stdout, stderr = await process.communicate()
        if remaining_stdout:
            decoded_remaining = remaining_stdout.decode('utf-8', errors='replace')
            output_lines.append(decoded_remaining)
            logger.info(f"Final output: {decoded_remaining.strip()[:100]}{'...' if len(decoded_remaining.strip()) > 100 else ''}")
        
        full_output = ''.join(output_lines)
        stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
        
        logger.info(f"Process completed with return code: {process.returncode}")
        logger.info(f"Total output length: {len(full_output)} chars")
        
        if process.returncode == 0:
            logger.info("Gemini CLI execution successful")
            return {"success": True, "output": full_output}
        else:
            logger.error(f"Gemini CLI failed with return code {process.returncode}: {stderr_str[:200]}...")
            return {"success": False, "error": stderr_str}
            
    except Exception as e:
        logger.error(f"Exception during Gemini CLI execution: {str(e)}")
        return {"success": False, "error": str(e)}

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    logger.info(f"Tool call received: {name} with arguments: {list(arguments.keys())}")
    logger.debug(f"Full arguments: {arguments}")
    try:
        if name == "gemini_quick_query":
            query = arguments.get("query", "")
            context = arguments.get("context", "")
            
            # Input validation and sanitization
            if not isinstance(query, str) or not query.strip():
                return [TextContent(type="text", text="Error: Query must be a non-empty string")]
            
            if not isinstance(context, str):
                return [TextContent(type="text", text="Error: Context must be a string")]
            
            # Sanitize inputs to prevent prompt injection
            sanitized_query = sanitize_for_prompt(query, max_length=10000)
            sanitized_context = sanitize_for_prompt(context, max_length=50000)
            
            prompt = f"Context: {sanitized_context}\n\nQuestion: {sanitized_query}\n\nProvide a concise answer in plain text format. Do not use markdown formatting. Break content into clear paragraphs when needed. Format your response like a helpful AI assistant would - clear, well-structured, and easy to read with proper line breaks between ideas." if sanitized_context else f"Question: {sanitized_query}\n\nProvide a concise answer in plain text format. Do not use markdown formatting. Break content into clear paragraphs when needed. Format your response like a helpful AI assistant would - clear, well-structured, and easy to read with proper line breaks between ideas."
            
            result = await execute_gemini_cli_streaming(prompt, "gemini_quick_query")
            
            if result["success"]:
                return [TextContent(type="text", text=result['output'])]
            else:
                return [TextContent(type="text", text=f"Query failed: {result['error']}")]
        
        elif name == "gemini_analyze_code":
            code_content = arguments.get("code_content", "")
            analysis_type = arguments.get("analysis_type", "comprehensive")
            
            # Input validation
            if not isinstance(code_content, str) or not code_content.strip():
                return [TextContent(type="text", text="Error: Code content must be a non-empty string")]
            
            if not isinstance(analysis_type, str) or analysis_type not in ["comprehensive", "security", "performance", "architecture"]:
                return [TextContent(type="text", text="Error: Invalid analysis type")]
            
            if len(code_content) > MAX_FILE_SIZE:
                return [TextContent(type="text", text=f"⚠️ Code too large ({len(code_content)} bytes). Max: {MAX_FILE_SIZE} bytes")]
            
            line_count = len(code_content.splitlines())
            if line_count > MAX_LINES:
                return [TextContent(type="text", text=f"⚠️ Too many lines ({line_count}). Max: {MAX_LINES} lines")]
            
            # Sanitize inputs to prevent prompt injection
            sanitized_code = sanitize_for_prompt(code_content, max_length=MAX_FILE_SIZE)
            
            prompt = f"""Perform a {analysis_type} analysis of this code:

{sanitized_code}

Provide comprehensive analysis including:
1. Code structure and organization
2. Logic flow and algorithm efficiency
3. Security considerations and vulnerabilities
4. Performance implications and optimizations
5. Error handling and edge cases
6. Code quality and maintainability
7. Best practices compliance
8. Specific recommendations for improvements

Be thorough and provide actionable insights. Respond in plain text format without markdown. Break content into clear paragraphs when needed. Format your response like a helpful AI assistant would - clear, well-structured, and easy to read with proper line breaks between ideas."""
            
            result = await execute_gemini_cli_streaming(prompt, "gemini_analyze_code")
            
            if result["success"]:
                return [TextContent(type="text", text=result['output'])]
            else:
                return [TextContent(type="text", text=f"Analysis failed: {result['error']}")]
        
        elif name == "gemini_codebase_analysis":
            directory_path = arguments.get("directory_path", "")
            analysis_scope = arguments.get("analysis_scope", "all")
            
            # Input validation
            if not isinstance(directory_path, str) or not directory_path.strip():
                return [TextContent(type="text", text="Error: Directory path must be a non-empty string")]
            
            if not isinstance(analysis_scope, str) or analysis_scope not in ["structure", "security", "performance", "patterns", "all"]:
                return [TextContent(type="text", text="Error: Invalid analysis scope")]
            
            logger.info(f"Initiating codebase analysis for directory: {directory_path} with scope: {analysis_scope}")
            
            # Path security validation
            is_valid, error_msg, resolved_path = validate_path_security(directory_path)
            if not is_valid:
                return [TextContent(type="text", text=f"❌ {error_msg}")]
            
            if not resolved_path.exists():
                return [TextContent(type="text", text=f"❌ Directory not found: {directory_path}")]
            
            if not resolved_path.is_dir():
                return [TextContent(type="text", text=f"❌ Path is not a directory: {directory_path}")]
            
            # Use sanitized directory name for prompt (just the name, not full path)
            safe_dir_name = sanitize_for_prompt(resolved_path.name, max_length=100)
            
            prompt = f"""Analyze this codebase in directory '{safe_dir_name}' (scope: {analysis_scope}):

Provide comprehensive analysis including:
1. Overall architecture and design patterns
2. Code quality and maintainability assessment
3. Security considerations and potential vulnerabilities
4. Performance implications and bottlenecks
5. Best practices adherence and improvement suggestions
6. Dependencies and integration points
7. Testing coverage and quality assurance
8. Documentation and code clarity

Be thorough and detailed in your analysis. Focus on actionable insights and recommendations. Respond in plain text format without markdown. Break content into clear paragraphs when needed. Format your response like a helpful AI assistant would - clear, well-structured, and easy to read with proper line breaks between ideas."""
            logger.info(f"Constructed prompt for Gemini CLI (length: {len(prompt)} chars)")
            
            result = await execute_gemini_cli_streaming(prompt, "gemini_codebase_analysis")
            
            if result["success"]:
                return [TextContent(type="text", text=result['output'])]
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
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server started successfully")
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
