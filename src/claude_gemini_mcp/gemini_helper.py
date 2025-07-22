#!/usr/bin/env python3
"""
Gemini CLI Helper - Simplified API discovery with timeout-protected CLI execution
Usage: python gemini_helper.py [command] [args]
"""

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, Optional

from claude_gemini_mcp.config import get_config

# Import hybrid progress utility
try:
    from helpers.hybrid_progress import create_dots_progress, create_spinner_progress

    PROGRESS_AVAILABLE = True
except ImportError:
    PROGRESS_AVAILABLE = False

# Import markdown utilities
try:
    from helpers.markdown_utils import markdown_to_text

    MARKDOWN_UTILS_AVAILABLE = True
except ImportError:
    MARKDOWN_UTILS_AVAILABLE = False

# Import codebase analyzer
try:
    from helpers.codebase_analyzer import analyze_codebase as real_analyze_codebase

    CODEBASE_ANALYZER_AVAILABLE = True
except ImportError:
    CODEBASE_ANALYZER_AVAILABLE = False

# Add the shared MCP environment path for Python packages (dynamic detection)
def add_shared_mcp_path():
    """Dynamically detect and add shared MCP environment to Python path"""
    import platform

    # First, try to read from installation.sh created env-info.json
    try:
        env_info_path = Path.home() / "mcp-servers" / "env-info.json"
        if env_info_path.exists():
            with open(env_info_path, "r") as f:
                env_info = json.load(f)
                site_packages = env_info.get("site_packages_path")
                if site_packages and Path(site_packages).exists():
                    # Verify google-generativeai is actually there
                    genai_path = Path(site_packages) / "google" / "generativeai"
                    if genai_path.exists():
                        sys.path.insert(0, str(site_packages))
                        return str(site_packages)
    except Exception:
        pass  # Fallback to manual detection

    # Fallback: Common locations for shared-mcp-env
    python_version = platform.python_version()[:3]  # e.g., "3.12"
    potential_paths = [
        Path.home()
        / "mcp-servers"
        / "shared-mcp-env"
        / "lib"
        / f"python{python_version}"
        / "site-packages",
        Path.home()
        / "mcp-servers"
        / "shared-mcp-env"
        / "lib"
        / "python3.12"
        / "site-packages",
        Path.home()
        / "mcp-servers"
        / "shared-mcp-env"
        / "lib"
        / "python3.11"
        / "site-packages",
        Path.home()
        / "mcp-servers"
        / "shared-mcp-env"
        / "lib"
        / "python3.10"
        / "site-packages",
    ]

    # Try to find google-generativeai in shared env
    for path in potential_paths:
        if path.exists():
            genai_path = path / "google" / "generativeai"
            if genai_path.exists():
                sys.path.insert(0, str(path))
                return str(path)

    return None


# Automatically add shared MCP path if available
_shared_path = add_shared_mcp_path()
if _shared_path:
    print(f"🔗 Using shared MCP environment: {_shared_path}", file=sys.stderr)

# Configuration - now loaded from config.py with backward compatibility
cfg = get_config()

# Model configuration - backward compatibility with environment variables
GEMINI_MODELS = {
    "flash": os.getenv("GEMINI_FLASH_MODEL", cfg.get_raw_config().get("models", {}).get("nicknames", {}).get("flash", "gemini-2.5-flash")),
    "pro": os.getenv("GEMINI_PRO_MODEL", cfg.get_raw_config().get("models", {}).get("nicknames", {}).get("pro", "gemini-2.5-pro")),
}

# Model assignment - now handled by config.get_model() but kept for reference
# This will be replaced by direct calls to cfg.get_model(tool_name)
MODEL_ASSIGNMENTS = {
    "quick_query": "flash",  # Simple Q&A
    "analyze_code": "pro",  # Deep analysis
    "analyze_codebase": "pro",  # Large context
}

# Configuration - loaded from config with backward compatibility
MAX_FILE_SIZE = cfg.get_limit("max_file_size", 81920)  # 80KB default
MAX_LINES = cfg.get_limit("max_lines", 800)  # 800 lines default  
CLI_TIMEOUT = cfg.get_timeout("cli_timeout", 60)  # 60 seconds default

