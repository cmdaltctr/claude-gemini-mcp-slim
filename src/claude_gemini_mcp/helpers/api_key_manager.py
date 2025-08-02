#!/usr/bin/env python3
"""
API Key Manager Module - Centralized API Key Discovery and Management

This module handles all Google API key discovery operations using a fallback chain
strategy to locate valid API keys from multiple sources. It provides a clean,
secure interface for API key management across the application.

Key Features:
- Multi-source API key discovery with intelligent fallback
- Secure API key validation and sanitization
- Dynamic MCP environment detection and integration
- Comprehensive error handling and logging
- Type-safe interfaces with full documentation

Fallback Chain Strategy:
1. Environment variables (GOOGLE_API_KEY)
2. Claude Code MCP configuration (~/.config/claude-code/mcp_config.json)
3. Claude Desktop configuration (~/Library/Application Support/Claude/claude_desktop_config.json)
4. Project .env files (./gemini/.env)

Usage:
    from claude_gemini_mcp.helpers.api_key_manager import get_api_key, is_api_key_available

    # Get API key with automatic discovery
    api_key = get_api_key()

    # Check availability without retrieval
    if is_api_key_available():
        print("API key is available")
"""

import json
import os
import platform
import sys
from pathlib import Path
from typing import Optional

# Constants for API key discovery
MIN_API_KEY_LENGTH = 10

CONFIG_PATHS = {
    "claude_code": Path.home() / ".config" / "claude-code" / "mcp_config.json",
    "claude_desktop": Path.home()
    / "Library"
    / "Application Support"
    / "Claude"
    / "claude_desktop_config.json",
}


def add_shared_mcp_path() -> Optional[str]:
    """Dynamically detect and add shared MCP environment to Python path

    This function searches for a shared MCP environment containing the
    google-generativeai package and adds it to the Python path if found.
    It first tries to read from installation.sh created env-info.json,
    then falls back to common location patterns.

    Returns:
        Optional[str]: Path to the shared MCP environment site-packages directory
                      if found and successfully added to sys.path, None otherwise

    Note:
        This function modifies sys.path when a valid shared environment is found.
        It performs validation to ensure the google-generativeai package is
        actually available before adding the path.
    """
    # First, try to read from installation.sh created env-info.json
    try:
        env_info_path = Path.home() / "mcp-servers" / "env-info.json"
        if env_info_path.exists():
            with open(env_info_path, "r", encoding="utf-8") as f:
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


def _validate_api_key(api_key: Optional[str]) -> Optional[str]:
    """Validate and return trimmed API key if valid

    Args:
        api_key: Raw API key string that may contain whitespace or be None/empty

    Returns:
        Optional[str]: Trimmed API key if valid (length > MIN_API_KEY_LENGTH),
                      None if invalid or too short

    Note:
        This function only validates length and trims whitespace.
        It does not validate the actual API key format or test connectivity.
    """
    if api_key and len(api_key.strip()) > MIN_API_KEY_LENGTH:
        return api_key.strip()
    return None


def _get_from_env_var() -> Optional[str]:
    """Get API key from environment variable

    Attempts to retrieve the Google API key from the GOOGLE_API_KEY
    environment variable, with automatic validation.

    Returns:
        Optional[str]: Valid API key if found in environment, None otherwise

    Note:
        This is typically the highest priority source in the fallback chain
        as environment variables are commonly used in deployment environments.
    """
    return _validate_api_key(os.getenv("GOOGLE_API_KEY"))


def _extract_mcp_api_key(config: dict) -> Optional[str]:
    """Extract API key from MCP config structure

    Parses the nested MCP configuration structure to extract the Google API key
    from the standard mcpServers.gemini-mcp.env.GOOGLE_API_KEY path.

    Args:
        config: Parsed JSON configuration dictionary from MCP config file

    Returns:
        Optional[str]: API key if found in the expected structure, None otherwise

    Note:
        This function safely navigates the nested dictionary structure using
        .get() calls to prevent KeyError exceptions.
    """
    return (
        config.get("mcpServers", {})
        .get("gemini-mcp", {})
        .get("env", {})
        .get("GOOGLE_API_KEY")
    )


