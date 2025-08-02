#!/usr/bin/env python3
"""
Slim Gemini CLI MCP Server
"""

import asyncio
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from claude_gemini_mcp.config import get_config
from claude_gemini_mcp.helpers.execution_orchestrator import execute_gemini_smart
from claude_gemini_mcp.helpers.security import (
    sanitize_for_prompt,
    validate_path_security,
)
from claude_gemini_mcp.helpers.tools.codebase_analyzer import (
    CodebaseAnalysisError,
    analyze_codebase,
)

# Import markdown utilities
try:
    pass

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
    sanitized_query = sanitize_for_prompt(
        query, max_length=cfg.get_limit("max_prompt_size", 10000) // 100
    )
    sanitized_context = sanitize_for_prompt(
        context, max_length=cfg.get_limit("max_prompt_size", 50000) // 20
    )

    # Build prompt with context-aware formatting
    base_instruction = "Provide a concise answer in plain text format. Do not use markdown formatting. Break content into clear paragraphs when needed. Format your response like a helpful AI assistant would - clear, well-structured, and easy to read with proper line breaks between ideas."

    if sanitized_context:
        prompt = f"Context: {sanitized_context}\n\nQuestion: {sanitized_query}\n\n{base_instruction}"
    else:
        prompt = f"Question: {sanitized_query}\n\n{base_instruction}"

    # Execute query and handle result
    result = await execute_gemini_smart(prompt, "gemini_quick_query")

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
        return _create_error_response(
            f"Code too large ({len(code_content)} bytes). Max: {MAX_FILE_SIZE} bytes"
        )

    line_count = len(code_content.splitlines())
    if line_count > MAX_LINES:
        return _create_error_response(
            f"Too many lines ({line_count}). Max: {MAX_LINES} lines"
        )

    # Sanitize code input
    sanitized_code = sanitize_for_prompt(
        code_content, max_length=cfg.get_limit("max_file_size", MAX_FILE_SIZE)
    )

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
    result = await execute_gemini_smart(prompt, "gemini_analyze_code")

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

    logger.info(
        f"Initiating codebase analysis for directory: {directory_path} with scope: {analysis_scope}"
    )

    # Validate path security
    is_valid, error_msg, resolved_path = validate_path_security(directory_path)
    if not is_valid or resolved_path is None:
        return _create_error_response(error_msg)

    try:
        # Configure analysis parameters
        max_total_size = 500_000 if analysis_scope == "all" else 200_000
        config = {
            "max_total_size": max_total_size,
            "skip_directories": [
                "node_modules",
                ".git",
                "__pycache__",
                ".venv",
                "venv",
            ],
            "include_hidden": [".github"],
            "skip_patterns": ["*.pyc", "*.log", "*.tmp"],
        }

        logger.info(f"Analyzing codebase with config: {config}")
        result = analyze_codebase(
            str(resolved_path), max_total_size=max_total_size, config=config
        )

        if result.error:
            logger.error(f"Analysis failed: {result.error}")
            return _create_error_response(f"Analysis failed: {result.error}")

        # Generate structured output
        output_lines = [
            f"Codebase Analysis for {directory_path} (Scope: {analysis_scope})",
            "=" * 60,
            "",
            "PROJECT OVERVIEW:",
            f"Total Files: {result.stats.files_analyzed}",
            f"Total Lines: {result.structure.total_lines}",
            f"Analysis Time: {result.stats.total_time:.2f}s",
            f"Primary Language: {result.project_report['summary']['primary_language']}",
            "",
            "TECHNOLOGY STACK:",
        ]

        # Add technology stack details
        tech_stack_data = [
            ("frameworks", result.tech_stack.frameworks),
            ("databases", result.tech_stack.databases),
            ("testing_frameworks", result.tech_stack.testing_frameworks),
            ("build_tools", result.tech_stack.build_tools),
            ("deployment_tools", result.tech_stack.deployment_tools),
            ("languages", result.tech_stack.languages),
            ("dependencies", result.tech_stack.dependencies),
            ("dev_dependencies", result.tech_stack.dev_dependencies),
        ]

        for category, techs in tech_stack_data:
            if techs:
                if isinstance(techs, dict):
                    tech_list = [f"{k} ({v})" if v else k for k, v in techs.items()]
                else:
                    tech_list = list(techs)
                output_lines.append(
                    f"{category.replace('_', ' ').title()}: {', '.join(tech_list)}"
                )

        output_lines.extend(["", "DIRECTORY STRUCTURE:"])

        # Add directory structure summary
        for dir_name in result.structure.directories:
            output_lines.append(f"  {dir_name}/")

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
