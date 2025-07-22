import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional

from claude_gemini_mcp.config import get_config

cfg = get_config()


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
        allowed_extensions = set(
            cfg.get_raw_config()
            .get("security", {})
            .get(
                "allowed_extensions",
                [
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
                ],
            )
        )
        if resolved_path.suffix.lower() not in allowed_extensions:
            return False, f"File type not supported: {resolved_path.suffix}", None

        # Check file size before processing
        max_size = cfg.get_limit("max_file_size", 81920)
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
        r"/[a-zA-Z0-9_/.-]*\\.(py|js|json|yaml|toml)",
        "[FILE_PATH_REDACTED]",
        error_message,
    )
    error_message = re.sub(
        r"C:\\[a-zA-Z0-9_\\.-]*\\.(py|js|json|yaml|toml)",
        "[FILE_PATH_REDACTED]",
        error_message,
    )

    # Remove potential user information
    error_message = re.sub(r"/Users/[^/\\s]+", "/Users/[USER]", error_message)
    error_message = re.sub(r"/home/[^/\\s]+", "/home/[USER]", error_message)
    error_message = re.sub(r"C:\\Users\\[^\\\\s]+", r"C:\\Users\\[USER]", error_message)

    # Remove environment variables
    error_message = re.sub(r"[A-Z_]{3,}=[^\\s]*", "[ENV_VAR_REDACTED]", error_message)

    return error_message