def _get_from_json_config(file_path: Path) -> Optional[str]:
    """Read API key from JSON config file

    Attempts to read and parse a JSON configuration file, then extract
    the API key using the MCP configuration structure.

    Args:
        file_path: Path to the JSON configuration file to read

    Returns:
        Optional[str]: Valid API key if found and valid, None if file doesn't exist,
                      is malformed, or doesn't contain a valid API key

    Note:
        This function handles multiple potential exceptions silently:
        - FileNotFoundError: File doesn't exist
        - json.JSONDecodeError: Invalid JSON format
        - PermissionError: Insufficient permissions to read file
    """
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return _validate_api_key(_extract_mcp_api_key(config))
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        pass
    return None


def _get_from_env_file() -> Optional[str]:
    """Read API key from project .env file

    Searches for a project-specific .env file in the ./gemini/.env path
    and attempts to parse the GOOGLE_API_KEY variable from it.

    Returns:
        Optional[str]: Valid API key if found in .env file, None otherwise

    Note:
        This function parses .env files manually by searching for lines that
        start with "GOOGLE_API_KEY=" and handles both quoted and unquoted values.
        It gracefully handles file access errors.
    """
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
    """Get API key using simplified discovery approach with fallback chain

    This is the main entry point for API key discovery. It tries multiple
    sources in priority order and returns the first valid API key found.

    Fallback chain priority:
    1. Environment variables (GOOGLE_API_KEY) - Highest priority
    2. Claude Code MCP configuration file
    3. Claude Desktop configuration file
    4. Project .env file - Lowest priority

    Returns:
        Optional[str]: First valid API key found in the fallback chain,
                      None if no valid API key is found from any source

    Usage:
        api_key = get_api_key()
        if api_key:
            # Use the API key for authentication
            configure_genai(api_key)
        else:
            print("No API key found - falling back to CLI")

    Note:
        This function does not cache results - each call performs a fresh
        discovery process. For performance-critical code that calls this
        frequently, consider caching the result.
    """
    # Define discovery strategies in priority order
    strategies = [
        _get_from_env_var,
        lambda: _get_from_json_config(CONFIG_PATHS["claude_code"]),
        lambda: _get_from_json_config(CONFIG_PATHS["claude_desktop"]),
        _get_from_env_file,
    ]

    # Try each strategy until one succeeds
    for strategy in strategies:
        if api_key := strategy():
            return api_key

    return None


def is_api_key_available() -> bool:
    """Check if valid API key is available without retrieving it

    This function performs the same discovery process as get_api_key()
    but only returns whether a valid key exists, without returning the
    actual key value. Useful for availability checks without exposing
    sensitive data.

    Returns:
        bool: True if a valid API key is available from any source,
              False if no valid API key can be found

    Usage:
        if is_api_key_available():
            print("API key detected - API calls will be available")
        else:
            print("No API key found - will use CLI fallback")

    Note:
        This is essentially a wrapper around get_api_key() that returns
        a boolean instead of the actual key value. It has the same
        performance characteristics.
    """
    return get_api_key() is not None


# Initialize shared MCP environment detection
def _initialize_shared_mcp_environment() -> None:
    """Initialize shared MCP environment detection and logging

    This function is called automatically when the module is imported.
    It attempts to detect and configure shared MCP environments, adding
    appropriate paths to sys.path and logging the results.

    Note:
        This function is called automatically during module import and
        should not be called directly by user code.
    """
    shared_path = add_shared_mcp_path()
    if shared_path:
        print(f"🔗 Using shared MCP environment: {shared_path}", file=sys.stderr)


# Automatically initialize shared MCP environment when module is imported
_initialize_shared_mcp_environment()
