#!/usr/bin/env python3
"""
Slim Gemini CLI MCP Server
"""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from claude_gemini_mcp.config import get_config
from claude_gemini_mcp.helpers.code_analyzer import CodebaseAnalysisError, analyze_codebase

# Import markdown utilities
try:
    from claude_gemini_mcp.helpers.markdown_utils import markdown_to_text

    MARKDOWN_UTILS_AVAILABLE = True
except ImportError:
    MARKDOWN_UTILS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server: Server = Server("slim-gemini-cli-mcp")

# Configuration - now loaded from config.py with backward compatibility
cfg = get_config()
MAX_FILE_SIZE = cfg.get_limit("max_file_size", 81920)  # 80KB default
MAX_LINES = cfg.get_limit("max_lines", 800)  # 800 lines default


# Enhanced Security functions - prevent prompt injection and path traversal attacks
def sanitize_for_prompt(text: str, max_length: int = None) -> str:
    """Enhanced sanitize text input to prevent prompt injection attacks"""
    if not isinstance(text, str):
        return ""

    # Get max length from config if not provided
    if max_length is None:
        max_length = cfg.get_limit("sanitization_max_length", 100000)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]

    # Unicode normalization to prevent homograph attacks
    import unicodedata

    text = unicodedata.normalize("NFC", text)

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
        "[/INST]",
        # Additional enterprise security patterns
        "javascript:",
        "data:",
        "vbscript:",
        "file://",
        "ftp://",
        # SQL injection patterns
        "' or 1=1--",
        "'; drop table",
        "union select",
        "exec(",
        "eval(",
        # Script injection patterns
        "<script",
        "</script>",
        "onload=",
        "onerror=",
        "onclick=",
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in text_lower:
            # Replace with safe alternative (case-insensitive)
            import re

            # Create case-insensitive regex pattern
            escaped_pattern = re.escape(pattern)
            replacement = f"[filtered-content]"
            text = re.sub(escaped_pattern, replacement, text, flags=re.IGNORECASE)

    # Escape potential control characters
    text = text.replace("\x00", "").replace("\x1b", "")

    return text


def validate_path_security(file_path: str) -> tuple[bool, str, Optional[Path]]:
    """Validate path for security - prevent path traversal attacks"""
    try:
        if not isinstance(file_path, str) or not file_path.strip():
            return False, "Invalid path", None

        # Handle special cases and expand user paths
        if file_path.startswith("~"):
            # Block home directory access for security
            return False, "Path outside allowed directory", None

        # Block absolute paths that are clearly system paths
        if file_path.startswith(
            ("/etc/", "/proc/", "/sys/", "/dev/", "/var/", "/usr/", "/bin/", "/sbin/")
        ):
            return False, "Path outside allowed directory", None

        # Block Windows system paths
        if file_path.lower().startswith(
            ("c:\\windows", "c:/windows", "\\windows", "/windows")
        ):
            return False, "Path outside allowed directory", None

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


# Model configuration - now managed by config.py
# Backward compatibility: still support environment variables if config doesn't provide values
GEMINI_MODELS = {
    "flash": os.getenv("GEMINI_FLASH_MODEL", cfg.get_raw_config().get("models", {}).get("nicknames", {}).get("flash", "gemini-2.5-flash")),
    "pro": os.getenv("GEMINI_PRO_MODEL", cfg.get_raw_config().get("models", {}).get("nicknames", {}).get("pro", "gemini-2.5-pro")),
}

# API key for direct API usage
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model assignment - now handled by config.get_model() but kept for reference
# This will be replaced by direct calls to cfg.get_model(tool_name)


async def execute_gemini_api(prompt: str, model_name: str) -> Dict[str, Any]:
    """Execute Gemini API directly with specified model"""
    try:
        # Validate API key securely
        if (
            not GOOGLE_API_KEY
            or not isinstance(GOOGLE_API_KEY, str)
            or len(GOOGLE_API_KEY.strip()) < 10
        ):
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

        error_message = re.sub(
            r"AIzaSy[A-Za-z0-9_-]{25,}", "[API_KEY_REDACTED]", error_message
        )
        error_message = re.sub(
            r"sk-[A-Za-z0-9_-]{32,}", "[API_KEY_REDACTED]", error_message
        )
        error_message = re.sub(
            r"Bearer [A-Za-z0-9_.-]{10,}", "[TOKEN_REDACTED]", error_message
        )

        logger.error(f"API call failed: {error_message}")
        return {"success": False, "error": error_message}