# Constants for API key discovery
MIN_API_KEY_LENGTH = 10
CONFIG_PATHS = {
    'claude_code': Path.home() / ".config" / "claude-code" / "mcp_config.json",
    'claude_desktop': Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
}


def _validate_api_key(api_key: Optional[str]) -> Optional[str]:
    """Validate and return trimmed API key if valid"""
    if api_key and len(api_key.strip()) > MIN_API_KEY_LENGTH:
        return api_key.strip()
    return None


def _get_from_env_var() -> Optional[str]:
    """Get API key from environment variable"""
    return _validate_api_key(os.getenv("GOOGLE_API_KEY"))


def _extract_mcp_api_key(config: dict) -> Optional[str]:
    """Extract API key from MCP config structure"""
    return config.get("mcpServers", {}).get("gemini-mcp", {}).get("env", {}).get("GOOGLE_API_KEY")


def _get_from_json_config(file_path: Path) -> Optional[str]:
    """Read API key from JSON config file"""
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return _validate_api_key(_extract_mcp_api_key(config))
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        pass
    return None


def _get_from_env_file() -> Optional[str]:
    """Read API key from project .env file"""
    try:
        project_env = Path.cwd() / "gemini" / ".env"
        if project_env.exists():
            with open(project_env, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip("\"'")
                        return _validate_api_key(api_key)
    except (FileNotFoundError, PermissionError):
        pass
    return None


def get_api_key() -> Optional[str]:
    """Get API key using simplified discovery approach with fallback chain"""
    # Define discovery strategies in priority order
    strategies = [
        _get_from_env_var,
        lambda: _get_from_json_config(CONFIG_PATHS['claude_code']),
        lambda: _get_from_json_config(CONFIG_PATHS['claude_desktop']),
        _get_from_env_file
    ]
    
    # Try each strategy until one succeeds
    for strategy in strategies:
        if api_key := strategy():
            return api_key
    
    return None


def stream_subprocess_output(
    process: subprocess.Popen, output_queue: Queue, stop_event: threading.Event
) -> None:
    """Thread function to stream subprocess output with timeout protection"""
    try:
        while not stop_event.is_set() and process.poll() is None:
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    output_queue.put(("stdout", line))
                elif process.poll() is not None:
                    break
            time.sleep(0.01)  # Small delay to prevent tight loop

        # Get any remaining output
        if process.stdout:
            remaining = process.stdout.read()
            if remaining:
                output_queue.put(("stdout", remaining))
    except Exception as e:
        output_queue.put(("error", str(e)))
    finally:
        output_queue.put(("done", None))


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
    # Remove common prompt injection prefixes/suffixes
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


# Security validation functions
def validate_file_security(file_path: str) -> tuple[bool, str, Optional[Path]]:
    """Enhanced file security validation with additional checks"""
    try:
        if not isinstance(file_path, str) or not file_path.strip():
            return False, "Invalid file path", None

        # Resolve path and check for path traversal
        resolved_path = Path(file_path).resolve()
        current_dir = Path.cwd().resolve()

        # Check if the resolved path is within current directory tree
        try:
            resolved_path.relative_to(current_dir)
        except ValueError:
            return (
                False,
                f"File access denied - path outside allowed directory: {file_path}",
                None,
            )

        if not resolved_path.exists():
            return False, f"File not found: {file_path}", None

        if not resolved_path.is_file():
            return False, f"Path is not a file: {file_path}", None

        # Check for symbolic links to prevent symlink attacks
        if resolved_path.is_symlink():
            return False, "Symbolic links are not allowed for security reasons", None

        # File extension validation - get from config with fallback
        allowed_extensions = set(cfg.get_raw_config().get("security", {}).get("allowed_extensions", [
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".rs",
            ".vue",
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".jsx",
            ".tsx",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".md",
            ".txt",
            ".go",
            ".php",
            ".rb",
            ".swift",
            ".kt",
            ".scala",
            ".sh",
            ".bat",
            ".ps1",
        ]))
        if resolved_path.suffix.lower() not in allowed_extensions:
            return False, f"File type not supported: {resolved_path.suffix}", None

        # Check file size before processing
        max_size = cfg.get_limit("max_file_size", MAX_FILE_SIZE)
        file_stat = resolved_path.stat()
        if file_stat.st_size > max_size * 2:  # Allow some buffer
            return (
                False,
                f"File too large: {file_stat.st_size} bytes (max: {max_size * 2})",
                None,
            )

        # Basic content validation - ensure it's not a binary file
        try:
            with open(resolved_path, "rb") as f:
                chunk = f.read(1024)  # Read first 1KB
                if b"\x00" in chunk:  # Contains null bytes, likely binary
                    return False, "Binary files are not supported", None
        except Exception:
            return False, "Unable to read file for validation", None

        return True, "File validation successful", resolved_path
    except Exception as e:
        return False, f"File validation error: {str(e)}", None


def sanitize_error_message(error_message: str) -> str:
    """Enhanced error message sanitization to prevent information disclosure"""
    import re

    # Remove API keys and tokens
    error_message = re.sub(
        r"AIzaSy[A-Za-z0-9_-]{25,}", "[API_KEY_REDACTED]", error_message
    )
    error_message = re.sub(
        r"sk-[A-Za-z0-9_-]{32,}", "[API_KEY_REDACTED]", error_message
    )
    error_message = re.sub(
        r"Bearer [A-Za-z0-9_.-]{10,}", "[TOKEN_REDACTED]", error_message
    )

    # Remove file paths that might expose system structure
    error_message = re.sub(
        r"/[a-zA-Z0-9_/.-]*\.(py|js|json|yaml|toml)",
        "[FILE_PATH_REDACTED]",
        error_message,
    )
    error_message = re.sub(
        r"C:\\[a-zA-Z0-9_\\.-]*\.(py|js|json|yaml|toml)",
        "[FILE_PATH_REDACTED]",
        error_message,
    )

    # Remove potential user information
    error_message = re.sub(r"/Users/[^/\s]+", "/Users/[USER]", error_message)
    error_message = re.sub(r"/home/[^/\s]+", "/home/[USER]", error_message)
    error_message = re.sub(r"C:\\Users\\[^\\\s]+", r"C:\\Users\\[USER]", error_message)

    # Remove environment variables
    error_message = re.sub(r"[A-Z_]{3,}=[^\s]*", "[ENV_VAR_REDACTED]", error_message)

    return error_message


def execute_gemini_api(
    prompt: str, model_name: str, show_progress: bool = True
) -> dict:
    """Execute Gemini API directly with specified model - try this first before CLI fallback"""
    try:
        # Get API key using simplified discovery
        api_key = get_api_key()
        if not api_key:
            return {"success": False, "error": "No API key found"}

        import google.generativeai as genai

        if show_progress:
            print(f"🌟 Using API key: {api_key[:8]}...", file=sys.stderr)
            print(f"🌟 Making API call to {model_name}...", file=sys.stderr)

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        response = model.generate_content(prompt)

        if show_progress:
            print("✅ API call successful!", file=sys.stderr)

        return {"success": True, "output": response.text}

    except ImportError:
        if show_progress:
            print(
                "⚠️ google-generativeai not installed, using CLI fallback",
                file=sys.stderr,
            )
        return {"success": False, "error": "API library not available"}
    except Exception as e:
        # Sanitize error message to prevent sensitive information leakage
        error_message = str(e)
        # Remove potential API key patterns from error messages
        import re

        error_message = re.sub(
            r"AIzaSy[A-Za-z0-9_-]{33}", "[API_KEY_REDACTED]", error_message
        )
        error_message = re.sub(
            r"sk-[A-Za-z0-9_-]{32,}", "[API_KEY_REDACTED]", error_message
        )
        error_message = re.sub(
            r"Bearer [A-Za-z0-9_.-]{10,}", "[TOKEN_REDACTED]", error_message
        )

        if show_progress:
            print(
                f"⚠️ API call failed: {error_message}, using CLI fallback",
                file=sys.stderr,
            )
        return {"success": False, "error": error_message}


def execute_gemini_cli(
    prompt: str, model_name: Optional[str] = None, show_progress: bool = True
) -> Dict[str, Any]:
    """Execute Gemini CLI with timeout-protected real-time streaming output"""
    try:
        # Input validation
        if not isinstance(prompt, str) or len(prompt.strip()) == 0:
            return {
                "success": False,
                "error": "Invalid prompt: must be non-empty string",
            }

        # Check prompt size limit from config
        max_prompt_size = cfg.get_limit("max_prompt_size", 1000000)
        if len(prompt) > max_prompt_size:
            return {"success": False, "error": f"Prompt too large (max {max_prompt_size} bytes)"}

        # Validate model name if provided
        if model_name is not None:
            if not isinstance(model_name, str) or not model_name.strip():
                return {"success": False, "error": "Invalid model name"}
            # Basic sanitization: only allow alphanumeric, dots, hyphens
            if not all(c.isalnum() or c in ".-" for c in model_name):
                return {"success": False, "error": "Invalid model name characters"}

        # Build command args safely (no shell=True)
        cmd_args = ["gemini"]
        if model_name:
            cmd_args.extend(["-m", model_name])
        cmd_args.extend(["-p", prompt[:1000]])  # Limit prompt length for CLI

        # Get timeout from config
        timeout = cfg.get_timeout("cli_timeout", CLI_TIMEOUT)
        
        if show_progress:
            print("🔍 Starting timeout-protected Gemini CLI...", file=sys.stderr)
            print(f"📝 Prompt length: {len(prompt)} characters", file=sys.stderr)
            print(f"⏱️ Timeout: {timeout} seconds", file=sys.stderr)
            print("⏳ Streaming output:", file=sys.stderr)
            print("-" * 50, file=sys.stderr)

        # Set up environment
        env = {"PATH": os.environ.get("PATH", "")}
        if "GOOGLE_CLOUD_PROJECT" in os.environ:
            env["GOOGLE_CLOUD_PROJECT"] = os.environ["GOOGLE_CLOUD_PROJECT"]

        # Start process with streaming support
        process = subprocess.Popen(
            cmd_args,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            env=env,
        )

        # Set up threaded streaming with timeout protection
        output_queue = Queue()
        stop_event = threading.Event()

        # Start output streaming thread
        stream_thread = threading.Thread(
            target=stream_subprocess_output,
            args=(process, output_queue, stop_event),
            daemon=True,
        )
        stream_thread.start()

        output_lines = []
        start_time = time.time()
        last_progress_time = start_time
        timeout_reached = False

        # Process output with timeout protection
        while True:
            elapsed = time.time() - start_time

            # Check for timeout
            if elapsed > timeout:
                if show_progress:
                    print(
                        f"\n⚠️ Timeout reached after {timeout}s, terminating...",
                        file=sys.stderr,
                    )
                timeout_reached = True
                stop_event.set()
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    try:
                        process.kill()
                        process.wait(timeout=5)
                    except Exception:
                        pass
                break

            # Try to get output from queue (non-blocking)
            try:
                msg_type, data = output_queue.get(timeout=0.1)

                if msg_type == "stdout" and data:
                    output_lines.append(data)
                    if show_progress:
                        print(data.rstrip(), flush=True)
                    last_progress_time = time.time()

                elif msg_type == "error":
                    if show_progress:
                        print(f"\n⚠️ Stream error: {data}", file=sys.stderr)
                    break

                elif msg_type == "done":
                    if show_progress:
                        print("\n✅ Streaming completed", file=sys.stderr)
                    break

            except Empty:
                # No output received, continue waiting
                pass

            # Show progress periodically
            if show_progress and time.time() - last_progress_time > 15:
                elapsed_seconds = int(elapsed)
                remaining_seconds = max(0, timeout - elapsed_seconds)
                print(
                    f"\n⏱️ Progress: {elapsed_seconds}s elapsed, {remaining_seconds}s remaining",
                    file=sys.stderr,
                )
                last_progress_time = time.time()

            # Check if process finished naturally
            if process.poll() is not None:
                break

            time.sleep(0.1)  # Small delay to prevent tight loop

        # Clean up
        stop_event.set()
        stream_thread.join(timeout=1)

        # Get any remaining stderr
        stderr_output = ""
        try:
            if process.stderr:
                stderr_output = process.stderr.read()
        except Exception:
            pass

        full_output = "".join(output_lines)

        if show_progress:
            print("-" * 50, file=sys.stderr)
            if timeout_reached:
                print(f"⏰ Operation timed out after {timeout}s", file=sys.stderr)
            else:
                print("✅ Analysis complete!", file=sys.stderr)

        # Return results
        if timeout_reached:
            return {
                "success": False,
                "error": f"CLI timeout after {timeout} seconds",
                "partial_output": full_output,
            }
        elif process.returncode == 0:
            return {"success": True, "output": full_output}
        else:
            return {"success": False, "error": stderr_output or "CLI execution failed"}

    except subprocess.TimeoutExpired:
        timeout = cfg.get_timeout("cli_timeout", CLI_TIMEOUT)
        return {"success": False, "error": f"CLI timeout after {timeout} seconds"}
    except FileNotFoundError:
        return {"success": False, "error": "Gemini CLI not found in PATH"}
    except Exception as e:
        return {"success": False, "error": f"CLI execution error: {str(e)}"}


def _process_result_output(
    result: dict, convert_markdown: bool, show_progress: bool
) -> dict:
    """Process result output through markdown parser if enabled and available.

    Args:
        result: Result dictionary with 'success' and 'output' keys
        convert_markdown: Whether to convert markdown to plain text
        show_progress: Whether to show progress indicators

    Returns:
        dict: Processed result dictionary
    """
    if not result["success"] or not result.get("output"):
        return result

    # Skip conversion if disabled or markdown utils not available
    if not convert_markdown or not MARKDOWN_UTILS_AVAILABLE:
        if not convert_markdown and show_progress:
            print("🔧 Markdown conversion bypassed for debugging", file=sys.stderr)
        elif not MARKDOWN_UTILS_AVAILABLE and show_progress:
            print(
                "⚠️ Markdown utils not available, skipping conversion", file=sys.stderr
            )
        return result

    try:
        original_output = result["output"]
        if show_progress:
            print("📝 Converting markdown to plain text...", file=sys.stderr)

        # Convert markdown to plain text
        converted_output = markdown_to_text(original_output)

        # Update result with converted output
        result["output"] = converted_output

        if show_progress:
            original_len = len(original_output)
            converted_len = len(converted_output)
            print(
                f"✅ Markdown conversion complete: {original_len} → {converted_len} chars",
                file=sys.stderr,
            )

    except Exception as e:
        if show_progress:
            print(
                f"⚠️ Markdown conversion failed: {str(e)}, using original output",
                file=sys.stderr,
            )
        # Keep original output if conversion fails

    return result


def execute_gemini_smart(
    prompt: str,
    task_type: str = "quick_query",
    show_progress: bool = True,
    convert_markdown: bool = True,
) -> dict:
    """Smart execution: try API first, fall back to CLI if needed

    Args:
        prompt: Input prompt for the AI model
        task_type: Type of task for model selection
        show_progress: Whether to show progress indicators
        convert_markdown: Whether to convert markdown output to plain text (default: True)
    """

    # Get model from config instead of hardcoded assignments
    model_name = cfg.get_model(task_type, None)
    if not model_name:
        # Fallback to old logic for backward compatibility
        model_type = MODEL_ASSIGNMENTS.get(task_type, "flash")
        model_name = GEMINI_MODELS[model_type]
    
    # For backward compatibility, resolve nickname if it matches old pattern
    if model_name in GEMINI_MODELS:
        model_name = GEMINI_MODELS[model_name]

    if show_progress:
        print(f"📝 Task: {task_type}", file=sys.stderr)
        print(f"🤖 Selected model: {model_name}", file=sys.stderr)

    # Try API first using the new discovery approach
    api_key = get_api_key()
    if api_key:
        if show_progress:
            print("🚀 API key found, attempting API call...", file=sys.stderr)
        result = execute_gemini_api(prompt, model_name, show_progress)
        if result["success"]:
            # Process the result through markdown parser if enabled
            result = _process_result_output(result, convert_markdown, show_progress)
            return result
        if show_progress:
            print("🔄 API failed, falling back to CLI...", file=sys.stderr)
    else:
        if show_progress:
            print(
                "📝 No API key found in any location, using CLI directly",
                file=sys.stderr,
            )

    # Fallback to CLI
    result = execute_gemini_cli(prompt, model_name, show_progress)
    # Process the result through markdown parser if enabled
    result = _process_result_output(result, convert_markdown, show_progress)
    return result


def quick_query(query: str, context: str = "") -> None:
    """Ask Gemini CLI a quick question"""
    start_time = time.time()

    # Sanitize inputs to prevent prompt injection
    sanitized_query = sanitize_for_prompt(query, max_length=cfg.get_limit("max_prompt_size", 10000) // 100)
    sanitized_context = sanitize_for_prompt(context, max_length=cfg.get_limit("max_prompt_size", 50000) // 20)

    if sanitized_context:
        prompt = f"Context: {sanitized_context}\n\nQuestion: {sanitized_query}\n\nProvide a concise answer."
    else:
        prompt = f"Question: {sanitized_query}\n\nProvide a concise answer."

    result = execute_gemini_smart(prompt, "quick_query")

    elapsed_time = time.time() - start_time

    if result["success"]:
        print(f"\nQuery: {query}")
        print("=" * 50)
        print()
        print(result["output"])
        print()
        print("=" * 50)
        print(f"✅ Request completed ({elapsed_time:.1f}s)")
    else:
        print(f"Error: {result['error']}")


def analyze_code(file_path: str, analysis_type: str = "comprehensive") -> None:
    """Analyze a code file"""
    try:
        # Input validation
        if not isinstance(file_path, str) or not file_path.strip():
            print("Error: Invalid file path")
            return

        if not isinstance(analysis_type, str) or analysis_type not in [
            "comprehensive",
            "security",
            "performance",
            "architecture",
        ]:
            print("Error: Invalid analysis type")
            return

        # Enhanced security validation using new function
        is_valid, error_message, resolved_path = validate_file_security(file_path)
        if not is_valid or resolved_path is None:
            print(f"Error: {error_message}")
            return

        file_path = str(resolved_path)  # Use the resolved, validated path

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if len(content) > MAX_FILE_SIZE:
            print(
                f"Warning: File too large ({len(content)} bytes). Truncating to {MAX_FILE_SIZE} bytes..."
            )
            content = content[:MAX_FILE_SIZE]

        line_count = len(content.splitlines())
        if line_count > MAX_LINES:
            print(
                f"Warning: Too many lines ({line_count}). Truncating to {MAX_LINES} lines..."
            )
            lines = content.splitlines()[:MAX_LINES]
            content = "\n".join(lines)

        # Sanitize inputs to prevent prompt injection
        sanitized_content = sanitize_for_prompt(content, max_length=MAX_FILE_SIZE)
        # analysis_type is already validated above

        prompt = f"""Perform a {analysis_type} analysis of this code:

{sanitized_content}

Provide comprehensive analysis including:
1. Code structure and organization
2. Logic flow and algorithm efficiency
3. Security considerations and vulnerabilities
4. Performance implications and optimizations
5. Error handling and edge cases
6. Code quality and maintainability
7. Best practices compliance
8. Specific recommendations for improvements

Be thorough and provide actionable insights."""

        result = execute_gemini_smart(prompt, "analyze_code")

        if result["success"]:
            print(f"\nCode Analysis: {file_path}")
            print(f"Type: {analysis_type}")
            print(f"Lines: {line_count}")
            print("=" * 50)
            print()
            print(result["output"])
            print()
            print("=" * 50)
            print("✅ Request completed")
        else:
            print(f"Error: {result['error']}")

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"Error: {str(e)}")


def analyze_codebase(directory_path: str, analysis_scope: str = "all") -> None:
    """Analyze entire codebase - thin wrapper that calls real analyzer and feeds to Gemini"""
    start_time = time.time()

    # Input validation
    if not isinstance(directory_path, str) or not directory_path.strip():
        print("Error: Invalid directory path")
        return

    if not isinstance(analysis_scope, str) or analysis_scope not in [
        "structure",
        "security",
        "performance",
        "patterns",
        "all",
    ]:
        print("Error: Invalid analysis scope")
        return

    # Path security validation
    try:
        resolved_path = Path(directory_path).resolve()
        current_dir = Path.cwd().resolve()

        # Check if the resolved path is within current directory tree (prevent path traversal)
        try:
            resolved_path.relative_to(current_dir)
        except ValueError:
            print(
                f"Error: Directory access denied - path outside allowed directory: {directory_path}"
            )
            return

        if not resolved_path.exists():
            print(f"Error: Directory not found: {directory_path}")
            return

        if not resolved_path.is_dir():
            print(f"Error: Path is not a directory: {directory_path}")
            return

    except Exception as e:
        print(f"Error: Path validation failed: {str(e)}")
        return

    # Check if codebase analyzer is available
    if not CODEBASE_ANALYZER_AVAILABLE:
        print(
            "Error: Codebase analyzer not available. Please ensure helpers/codebase_analyzer.py is accessible."
        )
        return

    try:
        print(
            f"🔍 Starting comprehensive codebase analysis for: {directory_path}",
            file=sys.stderr,
        )
        print(f"📋 Analysis scope: {analysis_scope}", file=sys.stderr)
        print(
            "⏳ Step 1/3: Analyzing project structure and content...", file=sys.stderr
        )

        # Step 1: Call the real analyze_codebase function
        analysis_result = real_analyze_codebase(resolved_path, max_total_size=300_000)

        if analysis_result.error:
            print(f"Error during codebase analysis: {analysis_result.error}")
            return

        # Extract key information
        prompt_payload = analysis_result.prompt_payload
        project_report = analysis_result.project_report

        if not prompt_payload:
            print("Error: No content generated from codebase analysis")
            return

        print(
            f"✅ Step 1 complete: Analyzed {analysis_result.stats.files_analyzed} files",
            file=sys.stderr,
        )
        print(
            f"📊 Generated {len(prompt_payload):,} characters of structured content",
            file=sys.stderr,
        )
        print(
            f"⏱️ Analysis took {analysis_result.stats.total_time:.2f}s", file=sys.stderr
        )
        print("⏳ Step 2/3: Feeding to Gemini for AI analysis...", file=sys.stderr)

        # Step 2: Create analysis prompt based on scope
        analysis_prompt = f"""You are a senior software architect and code reviewer. Analyze this codebase comprehensively.

{prompt_payload}

## Analysis Requirements

Based on the scope '{analysis_scope}', provide detailed analysis covering:

1. **Architecture & Design Patterns**: Overall system design, patterns used, architectural decisions
2. **Code Quality & Maintainability**: Code organization, readability, documentation quality
3. **Security Analysis**: Potential vulnerabilities, security best practices, risk assessment
4. **Performance Considerations**: Bottlenecks, optimization opportunities, scalability issues
5. **Best Practices Compliance**: Following language/framework conventions, industry standards
6. **Dependencies & Integration**: External dependencies, integration points, potential risks
7. **Testing & Quality Assurance**: Test coverage, testing strategies, quality metrics
8. **Documentation & Developer Experience**: Code clarity, documentation completeness, onboarding ease

## Output Format

Provide a comprehensive report with:
- **Executive Summary**: Key findings and overall assessment
- **Detailed Analysis**: In-depth analysis for each area above
- **Actionable Recommendations**: Specific, prioritized improvement suggestions
- **Risk Assessment**: Potential issues and their impact levels
- **Implementation Roadmap**: Step-by-step improvement plan

Be thorough, specific, and provide actionable insights that a development team can implement."""

        # Step 3: Feed to Gemini and stream results
        result = execute_gemini_smart(analysis_prompt, "analyze_codebase")

        elapsed_time = time.time() - start_time

        if result["success"]:
            print("\n" + "=" * 80)
            print(f"🏗️ CODEBASE ANALYSIS REPORT: {resolved_path.name}")
            print(f"📋 Scope: {analysis_scope.upper()}")
            print(f"📊 Files Analyzed: {analysis_result.stats.files_analyzed}")
            print(f"📈 Total Lines: {analysis_result.structure.total_lines:,}")
            if analysis_result.structure.languages:
                primary_lang = max(
                    analysis_result.structure.languages.items(), key=lambda x: x[1]
                )[0]
                print(f"🔤 Primary Language: {primary_lang.title()}")
            print(f"⏱️ Analysis Time: {elapsed_time:.1f}s")
            print("=" * 80)
            print()

            # Step 3: Stream the Gemini analysis result
            print("✅ Step 3/3: AI Analysis Complete!\n", file=sys.stderr)
            print(result["output"])
            print()
            print("=" * 80)
            print(f"✅ Comprehensive analysis completed in {elapsed_time:.1f}s")
            print(
                f"📋 Report generated from {len(prompt_payload):,} characters of codebase content"
            )
            print("=" * 80)
        else:
            print(f"\nError during AI analysis: {result['error']}")
            print("\n" + "=" * 50)
            print("📋 RAW CODEBASE ANALYSIS (Fallback)")
            print("=" * 50)
            print()
            # Fallback: show the project report if Gemini fails
            if project_report:
                import json

                print(json.dumps(project_report, indent=2))
            print()
            print("=" * 50)

    except Exception as e:
        print(f"Error during codebase analysis: {str(e)}")
        print(f"Details: {type(e).__name__}: {str(e)}", file=sys.stderr)


def main() -> None:
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python gemini_helper.py query 'your question here' [context]")
        print("  python gemini_helper.py analyze file_path [analysis_type]")
        print("  python gemini_helper.py codebase directory_path [scope]")
        return

    command = sys.argv[1].lower()

    if command == "query":
        if len(sys.argv) < 3:
            print("Error: Query text required")
            return
        query_text = sys.argv[2]
        context = sys.argv[3] if len(sys.argv) > 3 else ""
        quick_query(query_text, context)

    elif command == "analyze":
        if len(sys.argv) < 3:
            print("Error: File path required")
            return
        file_path = sys.argv[2]
        analysis_type = sys.argv[3] if len(sys.argv) > 3 else "comprehensive"
        analyze_code(file_path, analysis_type)

    elif command == "codebase":
        if len(sys.argv) < 3:
            print("Error: Directory path required")
            return
        directory_path = sys.argv[2]
        scope = sys.argv[3] if len(sys.argv) > 3 else "all"
        analyze_codebase(directory_path, scope)

    else:
        print(f"Unknown command: {command}")
        print("Available commands: query, analyze, codebase")


def split_into_chunks(text: str, chunk_size: int = 50) -> list[str]:
    """Split text into chunks for streaming display"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def execute_gemini_smart_with_progress(
    prompt: str, task_type: str = "quick_query"
) -> dict:
    """Execute Gemini with beautiful streaming progress indicators"""
    if not PROGRESS_AVAILABLE:
        return execute_gemini_smart(prompt, task_type, show_progress=True)

    progress = create_spinner_progress("🤖 Gemini")

    try:
        progress.start("Processing request")
        result = execute_gemini_smart(prompt, task_type, show_progress=False)

        if result["success"]:
            # Stream response in chunks for nice display
            chunks = split_into_chunks(result["output"], chunk_size=60)
            for chunk in chunks:
                progress.stream_chunk(chunk + " ", end="")
                time.sleep(0.05)  # Small delay for nice streaming effect

            progress.stream_chunk("\n")
            progress.complete("Request completed")
        else:
            progress.stop(f"Error: {result['error']}")

        return result

    except Exception as e:
        progress.stop(f"Unexpected error: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    main()
