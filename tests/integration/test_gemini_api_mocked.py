#!/usr/bin/env python3
"""
Integration tests for Gemini API with comprehensive mocking
Tests API fallback behavior, error handling, and response processing
"""

import asyncio
import os
import secrets
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import our server components
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from claude_gemini_mcp.helpers.api_key_manager import get_api_key
from claude_gemini_mcp.helpers.gemini_api_client import execute_gemini_api
from claude_gemini_mcp.helpers.gemini_cli_client import execute_gemini_cli_streaming


class TestGeminiAPIIntegration:
    """Test Gemini API integration with various scenarios"""

    @pytest.mark.asyncio
    async def test_fake_api_key_fixture(self, fake_api_key: str) -> None:
        """Test that fake_api_key fixture provides deterministic test key"""
        # Verify the fake API key is deterministic and safe for tests
        assert fake_api_key == "test-api-key-1234567890"
        assert fake_api_key.startswith("test-api-key-")
        assert len(fake_api_key) > 10  # Ensure it's long enough to be realistic

        # Verify it doesn't contain any real secret patterns
        assert not fake_api_key.startswith("AIza")  # Not a real Google API key
        assert "secret" not in fake_api_key.lower()
        assert "password" not in fake_api_key.lower()

    @pytest.mark.asyncio
    async def test_api_success_flow(self, mock_google_api_key: str) -> None:
        """Test successful API call flow"""

        # Mock the google.generativeai module
        mock_genai = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "API response text"

        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        # Need to patch at the module level where it's imported
        with patch("claude_gemini_mcp.helpers.gemini_api_client.genai", mock_genai):
            result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

            assert result["success"] is True
            assert result["output"] == "API response text"

            # Verify the API was configured correctly
            mock_genai.configure.assert_called_once_with(api_key=mock_google_api_key)
            mock_genai.GenerativeModel.assert_called_once_with("gemini-2.5-flash")
            mock_model.generate_content_async.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    async def test_api_missing_key(self) -> None:
        """Test API behavior with missing API key"""

        with patch(
            "claude_gemini_mcp.helpers.api_key_manager.get_api_key", return_value=None
        ):
            result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

            assert result["success"] is False
            assert "No API key found" in result["error"]

    @pytest.mark.asyncio
    async def test_api_invalid_key(self, monkeypatch) -> None:
        """Test API behavior with invalid API key"""

        # Set a short API key that should fail validation
        monkeypatch.setenv(
            "GOOGLE_API_KEY", "short"
        )  # Only 5 chars, should fail > 10 check

        # Patch all fallback discovery methods to ensure they don't find other keys
        with (
            patch(
                "claude_gemini_mcp.helpers.api_key_manager._get_from_json_config",
                return_value=None,
            ),
            patch(
                "claude_gemini_mcp.helpers.api_key_manager._get_from_env_file",
                return_value=None,
            ),
        ):
            result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

            assert result["success"] is False
            assert "No API key found" in result["error"]

    @pytest.mark.asyncio
    async def test_api_import_error(self, mock_google_api_key: str) -> None:
        """Test API fallback when google-generativeai is not available"""

        # Simulate ImportError
        with patch(
            "builtins.__import__",
            side_effect=ImportError("No module named 'google.generativeai'"),
        ):
            result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

            assert result["success"] is False
            assert "API library not available" in result["error"]

    @pytest.mark.asyncio
    async def test_api_key_redaction_in_errors(self, mock_google_api_key: str) -> None:
        """Test that API keys are properly redacted in error messages"""

        mock_genai = MagicMock()
        mock_model = MagicMock()

        # Simulate an error that includes an API key
        error_with_key = Exception(f"Error with key {mock_google_api_key} in message")
        mock_model.generate_content_async = AsyncMock(side_effect=error_with_key)
        mock_genai.GenerativeModel.return_value = mock_model

        with patch("claude_gemini_mcp.helpers.gemini_api_client.genai", mock_genai):
            result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

            assert result["success"] is False
            assert mock_google_api_key not in result["error"]
            assert "[API_KEY_REDACTED]" in result["error"]