@server.list_tools()  # type: ignore
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
                        "description": "Question to ask Gemini CLI",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional context to provide with the query",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="gemini_analyze_code",
            description="Analyze specific code sections with focused insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "code_content": {
                        "type": "string",
                        "description": "Code content to analyze",
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": [
                            "comprehensive",
                            "security",
                            "performance",
                            "architecture",
                        ],
                        "default": "comprehensive",
                        "description": "Type of analysis to perform",
                    },
                },
                "required": ["code_content"],
            },
        ),
        Tool(
            name="gemini_codebase_analysis",
            description="Analyze entire directories using Gemini CLI's 1M token context",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to directory to analyze",
                    },
                    "analysis_scope": {
                        "type": "string",
                        "enum": [
                            "structure",
                            "security",
                            "performance",
                            "patterns",
                            "all",
                        ],
                        "default": "all",
                        "description": "Scope of analysis",
                    },
                },
                "required": ["directory_path"],
            },
        ),
    ]


def _process_result_output(
    result: Dict[str, Any], convert_markdown: bool = True
) -> Dict[str, Any]:
    """Process result output through markdown parser if enabled and available.

    Args:
        result: Result dictionary with 'success' and 'output' keys
        convert_markdown: Whether to convert markdown to plain text

    Returns:
        dict: Processed result dictionary
    """
    if not result["success"] or not result.get("output"):
        return result

    # Skip conversion if disabled or markdown utils not available
    if not convert_markdown or not MARKDOWN_UTILS_AVAILABLE:
        if not convert_markdown:
            logger.info("Markdown conversion bypassed for debugging")
        elif not MARKDOWN_UTILS_AVAILABLE:
            logger.warning("Markdown utils not available, skipping conversion")
        return result

    try:
        original_output = result["output"]
        logger.info("Converting markdown to plain text...")

        # Convert markdown to plain text
        converted_output = markdown_to_text(original_output)

        # Update result with converted output
        result["output"] = converted_output

        original_len = len(original_output)
        converted_len = len(converted_output)
        logger.info(
            f"Markdown conversion complete: {original_len} → {converted_len} chars"
        )

    except Exception as e:
        logger.warning(f"Markdown conversion failed: {str(e)}, using original output")
        # Keep original output if conversion fails

    return result


def _validate_prompt_input(prompt: str, task_type: str) -> Dict[str, Any] | None:
    """Validate prompt input parameters, return error dict or None if valid"""
    if not isinstance(prompt, str) or not prompt.strip():
        return {"success": False, "error": "Invalid prompt: must be non-empty string"}
    
    max_prompt_size = cfg.get_limit("max_prompt_size", 1000000)
    if len(prompt) > max_prompt_size:
        return {"success": False, "error": f"Prompt too large (max {max_prompt_size} bytes)"}
    
    return None


def _get_validated_model(task_type: str) -> tuple[str, Dict[str, Any] | None]:
    """Get and validate model name, return (model, error_dict)"""
    model_name = cfg.get_model(task_type, None)
    if not model_name:
        return "", {"success": False, "error": "Invalid task type or no model configured"}
    
    # Resolve model nickname for backward compatibility
    if model_name in GEMINI_MODELS:
        model_name = GEMINI_MODELS[model_name]
    
    # Validate model name format
    if not isinstance(model_name, str) or not model_name.strip():
        return "", {"success": False, "error": "Invalid model name"}
    if not all(c.isalnum() or c in ".-" for c in model_name):
        return "", {"success": False, "error": "Invalid model name characters"}
    
    return model_name, None


def _format_output_log(content: str) -> str:
    """Format output for logging with truncation"""
    stripped = content.strip()
    return f"{stripped[:100]}{'...' if len(stripped) > 100 else ''}"


async def _read_line_with_timeout(process: asyncio.subprocess.Process) -> bytes | None:
    """Read single line from process with timeout, return None on timeout"""
    if process.stdout is None:
        return b""
    
    try:
        return await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
    except asyncio.TimeoutError:
        return None


def _should_show_progress(current_time: float, last_progress: float) -> bool:
    """Check if progress message should be displayed"""
    return current_time - last_progress > 15


