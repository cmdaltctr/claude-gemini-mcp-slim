##################################################################
#################### IMPORTS AND DEPENDENCIES ###################
##################################################################

# Standard library imports for asynchronous operations, subprocess management, and utilities
import asyncio
import subprocess
import logging
import json
import os
import shlex
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# MCP (Model Context Protocol) server components for building AI tool integrations
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

##################################################################
#################### LOGGING CONFIGURATION ######################
##################################################################

# Configure logging to track server operations and debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

##################################################################
#################### CONFIGURATION CLASSES ######################
##################################################################

@dataclass
class SlimGeminiConfig:
    """Streamlined configuration for token-efficient Gemini CLI integration"""
    timeout: int = 90  # Extended timeout for comprehensive analysis
    max_file_size: int = 81920  # 80KB file size limit
    max_lines: int = 800  # Maximum lines per file
    response_word_limit: int = 800  # Maximum words in response
    supported_extensions: List[str] = None  # File types to analyze

    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = [
                ".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs",  # Programming languages
                ".vue", ".html", ".css", ".scss", ".sass", ".jsx", ".tsx"  # Frontend files
            ]

##################################################################
#################### MAIN MCP SERVER CLASS ######################
##################################################################

class SlimGeminiMCPServer:
    """Streamlined MCP server focused on token efficiency and essential automation"""

    def __init__(self, config: SlimGeminiConfig):
        self.config = config
        self.server = Server("slim-gemini-cli-mcp")  # Create MCP server instance
        self.setup_tools()  # Register essential tools only

    ##################################################################
    #################### TOOL REGISTRATION SYSTEM ###################
    ##################################################################

    def setup_tools(self):
        """Register the 3 essential MCP tools for token-efficient development"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Define the 3 core tools optimized for Claude Code token savings"""
            return [
                # Universal query tool for quick questions and clarifications
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
                # Core analysis tool for focused code review and insights
                Tool(
                    name="gemini_analyze_code",
                    description="Analyze specific code sections with focused insights (up to 800 words)",
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
                # Large-scale analysis leveraging Gemini's 1M token context window
                Tool(
                    name="gemini_codebase_analysis",
                    description="Analyze entire directories using Gemini CLI's 1M token context window",
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
                                "default": ["*.py", "*.js", "*.ts", "*.vue", "*.html", "*.css"],
                                "description": "File patterns to include in analysis"
                            },
                            "analysis_scope": {
                                "type": "string",
                                "enum": ["structure", "security", "performance", "patterns", "all"],
                                "default": "all",
                                "description": "Scope of codebase analysis"
                            }
                        },
                        "required": ["directory_path"]
                    }
                )
            ]

        ##################################################################
        #################### TOOL CALL ROUTER ############################
        ##################################################################

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Route tool calls to appropriate handler methods"""
            try:
                # Route each tool call to its corresponding method
                if name == "gemini_quick_query":
                    return await self.quick_query(**arguments)
                elif name == "gemini_analyze_code":
                    return await self.analyze_code(**arguments)
                elif name == "gemini_codebase_analysis":
                    return await self.codebase_analysis(**arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    ##################################################################
    #################### CORE GEMINI CLI EXECUTION ###################
    ##################################################################

    async def execute_gemini_cli(self, prompt: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute Gemini CLI with basic error handling and timeout management"""
        if timeout is None:
            timeout = self.config.timeout

        try:
            # Safely escape the prompt to prevent shell injection
            escaped_prompt = shlex.quote(prompt)

            # Build command for Gemini CLI non-interactive mode
            cmd = f"gemini -p {escaped_prompt}"

            logger.info(f"Executing Gemini CLI command")

            # Create subprocess with proper I/O handling
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )

            # Wait for command completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            # Decode subprocess output
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')

            # Return structured result
            if process.returncode == 0:
                return {
                    "success": True,
                    "output": stdout_str,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": stderr_str,
                    "return_code": process.returncode,
                    "timestamp": datetime.now().isoformat()
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Gemini CLI execution timed out after {timeout} seconds",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    ##################################################################
    #################### PROMPT GENERATION SYSTEM ###################
    ##################################################################

    def create_focused_prompt(self, content: str, analysis_type: str, focus_areas: Optional[List[str]] = None) -> str:
        """Create token-efficient prompts optimized for 800-word responses"""

        # Base prompt with word limit for token efficiency
        base_prompt = f"Analyze this code (respond in under {self.config.response_word_limit} words):\n\n{content}\n\n"

        # Add analysis-specific instructions
        if analysis_type == "comprehensive":
            instructions = """Provide focused analysis covering:
1. Critical bugs or logic errors
2. Security vulnerabilities
3. Performance bottlenecks
4. Architecture improvements
5. Best practices compliance
Focus on actionable insights only."""

        elif analysis_type == "security":
            instructions = """Security-focused analysis:
1. Vulnerability assessment
2. Input validation issues
3. Authentication/authorization concerns
4. Data protection measures
5. Common attack vectors
Prioritize critical security issues."""

        elif analysis_type == "performance":
            instructions = """Performance-focused analysis:
1. Algorithmic complexity issues
2. Resource usage patterns
3. Bottleneck identification
4. Optimization opportunities
5. Scalability concerns
Focus on measurable improvements."""

        elif analysis_type == "architecture":
            instructions = """Architecture-focused analysis:
1. Design patterns and structure
2. Component relationships
3. Modularity and coupling
4. Separation of concerns
5. Extensibility considerations
Focus on structural improvements."""

        # Add specific focus areas if provided
        if focus_areas:
            instructions += f"\n\nPay special attention to: {', '.join(focus_areas)}"

        return base_prompt + instructions

    ##################################################################
    #################### TOOL IMPLEMENTATION METHODS ################
    ##################################################################

    async def quick_query(self, query: str, context: Optional[str] = None) -> List[TextContent]:
        """Handle quick questions with optional context for efficient Q&A"""

        # Build query prompt with optional context
        if context:
            prompt = f"Context: {context}\n\nQuestion: {query}\n\nProvide a concise, actionable answer."
        else:
            prompt = f"Question: {query}\n\nProvide a concise, actionable answer."

        result = await self.execute_gemini_cli(prompt)

        # Return formatted response
        if result["success"]:
            return [TextContent(
                type="text",
                text=f"**Query:** {query}\n\n{result['output']}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Query failed: {result['error']}"
            )]

    async def analyze_code(self, code_content: str, analysis_type: str = "comprehensive",
                          focus_areas: Optional[List[str]] = None) -> List[TextContent]:
        """Analyze code with focused insights optimized for token efficiency"""

        # Check content size limits for token efficiency
        if len(code_content) > self.config.max_file_size:
            return [TextContent(
                type="text",
                text=f"⚠️ Code content too large ({len(code_content)} bytes). Maximum size: {self.config.max_file_size} bytes (80KB)"
            )]

        # Check line count limits
        line_count = len(code_content.splitlines())
        if line_count > self.config.max_lines:
            return [TextContent(
                type="text",
                text=f"⚠️ Code has too many lines ({line_count}). Maximum: {self.config.max_lines} lines"
            )]

        # Create focused prompt for analysis
        prompt = self.create_focused_prompt(code_content, analysis_type, focus_areas)
        result = await self.execute_gemini_cli(prompt)

        # Return formatted analysis results
        if result["success"]:
            return [TextContent(
                type="text",
                text=f"# Code Analysis Results\n\n**Type:** {analysis_type}\n**Lines:** {line_count}\n\n{result['output']}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Analysis failed: {result['error']}"
            )]

    async def codebase_analysis(self, directory_path: str, file_patterns: List[str],
                               analysis_scope: str = "all") -> List[TextContent]:
        """Analyze entire codebase leveraging Gemini CLI's 1M token context window"""

        try:
            # Validate directory path
            if not Path(directory_path).exists():
                return [TextContent(
                    type="text",
                    text=f"❌ Directory not found: {directory_path}"
                )]

            # Use Gemini CLI's @ syntax for directory analysis (1M token context)
            prompt = f"""@{directory_path} Analyze this codebase (scope: {analysis_scope}):

File patterns: {', '.join(file_patterns)}

Provide analysis covering:
1. Project structure and organization
2. Code quality and patterns
3. Security considerations
4. Performance implications
5. Architecture assessment
6. Improvement recommendations

Focus on {analysis_scope} aspects. Keep response under {self.config.response_word_limit} words."""

            # Use extended timeout for large codebagemini_cli_mcp_server.pyse analysis
            result = await self.execute_gemini_cli(prompt, timeout=120)

            # Return formatted codebase analysis
            if result["success"]:
                return [TextContent(
                    type="text",
                    text=f"# Codebase Analysis\n\n**Directory:** {directory_path}\n**Scope:** {analysis_scope}\n**Patterns:** {', '.join(file_patterns)}\n\n{result['output']}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Codebase analysis failed: {result['error']}"
                )]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error analyzing codebase: {str(e)}"
            )]

    ##################################################################
    #################### SERVER STARTUP AND MAIN LOOP ###############
    ##################################################################

    async def run(self):
        """Start the MCP server and handle I/O communication"""
        async with stdio_server(self.server) as (read_stream, write_stream):
            logger.info("Slim Gemini CLI MCP Server started - Token-efficient mode")
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

##################################################################
#################### MAIN EXECUTION ENTRY POINT ################
##################################################################

def main():
    """Initialize and run the slim MCP server"""
    config = SlimGeminiConfig()  # Create streamlined configuration
    server = SlimGeminiMCPServer(config)  # Initialize server

    try:
        asyncio.run(server.run())  # Start the asyncio event loop
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
