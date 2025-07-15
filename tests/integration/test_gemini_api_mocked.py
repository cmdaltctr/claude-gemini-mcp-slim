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

from gemini_mcp_server import (
    GOOGLE_API_KEY,
    execute_gemini_api,
    execute_gemini_cli_streaming,
)


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
    async def test_api_success_flow(self, fake_api_key: str) -> None:
        """Test successful API call flow"""

        # Mock the google.generativeai module
        mock_genai = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "API response text"

        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", fake_api_key):
                result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

                assert result["success"] is True
                assert result["output"] == "API response text"

                # Verify the API was configured correctly
                mock_genai.configure.assert_called_once_with(api_key=fake_api_key)
                mock_genai.GenerativeModel.assert_called_once_with("gemini-2.5-flash")
                mock_model.generate_content_async.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    async def test_api_missing_key(self) -> None:
        """Test API behavior with missing API key"""

        with patch("gemini_mcp_server.GOOGLE_API_KEY", None):
            result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

            assert result["success"] is False
            assert "Invalid or missing API key" in result["error"]

    @pytest.mark.asyncio
    async def test_api_invalid_key(self) -> None:
        """Test API behavior with invalid API key"""

        with patch("gemini_mcp_server.GOOGLE_API_KEY", "short"):
            result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

            assert result["success"] is False
            assert "Invalid or missing API key" in result["error"]

    @pytest.mark.asyncio
    async def test_api_import_error(self) -> None:
        """Test API fallback when google-generativeai is not available"""

        with patch("gemini_mcp_server.GOOGLE_API_KEY", "valid_api_key_1234567890"):
            # Simulate ImportError
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'google.generativeai'"),
            ):
                result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

                assert result["success"] is False
                assert "API library not available" in result["error"]

    @pytest.mark.asyncio
    async def test_api_key_redaction_in_errors(self) -> None:
        """Test that API keys are properly redacted in error messages"""

        mock_genai = MagicMock()
        mock_model = MagicMock()

        # Simulate an error that includes an API key
        error_with_key = Exception(
            "Error with key AIzaSyBHJ5X2K9L8M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z in message"
        )
        mock_model.generate_content_async = AsyncMock(side_effect=error_with_key)
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", "valid_api_key_1234567890"):
                result = await execute_gemini_api("Test prompt", "gemini-2.5-flash")

                assert result["success"] is False
                assert (
                    "AIzaSyBHJ5X2K9L8M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z" not in result["error"]
                )
                # Generate a runtime token to replace REDACTED
                api_key_placeholder = f"[API_KEY_{secrets.token_hex(8).upper()}]"
                assert (
                    api_key_placeholder in result["error"]
                    or "[API_KEY_REDACTED]" in result["error"]
                )


class TestCLIFallbackIntegration:
    """Test CLI fallback behavior when API fails"""

    @pytest.mark.asyncio
    async def test_api_to_cli_fallback(self) -> None:
        """Test automatic fallback from API to CLI"""

        # Mock subprocess for CLI execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"CLI response line 1\n",
                b"CLI response line 2\n",
                b"",  # End of output
            ]
        )
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", "valid_key"):
                # Mock API failure
                with patch("gemini_mcp_server.execute_gemini_api") as mock_api:
                    mock_api.return_value = {"success": False, "error": "API failed"}

                    result = await execute_gemini_cli_streaming(
                        "Test prompt", "gemini_quick_query"
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
        mock_process.stdout.readline = AsyncMock(return_value=b"")
        mock_process.communicate = AsyncMock(return_value=(b"Safe output", b""))

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_exec:
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):  # Force CLI usage
                result = await execute_gemini_cli_streaming(
                    "Test prompt", "gemini_quick_query"
                )

                # Verify the command was constructed securely (no shell=True)
                mock_exec.assert_called_once()
                call_args = mock_exec.call_args

                # Should be called with individual arguments, not shell command
                expected_args = [
                    "gemini",
                    "-m",
                    "gemini-2.5-flash",
                    "-p",
                    "Test prompt",
                ]
                assert call_args[0] == tuple(expected_args)

                # Verify no shell=True  # noqa: B602
                assert (
                    "shell" not in call_args[1] or call_args[1]["shell"] is False
                )  # noqa: B602

    @pytest.mark.asyncio
    async def test_cli_error_handling(self) -> None:
        """Test CLI error handling and timeout scenarios"""

        # Test CLI failure
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.pid = 12345
        mock_process.stdout.readline = AsyncMock(return_value=b"")
        mock_process.communicate = AsyncMock(return_value=(b"", b"CLI error message"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):
                result = await execute_gemini_cli_streaming(
                    "Test prompt", "gemini_quick_query"
                )

                assert result["success"] is False
                assert "CLI error message" in result["error"]

    @pytest.mark.asyncio
    async def test_cli_streaming_output(self) -> None:
        """Test CLI streaming output handling"""

        # Mock streaming output
        output_lines = [
            b"Starting analysis...\n",
            b"Processing data...\n",
            b"Analysis complete.\n",
            b"",  # End of stream
        ]

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.stdout.readline = AsyncMock(side_effect=output_lines)
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):
                result = await execute_gemini_cli_streaming(
                    "Test prompt", "gemini_quick_query"
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
            ("pre_edit", "gemini-2.5-flash"),
            ("pre_commit", "gemini-2.5-pro"),
            ("session_summary", "gemini-2.5-flash"),
        ]

        for task_type, expected_model in test_cases:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.pid = 12345
            mock_process.stdout.readline = AsyncMock(return_value=b"")
            mock_process.communicate = AsyncMock(return_value=(b"output", b""))

            with patch(
                "asyncio.create_subprocess_exec", return_value=mock_process
            ) as mock_exec:
                with patch("gemini_mcp_server.GOOGLE_API_KEY", None):
                    await execute_gemini_cli_streaming("Test prompt", task_type)

                    # Verify correct model was selected
                    call_args = mock_exec.call_args[0]
                    assert call_args[2] == expected_model  # -m flag argument

    @pytest.mark.asyncio
    async def test_invalid_task_type(self) -> None:
        """Test handling of invalid task types"""

        result = await execute_gemini_cli_streaming("Test prompt", "invalid_task_type")

        assert result["success"] is False
        assert "Invalid task type" in result["error"]

    @pytest.mark.asyncio
    async def test_model_validation(self) -> None:
        """Test model name validation for security"""

        with patch("gemini_mcp_server.GEMINI_MODELS", {"flash": "../../etc/passwd"}):
            result = await execute_gemini_cli_streaming(
                "Test prompt", "gemini_quick_query"
            )

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