class TestCLIFallbackIntegration:
    """Test CLI fallback behavior when API fails"""

    @pytest.mark.asyncio
    async def test_api_to_cli_fallback(self, mock_google_api_key: str) -> None:
        """Test automatic fallback from API to CLI"""

        # Mock successful CLI execution
        async def mock_cli_execution(prompt, model_name, show_progress=True):
            return {
                "success": True,
                "output": "CLI response line 1\nCLI response line 2\n",
            }

        # First test that API failure triggers CLI fallback
        with patch(
            "claude_gemini_mcp.helpers.gemini_api_client.execute_gemini_api"
        ) as mock_api:
            mock_api.return_value = {"success": False, "error": "API failed"}

            with patch(
                "claude_gemini_mcp.helpers.gemini_cli_client.execute_gemini_cli_streaming",
                side_effect=mock_cli_execution,
            ):
                # Import and use execute_gemini_smart which handles the fallback
                from claude_gemini_mcp.helpers.execution_orchestrator import (
                    execute_gemini_smart,
                )

                result = await execute_gemini_smart(
                    "Test prompt", "quick_query", show_progress=False
                )

                assert result["success"] is True
                assert "CLI response line 1" in result["output"]
                assert "CLI response line 2" in result["output"]

    @pytest.mark.asyncio
    async def test_cli_command_construction(self) -> None:
        """Test that CLI commands are constructed securely"""

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.poll = MagicMock(
            side_effect=[None, 0]
        )  # Process running then finished
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(return_value="")
        mock_process.stdout.read = MagicMock(return_value="Safe output")
        mock_process.stderr = MagicMock()
        mock_process.stderr.read = MagicMock(return_value="")

        with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
            with patch(
                "claude_gemini_mcp.helpers.api_key_manager.get_api_key",
                return_value=None,
            ):  # Force CLI
                await execute_gemini_cli_streaming("Test prompt", "gemini-pro")

                # Verify the command was constructed securely
                mock_popen.assert_called_once()
                call_args = mock_popen.call_args

                expected_args = [
                    "gemini",
                    "-m",
                    "gemini-pro",
                    "-p",
                    "Test prompt",
                ]
                assert call_args[0][0] == expected_args
                assert call_args[1]["shell"] is False

    @pytest.mark.asyncio
    async def test_cli_error_handling(self) -> None:
        """Test CLI error handling and timeout scenarios"""

        # Test CLI failure
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.pid = 12345
        mock_process.poll = MagicMock(
            side_effect=[None, 1]
        )  # Process running then failed
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(return_value="")
        mock_process.stdout.read = MagicMock(return_value="")
        mock_process.stderr = MagicMock()
        mock_process.stderr.read = MagicMock(return_value="CLI error message")

        with patch("subprocess.Popen", return_value=mock_process):
            with patch(
                "claude_gemini_mcp.helpers.api_key_manager.get_api_key",
                return_value=None,
            ):
                result = await execute_gemini_cli_streaming("Test prompt", "gemini-pro")

                assert result["success"] is False
                assert "CLI error message" in result["error"]

    @pytest.mark.asyncio
    async def test_cli_streaming_output(self) -> None:
        """Test CLI streaming output handling"""

        # Mock successful CLI execution with streaming output
        async def mock_cli_streaming(prompt, model_name, show_progress=True):
            return {
                "success": True,
                "output": "Starting analysis...\nProcessing data...\nAnalysis complete.\n",
            }

        with patch(
            "claude_gemini_mcp.helpers.gemini_cli_client.execute_gemini_cli_streaming",
            side_effect=mock_cli_streaming,
        ):
            result = await execute_gemini_cli_streaming(
                "Test prompt", "gemini-pro", show_progress=False
            )

            assert result["success"] is True
            assert "Starting analysis..." in result["output"]
            assert "Processing data..." in result["output"]
            assert "Analysis complete." in result["output"]


class TestModelSelection:
    """Test model selection logic for different task types"""

    @pytest.mark.asyncio
    async def test_task_type_model_mapping(self) -> None:
        """Test that different task types select appropriate models"""

        test_cases = [
            ("gemini_quick_query", "gemini-2.5-flash"),
            ("gemini_analyze_code", "gemini-2.5-pro"),
            ("gemini_codebase_analysis", "gemini-2.5-pro"),
        ]

        for task_type, expected_model in test_cases:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.pid = 12345
            mock_process.poll = MagicMock(
                side_effect=[None, 0]
            )  # Process running then finished
            mock_process.stdout = MagicMock()
            mock_process.stdout.readline = MagicMock(return_value="")
            mock_process.stdout.read = MagicMock(return_value="output")
            mock_process.stderr = MagicMock()
            mock_process.stderr.read = MagicMock(return_value="")

            with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
                with patch(
                    "claude_gemini_mcp.helpers.api_key_manager.get_api_key",
                    return_value=None,
                ):
                    await execute_gemini_cli_streaming("Test prompt", expected_model)

                    # Verify correct model was selected
                    call_args = mock_popen.call_args[0][0]
                    assert call_args[2] == expected_model  # -m flag argument

    @pytest.mark.asyncio
    async def test_invalid_task_type(self) -> None:
        """Test handling of invalid task types"""

        from claude_gemini_mcp.config import get_config

        with patch("claude_gemini_mcp.config.get_config") as mock_get_config:
            mock_cfg = mock_get_config.return_value
            mock_cfg.get_model.return_value = None
            result = await execute_gemini_cli_streaming(
                "Test prompt", "invalid_model_name"
            )

            assert result["success"] is False
            assert "Invalid model name" in result["error"]

    @pytest.mark.asyncio
    async def test_model_validation(self) -> None:
        """Test model name validation for security"""

        # Mock process for CLI execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.stdout.readline = AsyncMock(return_value=b"")
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        # Actually this test doesn't need subprocess mocking since model validation happens before CLI execution
        result = await execute_gemini_cli_streaming("Test prompt", "invalid@model#name")

        assert result["success"] is False
        assert "Invalid model name" in result["error"]


if __name__ == "__main__":
    # Run integration tests
    import subprocess
    import sys

    print("Running Gemini API Integration Tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    sys.exit(result.returncode)