def _log_progress_update(start_time: float) -> float:
    """Log progress and return updated timestamp"""
    current_time = asyncio.get_event_loop().time()
    elapsed = int(current_time - start_time)
    logger.info(f"Analysis in progress... {elapsed}s elapsed")
    return current_time


async def _collect_remaining_output(process: asyncio.subprocess.Process, output_lines: list[str]) -> str:
    """Collect any remaining output after streaming completes"""
    remaining_stdout, stderr = await process.communicate()
    
    if remaining_stdout:
        decoded_remaining = remaining_stdout.decode("utf-8", errors="replace")
        output_lines.append(decoded_remaining)
        logger.info(f"Final output: {_format_output_log(decoded_remaining)}")
    
    stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
    return stderr_str


async def _stream_process_output(process: asyncio.subprocess.Process) -> tuple[str, str]:
    """Stream subprocess output with progress tracking"""
    output_lines = []
    start_time = asyncio.get_event_loop().time()
    last_progress = start_time
    
    logger.info("Streaming Gemini CLI output...")
    
    # Main streaming loop
    while process.returncode is None:
        line = await _read_line_with_timeout(process)
        
        if line is None:  # Timeout occurred
            current_time = asyncio.get_event_loop().time()
            if _should_show_progress(current_time, last_progress):
                last_progress = _log_progress_update(start_time)
            continue
        
        if line:  # Data received
            try:
                decoded_line = line.decode("utf-8", errors="replace")
                output_lines.append(decoded_line)
                logger.info(f"Gemini output: {_format_output_log(decoded_line)}")
                last_progress = asyncio.get_event_loop().time()
            except (BrokenPipeError, OSError):
                logger.warning("Process output stream broken, checking for crash")
                break
        else:  # No more data and process finished
            break
    
    # Collect any remaining output
    stderr_str = await _collect_remaining_output(process, output_lines)
    full_output = "".join(output_lines)
    
    return full_output, stderr_str


def _sanitize_error_output(stderr: str) -> str:
    """Remove sensitive information from error output"""
    import re
    
    # Remove various API key patterns
    sanitized = re.sub(r"AIzaSy[A-Za-z0-9_-]{25,}", "[API_KEY_REDACTED]", stderr)
    sanitized = re.sub(r"sk-[A-Za-z0-9_-]{32,}", "[API_KEY_REDACTED]", sanitized)
    sanitized = re.sub(r"Bearer [A-Za-z0-9_.-]{10,}", "[TOKEN_REDACTED]", sanitized)
    
    return sanitized


async def execute_gemini_cli_streaming(
    prompt: str, task_type: str = "gemini_quick_query", convert_markdown: bool = True, _test_mode: bool = False
) -> Dict[str, Any]:
    """Execute Gemini CLI with model selection and API fallback"""
    logger.info("Starting Gemini CLI execution with streaming")
    
    # Validate input parameters
    validation_error = _validate_prompt_input(prompt, task_type)
    if validation_error:
        return validation_error
    
    logger.info(f"Prompt length: {len(prompt)} characters, Task type: {task_type}")
    
    # Get validated model
    model_name, model_error = _get_validated_model(task_type)
    if model_error:
        return model_error
    
    logger.info(f"Selected model: {model_name}")
    
    try:
        # Handle test mode early return
        if _test_mode:
            logger.info("Test mode enabled - returning dummy response")
            dummy_output = f"Dummy response for prompt: {prompt[:50]}..." if len(prompt) > 50 else f"Dummy response for prompt: {prompt}"
            result = {"success": True, "output": dummy_output}
            return _process_result_output(result, convert_markdown)
        
        # Try API first if available
        if GOOGLE_API_KEY:
            logger.info("Attempting direct API call")
            result = await execute_gemini_api(prompt, model_name)
            if result["success"]:
                return _process_result_output(result, convert_markdown)
            logger.warning("API call failed, falling back to CLI")
        
        # Execute CLI subprocess
        cmd_args = ["gemini", "-m", model_name, "-p", prompt]
        logger.info(f"Executing command: gemini -m {model_name} -p [prompt length: {len(prompt)}]")
        
        # Setup environment variables
        env = {"PATH": os.environ.get("PATH", "")}
        if "GOOGLE_CLOUD_PROJECT" in os.environ:
            env["GOOGLE_CLOUD_PROJECT"] = os.environ["GOOGLE_CLOUD_PROJECT"]
        
        # Create subprocess with secure execution
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        logger.info(f"Process created with PID: {process.pid}")
        
        # Stream output with progress tracking
        full_output, stderr_str = await _stream_process_output(process)
        
        logger.info(f"Process completed with return code: {process.returncode}")
        logger.info(f"Total output length: {len(full_output)} chars")
        
        # Handle process result
        if process.returncode == 0:
            logger.info("Gemini CLI execution successful")
            result = {"success": True, "output": full_output}
            return _process_result_output(result, convert_markdown)
        else:
            sanitized_stderr = _sanitize_error_output(stderr_str)
            logger.error(f"Gemini CLI failed with return code {process.returncode}: {sanitized_stderr[:200]}...")
            return {"success": False, "error": sanitized_stderr}
    
    except Exception as e:
        logger.error(f"Exception during Gemini CLI execution: {str(e)}")
        return {"success": False, "error": str(e)}


