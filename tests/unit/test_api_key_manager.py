#!/usr/bin/env python3
"""
Comprehensive unit tests for the API Key Manager module.

Tests API key discovery strategies, validation, and environment detection
as specified in task 1.10 requirements.
"""

import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch
import unittest

# Add project root to path for imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from claude_gemini_mcp.helpers.api_key_manager import (
    MIN_API_KEY_LENGTH,
    add_shared_mcp_path,
    get_api_key,
    is_api_key_available,
    _validate_api_key,
    _get_from_env_var,
    _extract_mcp_api_key,
    _get_from_json_config,
    _get_from_env_file,
)


class TestAPIKeyValidation(unittest.TestCase):
    """Test API key validation functionality."""

    def test_validate_api_key_valid_key(self):
        """Test validation of valid API keys."""
        valid_keys = [
            "AIzaSy1234567890123456789012345678901234567890",  # Google API key format
            "sk-1234567890123456789012345678901234567890",      # OpenAI-style key
            "test-api-key-1234567890",                          # Test key format
            "a" * (MIN_API_KEY_LENGTH + 1),                     # Just above minimum length
        ]

        for key in valid_keys:
            with self.subTest(key=key[:20] + "..."):
                result = _validate_api_key(key)
                self.assertEqual(result, key.strip())

    def test_validate_api_key_invalid_key(self):
        """Test validation of invalid API keys."""
        invalid_keys = [
            None,                           # None value
            "",                            # Empty string
            "   ",                         # Whitespace only
            "short",                       # Too short
            "a" * (MIN_API_KEY_LENGTH - 1), # Just below minimum length
        ]

        for key in invalid_keys:
            with self.subTest(key=str(key)):
                result = _validate_api_key(key)
                self.assertIsNone(result)

    def test_validate_api_key_whitespace_trimming(self):
        """Test that validation properly trims whitespace."""
        key_with_whitespace = "  AIzaSy1234567890123456789012345678901234567890  "
        expected = "AIzaSy1234567890123456789012345678901234567890"

        result = _validate_api_key(key_with_whitespace)
        self.assertEqual(result, expected)


class TestEnvironmentVariableDiscovery(unittest.TestCase):
    """Test API key discovery from environment variables."""

    def test_get_from_env_var_success(self):
        """Test successful API key retrieval from environment variable."""
        test_key = "test-api-key-1234567890"

        with patch.dict(os.environ, {"GOOGLE_API_KEY": test_key}):
            result = _get_from_env_var()
            self.assertEqual(result, test_key)

    def test_get_from_env_var_missing(self):
        """Test handling when environment variable is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = _get_from_env_var()
            self.assertIsNone(result)

    def test_get_from_env_var_invalid_key(self):
        """Test handling of invalid key in environment variable."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "short"}):
            result = _get_from_env_var()
            self.assertIsNone(result)

    def test_get_from_env_var_whitespace(self):
        """Test trimming of whitespace in environment variable."""
        test_key = "test-api-key-1234567890"

        with patch.dict(os.environ, {"GOOGLE_API_KEY": f"  {test_key}  "}):
            result = _get_from_env_var()
            self.assertEqual(result, test_key)