def _create_error_response(message: str) -> List[TextContent]:
    """Create standardized error response"""
    print(f"Error: {message}")
    return [TextContent(type="text", text=f"❌ Error: {message}")]


def _create_success_response(output: str, header: str = "") -> List[TextContent]:
    """Create standardized success response with optional header"""
    if header:
        print(f"\n{header}")
        print("=" * 50)
        print()
    print(output)
    if header:
        print()
        print("=" * 50)
    print("✅ Request completed")
    return [TextContent(type="text", text=output)]


async def _handle_quick_query(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle gemini_quick_query tool requests"""
    query = arguments.get("query", "")
    context = arguments.get("context", "")
    
    # Validate inputs
    if not isinstance(query, str) or not query.strip():
        return _create_error_response("Query must be a non-empty string")
    if not isinstance(context, str):
        return _create_error_response("Context must be a string")
    
    # Sanitize inputs for security
    sanitized_query = sanitize_for_prompt(query, max_length=cfg.get_limit("max_prompt_size", 10000) // 100)
    sanitized_context = sanitize_for_prompt(context, max_length=cfg.get_limit("max_prompt_size", 50000) // 20)
    
    # Build prompt with context-aware formatting
    base_instruction = "Provide a concise answer in plain text format. Do not use markdown formatting. Break content into clear paragraphs when needed. Format your response like a helpful AI assistant would - clear, well-structured, and easy to read with proper line breaks between ideas."
    
    if sanitized_context:
        prompt = f"Context: {sanitized_context}\n\nQuestion: {sanitized_query}\n\n{base_instruction}"
    else:
        prompt = f"Question: {sanitized_query}\n\n{base_instruction}"
    
    # Execute query and handle result
    result = await execute_gemini_cli_streaming(prompt, "gemini_quick_query")
    
    if result["success"]:
        return _create_success_response(result["output"], f"Query: {query}")
    else:
        return _create_error_response(result["error"])


async def _handle_code_analysis(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle gemini_analyze_code tool requests"""
    code_content = arguments.get("code_content", "")
    analysis_type = arguments.get("analysis_type", "comprehensive")
    
    # Validate inputs
    if not isinstance(code_content, str) or not code_content.strip():
        return _create_error_response("Code content must be a non-empty string")
    
    valid_analysis_types = ["comprehensive", "security", "performance", "architecture"]
    if not isinstance(analysis_type, str) or analysis_type not in valid_analysis_types:
        return _create_error_response("Invalid analysis type")
    
    # Check size limits
    if len(code_content) > MAX_FILE_SIZE:
        return _create_error_response(f"Code too large ({len(code_content)} bytes). Max: {MAX_FILE_SIZE} bytes")
    
    line_count = len(code_content.splitlines())
    if line_count > MAX_LINES:
        return _create_error_response(f"Too many lines ({line_count}). Max: {MAX_LINES} lines")
    
    # Sanitize code input
    sanitized_code = sanitize_for_prompt(code_content, max_length=cfg.get_limit("max_file_size", MAX_FILE_SIZE))
    
    # Build analysis prompt
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

CRITICAL FORMATTING: Output ONLY plain text. Do NOT use:
- No ### headers or ** bold text or * italics
- No --- separators or bullet points
- No markdown formatting whatsoever
- No special characters for emphasis
Write exactly like a plain text document. Use simple numbered points and paragraph breaks only."""
    
    # Execute analysis and handle result
    result = await execute_gemini_cli_streaming(prompt, "gemini_analyze_code")
    
    if result["success"]:
        header = f"Code Analysis: {analysis_type}\nLines: {line_count}"
        return _create_success_response(result["output"], header)
    else:
        return _create_error_response(f"Analysis failed: {result['error']}")


async def _handle_codebase_analysis(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle gemini_codebase_analysis tool requests"""
    directory_path = arguments.get("directory_path", "")
    analysis_scope = arguments.get("analysis_scope", "all")
    
    # Validate inputs
    if not isinstance(directory_path, str) or not directory_path.strip():
        return _create_error_response("Directory path must be a non-empty string")
    
    valid_scopes = ["structure", "security", "performance", "patterns", "all"]
    if not isinstance(analysis_scope, str) or analysis_scope not in valid_scopes:
        return _create_error_response("Invalid analysis scope")
    
    logger.info(f"Initiating codebase analysis for directory: {directory_path} with scope: {analysis_scope}")
    
    # Validate path security
    is_valid, error_msg, resolved_path = validate_path_security(directory_path)
    if not is_valid or resolved_path is None:
        return _create_error_response(error_msg)
    
    try:
        # Configure analysis parameters
        max_total_size = 500_000 if analysis_scope == "all" else 200_000
        config = {
            "max_total_size": max_total_size,
            "skip_directories": ["node_modules", ".git", "__pycache__", ".venv", "venv"],
            "include_hidden": [".github"],
            "skip_patterns": ["*.pyc", "*.log", "*.tmp"],
        }
        
        logger.info(f"Analyzing codebase with config: {config}")
        result = analyze_codebase(str(resolved_path), max_total_size=max_total_size, config=config)
        
        if result.error:
            logger.error(f"Analysis failed: {result.error}")
            return _create_error_response(f"Analysis failed: {result.error}")
        
        # Generate structured output
        output_lines = [
            f"Codebase Analysis for {directory_path} (Scope: {analysis_scope})",
            "=" * 60, "",
            "PROJECT OVERVIEW:",
            f"Total Files: {result.stats.files_analyzed}",
            f"Total Lines: {result.structure.total_lines}",
            f"Analysis Time: {result.stats.total_time:.2f}s",
            f"Primary Language: {result.project_report['summary']['primary_language']}",
            "", "TECHNOLOGY STACK:"
        ]
        
        # Add technology stack details
        for category, techs in result.tech_stack.items():
            if techs:
                output_lines.append(f"{category.title()}: {', '.join(techs)}")
        
        output_lines.extend(["", "DIRECTORY STRUCTURE:"])
        
        # Add directory structure summary
        for dir_name, dir_info in result.structure.directories.items():
            file_count = dir_info.get("file_count", 0)
            output_lines.append(f"  {dir_name}/ ({file_count} files)")
        
        output_lines.extend(["", "=" * 60, "Analysis completed successfully"])
        
        output = "\n".join(output_lines)
        print(output)
        print("✅ Request completed")
        return [TextContent(type="text", text=output)]
    
    except (ValueError, FileNotFoundError, NotADirectoryError) as e:
        logger.error(f"Input validation failed: {e}")
        return _create_error_response(f"Input validation failed: {e}")
    except CodebaseAnalysisError as e:
        logger.error(f"Codebase analysis failed: {e}")
        return _create_error_response(f"Codebase analysis failed: {e}")


# Tool handler registry for clean dispatch
TOOL_HANDLERS = {
    "gemini_quick_query": _handle_quick_query,
    "gemini_analyze_code": _handle_code_analysis,
    "gemini_codebase_analysis": _handle_codebase_analysis,
}


@server.call_tool()  # type: ignore
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Main tool dispatcher with clean handler delegation"""
    logger.info(f"Tool call received: {name} with arguments: {list(arguments.keys())}")
    logger.debug(f"Full arguments: {arguments}")
    
    try:
        # Dispatch to specific tool handler
        if name in TOOL_HANDLERS:
            return await TOOL_HANDLERS[name](arguments)
        else:
            return _create_error_response(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return _create_error_response(str(e))


async def main() -> None:
    """Run the server"""
    try:
        logger.info("Starting Slim Gemini CLI MCP Server...")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server started successfully")
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