class TestJSONConfigDiscovery(unittest.TestCase):
    """Test API key discovery from JSON configuration files."""

    def test_extract_mcp_api_key_success(self):
        """Test successful extraction from MCP config structure."""
        config = {
            "mcpServers": {
                "gemini-mcp": {
                    "env": {
                        "GOOGLE_API_KEY": "test-api-key-1234567890"
                    }
                }
            }
        }

        result = _extract_mcp_api_key(config)
        self.assertEqual(result, "test-api-key-1234567890")

    def test_extract_mcp_api_key_missing_structure(self):
        """Test handling of missing structure in config."""
        test_cases = [
            {},                                              # Empty config
            {"mcpServers": {}},                             # Missing gemini-mcp
            {"mcpServers": {"gemini-mcp": {}}},            # Missing env
            {"mcpServers": {"gemini-mcp": {"env": {}}}},   # Missing GOOGLE_API_KEY
        ]

        for config in test_cases:
            with self.subTest(config=str(config)):
                result = _extract_mcp_api_key(config)
                self.assertIsNone(result)

    def test_get_from_json_config_success(self):
        """Test successful JSON config file reading."""
        config_data = {
            "mcpServers": {
                "gemini-mcp": {
                    "env": {"GOOGLE_API_KEY": "test-api-key-1234567890"}
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
                result = _get_from_json_config(Path("/fake/path"))
                self.assertEqual(result, "test-api-key-1234567890")

    def test_get_from_json_config_file_not_exists(self):
        """Test handling when JSON config file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = _get_from_json_config(Path("/fake/path"))
            self.assertIsNone(result)

    def test_get_from_json_config_invalid_json(self):
        """Test handling of invalid JSON in config file."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                result = _get_from_json_config(Path("/fake/path"))
                self.assertIsNone(result)

    def test_get_from_json_config_permission_error(self):
        """Test handling of permission errors when reading config."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=PermissionError()):
                result = _get_from_json_config(Path("/fake/path"))
                self.assertIsNone(result)

    def test_get_from_json_config_invalid_key(self):
        """Test handling of invalid API key in JSON config."""
        config_data = {
            "mcpServers": {
                "gemini-mcp": {
                    "env": {"GOOGLE_API_KEY": "short"}  # Too short
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
                result = _get_from_json_config(Path("/fake/path"))
                self.assertIsNone(result)


class TestEnvFileDiscovery(unittest.TestCase):
    """Test API key discovery from .env files."""

    def test_get_from_env_file_success(self):
        """Test successful API key retrieval from .env file."""
        env_content = "GOOGLE_API_KEY=test-api-key-1234567890\nOTHER_VAR=value"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=env_content)):
                result = _get_from_env_file()
                self.assertEqual(result, "test-api-key-1234567890")

    def test_get_from_env_file_quoted_values(self):
        """Test handling of quoted values in .env file."""
        test_cases = [
            'GOOGLE_API_KEY="test-api-key-1234567890"',     # Double quotes
            "GOOGLE_API_KEY='test-api-key-1234567890'",     # Single quotes
            'GOOGLE_API_KEY="test-api-key-1234567890"\n',   # With newline
        ]

        for env_content in test_cases:
            with self.subTest(content=env_content):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("builtins.open", mock_open(read_data=env_content)):
                        result = _get_from_env_file()
                        self.assertEqual(result, "test-api-key-1234567890")

    def test_get_from_env_file_not_exists(self):
        """Test handling when .env file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = _get_from_env_file()
            self.assertIsNone(result)

    def test_get_from_env_file_permission_error(self):
        """Test handling of permission errors when reading .env file."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=PermissionError()):
                result = _get_from_env_file()
                self.assertIsNone(result)

    def test_get_from_env_file_missing_key(self):
        """Test handling when GOOGLE_API_KEY is not in .env file."""
        env_content = "OTHER_VAR=value\nANOTHER_VAR=another_value"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=env_content)):
                result = _get_from_env_file()
                self.assertIsNone(result)

    def test_get_from_env_file_invalid_key(self):
        """Test handling of invalid API key in .env file."""
        env_content = "GOOGLE_API_KEY=short"  # Too short

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=env_content)):
                result = _get_from_env_file()
                self.assertIsNone(result)


class TestFallbackChainStrategy(unittest.TestCase):
    """Test the complete fallback chain strategy."""

    def test_get_api_key_env_var_priority(self):
        """Test that environment variable has highest priority."""
        env_key = "env-api-key-1234567890"
        config_key = "config-api-key-1234567890"

        with patch.dict(os.environ, {"GOOGLE_API_KEY": env_key}):
            with patch("claude_gemini_mcp.helpers.api_key_manager._get_from_json_config", return_value=config_key):
                result = get_api_key()
                self.assertEqual(result, env_key)

    def test_get_api_key_claude_code_config_fallback(self):
        """Test fallback to Claude Code MCP configuration."""
        config_key = "config-api-key-1234567890"

        with patch.dict(os.environ, {}, clear=True):
            with patch("claude_gemini_mcp.helpers.api_key_manager._get_from_json_config") as mock_config:
                # First call (claude-code) returns the key, second call (claude-desktop) not called
                mock_config.return_value = config_key

                result = get_api_key()
                self.assertEqual(result, config_key)
                self.assertEqual(mock_config.call_count, 1)

    def test_get_api_key_claude_desktop_config_fallback(self):
        """Test fallback to Claude Desktop configuration."""
        config_key = "desktop-config-api-key-1234567890"

        with patch.dict(os.environ, {}, clear=True):
            with patch("claude_gemini_mcp.helpers.api_key_manager._get_from_json_config") as mock_config:
                # First call (claude-code) returns None, second call (claude-desktop) returns key
                mock_config.side_effect = [None, config_key]

                result = get_api_key()
                self.assertEqual(result, config_key)
                self.assertEqual(mock_config.call_count, 2)

    def test_get_api_key_env_file_fallback(self):
        """Test fallback to project .env file."""
        env_file_key = "env-file-api-key-1234567890"

        with patch.dict(os.environ, {}, clear=True):
            with patch("claude_gemini_mcp.helpers.api_key_manager._get_from_json_config", return_value=None):
                with patch("claude_gemini_mcp.helpers.api_key_manager._get_from_env_file", return_value=env_file_key):
                    result = get_api_key()
                    self.assertEqual(result, env_file_key)

    def test_get_api_key_no_key_found(self):
        """Test when no API key is found in any location."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("claude_gemini_mcp.helpers.api_key_manager._get_from_json_config", return_value=None):
                with patch("claude_gemini_mcp.helpers.api_key_manager._get_from_env_file", return_value=None):
                    result = get_api_key()
                    self.assertIsNone(result)

    def test_is_api_key_available_true(self):
        """Test is_api_key_available returns True when key exists."""
        with patch("claude_gemini_mcp.helpers.api_key_manager.get_api_key", return_value="test-key-1234567890"):
            result = is_api_key_available()
            self.assertTrue(result)

    def test_is_api_key_available_false(self):
        """Test is_api_key_available returns False when no key exists."""
        with patch("claude_gemini_mcp.helpers.api_key_manager.get_api_key", return_value=None):
            result = is_api_key_available()
            self.assertFalse(result)


class TestSharedMCPPathDetection(unittest.TestCase):
    """Test shared MCP environment path detection and configuration."""

    @patch("sys.path")
    @patch("pathlib.Path.home")
    def test_add_shared_mcp_path_env_info_success(self, mock_home, mock_sys_path):
        """Test successful path addition from env-info.json."""
        mock_home.return_value = Path("/home/user")
        env_info_data = {"site_packages_path": "/path/to/site-packages"}

        # Create a mock path that behaves correctly
        def mock_path_exists(self):
            path_str = str(self)
            return (
                "env-info.json" in path_str or
                "site-packages" in path_str or
                "google/generativeai" in path_str
            )

        with patch.object(Path, "exists", mock_path_exists):
            with patch("builtins.open", mock_open(read_data=json.dumps(env_info_data))):
                result = add_shared_mcp_path()

                self.assertEqual(result, "/path/to/site-packages")
                mock_sys_path.insert.assert_called_once_with(0, "/path/to/site-packages")

    @patch("sys.path")
    @patch("pathlib.Path.home")
    @patch("platform.python_version")
    def test_add_shared_mcp_path_fallback_detection(self, mock_python_version, mock_home, mock_sys_path):
        """Test fallback path detection when env-info.json fails."""
        mock_home.return_value = Path("/home/user")
        mock_python_version.return_value = "3.12.1"

        def mock_path_exists(self):
            path_str = str(self)
            return (
                "python3.12/site-packages" in path_str or
                "google/generativeai" in path_str
            )

        with patch.object(Path, "exists", mock_path_exists):
            with patch("builtins.open", side_effect=FileNotFoundError):  # env-info.json doesn't exist

                result = add_shared_mcp_path()

                self.assertIsNotNone(result)
                self.assertTrue(result.endswith("site-packages"))
                mock_sys_path.insert.assert_called_once()

    @patch("pathlib.Path.home")
    def test_add_shared_mcp_path_no_path_found(self, mock_home):
        """Test when no shared MCP path is found."""
        mock_home.return_value = Path("/home/user")

        with patch("pathlib.Path.exists", return_value=False):
            with patch("builtins.open", side_effect=FileNotFoundError):
                result = add_shared_mcp_path()
                self.assertIsNone(result)

    @patch("pathlib.Path.home")
    def test_add_shared_mcp_path_json_error(self, mock_home):
        """Test handling of JSON errors in env-info.json."""
        mock_home.return_value = Path("/home/user")

        def mock_path_exists(self):
            path_str = str(self)
            return "env-info.json" in path_str  # Only env-info.json exists, no fallback paths

        with patch.object(Path, "exists", mock_path_exists):
            # Simulate JSON decode error
            with patch("builtins.open", mock_open(read_data="invalid json")):
                result = add_shared_mcp_path()
                # Should fall back to manual detection (which will return None in this test)
                self.assertIsNone(result)

    @patch("sys.path")
    @patch("pathlib.Path.home")
    def test_add_shared_mcp_path_missing_generativeai(self, mock_home, mock_sys_path):
        """Test path rejection when google-generativeai is not found."""
        mock_home.return_value = Path("/home/user")
        env_info_data = {"site_packages_path": "/path/to/site-packages"}

        def mock_path_exists(self):
            path_str = str(self)
            # env-info.json and site-packages exist but google-generativeai doesn't
            return (
                "env-info.json" in path_str or
                ("site-packages" in path_str and "google/generativeai" not in path_str)
            )

        with patch.object(Path, "exists", mock_path_exists):
            with patch("builtins.open", mock_open(read_data=json.dumps(env_info_data))):
                result = add_shared_mcp_path()

                # Should not add path when google-generativeai is missing
                self.assertIsNone(result)
                mock_sys_path.insert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
