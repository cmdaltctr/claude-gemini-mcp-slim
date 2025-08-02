#!/usr/bin/env python3
"""
Comprehensive unit tests for the Gemini API Client module.

Tests direct API calls, error handling, response processing, and security
as specified in task 1.10 requirements.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path for imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from claude_gemini_mcp.helpers.gemini_api_client import (
    API_KEY_PATTERNS,
    check_api_availability,
    estimate_token_count,
    execute_gemini_api,
    get_supported_models,
    sanitize_api_error,
    test_api_connection,
    validate_model_name,
)


class TestAPIErrorSanitization:
    """Test API error sanitization functionality."""

    def test_sanitize_api_error_google_api_keys(self):
        """Test redaction of Google API keys from error messages."""
        test_cases = [
            (
                "Error: Invalid API key AIzaSy123456789012345678901234567890123",
                "Error: Invalid API key [API_KEY_REDACTED]",
            ),
            (
                "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567 not found",
                "[API_KEY_REDACTED] not found",
            ),
            (
                "Multiple keys: AIzaSy111111111111111111111111111111111 and AIzaSy222222222222222222222222222222222",
                "Multiple keys: [API_KEY_REDACTED] and [API_KEY_REDACTED]",
            ),
        ]

        for error_msg, expected in test_cases:
            result = sanitize_api_error(error_msg)
            assert result == expected
            assert "AIzaSy" not in result

    def test_sanitize_api_error_openai_style_keys(self):
        """Test redaction of OpenAI-style API keys."""
        test_cases = [
            (
                "Error with sk-1234567890123456789012345678901234567890",
                "Error with [API_KEY_REDACTED]",
            ),
            (
                "sk-abcdefghijklmnopqrstuvwxyz1234567890 is invalid",
                "[API_KEY_REDACTED] is invalid",
            ),
        ]

        for error_msg, expected in test_cases:
            result = sanitize_api_error(error_msg)
            assert result == expected
            assert "sk-" not in result

    def test_sanitize_api_error_bearer_tokens(self):
        """Test redaction of Bearer tokens."""
        test_cases = [
            (
                "Authorization failed: Bearer abc123def456ghi789",
                "Authorization failed: [TOKEN_REDACTED]",
            ),
            ("Bearer token_1234567890_abcdefghij expired", "[TOKEN_REDACTED] expired"),
        ]

        for error_msg, expected in test_cases:
            result = sanitize_api_error(error_msg)
            assert result == expected
            assert (
                "Bearer" not in result
                or result == "Authorization failed: [TOKEN_REDACTED]"
            )

    def test_sanitize_api_error_mock_keys(self):
        """Test redaction of mock API keys used in tests."""
        test_cases = [
            (
                "Test error with mock-api-key-test123",
                "Test error with [API_KEY_REDACTED]",
            ),
            ("mock-api-key-integration-test-456 failed", "[API_KEY_REDACTED] failed"),
        ]

        for error_msg, expected in test_cases:
            result = sanitize_api_error(error_msg)
            assert result == expected
            assert "mock-api-key" not in result

    def test_sanitize_api_error_no_sensitive_data(self):
        """Test that normal error messages are unchanged."""
        normal_messages = [
            "Network connection failed",
            "Invalid model name specified",
            "Request timed out",
            "Server error 500",
        ]

        for msg in normal_messages:
            result = sanitize_api_error(msg)
            assert result == msg

    def test_sanitize_api_error_multiple_patterns(self):
        """Test sanitization when multiple patterns are present."""
        error_msg = "Auth failed: Bearer token123456789 for AIzaSy123456789012345678901234567890123"
        result = sanitize_api_error(error_msg)

        assert "[TOKEN_REDACTED]" in result
        assert "[API_KEY_REDACTED]" in result
        assert "Bearer" not in result
        assert "AIzaSy" not in result


class TestModelValidation:
    """Test model name validation functionality."""

    def test_validate_model_name_valid_models(self):
        """Test validation of valid model names."""
        valid_models = [
            "gemini-pro",
            "gemini-2.5-flash",
            "gemini-1.5-pro",
            "model-1.0",
            "test.model",
            "gemini-pro-vision",
        ]

        for model in valid_models:
            assert validate_model_name(model) is True

    def test_validate_model_name_invalid_models(self):
        """Test validation of invalid model names."""
        invalid_models = [
            None,  # None value
            "",  # Empty string
            123,  # Non-string
            "model$name",  # Invalid character
            "model@name",  # Invalid character
            "model name",  # Space character
            "model/name",  # Invalid character
            "a",  # Too short
            "a" * 60,  # Too long
        ]

        for model in invalid_models:
            assert validate_model_name(model) is False

    def test_validate_model_name_edge_cases(self):
        """Test edge cases in model name validation."""
        # Exactly minimum length
        assert validate_model_name("abc") is True

        # Exactly maximum length
        assert validate_model_name("a" * 50) is True

        # Just over maximum length
        assert validate_model_name("a" * 51) is False


class TestAPIAvailability:
    """Test API availability checking functionality."""

    @patch(
        "claude_gemini_mcp.helpers.gemini_api_client.GOOGLE_GENERATIVEAI_AVAILABLE",
        True,
    )
    def test_check_api_availability_available(self):
        """Test when Google Generative AI library is available."""
        available, error = check_api_availability()
        assert available is True
        assert error is None

    @patch(
        "claude_gemini_mcp.helpers.gemini_api_client.GOOGLE_GENERATIVEAI_AVAILABLE",
        False,
    )
    def test_check_api_availability_unavailable(self):
        """Test when Google Generative AI library is unavailable."""
        available, error = check_api_availability()
        assert available is False
        assert error == "google-generativeai package not available"


class TestExecuteGeminiAPI:
    """Test main API execution functionality."""

    @patch("claude_gemini_mcp.helpers.gemini_api_client.get_api_key")
    @patch("claude_gemini_mcp.helpers.gemini_api_client.genai")
    @pytest.mark.asyncio
    async def test_execute_gemini_api_success(self, mock_genai, mock_get_key):
        """Test successful API call execution."""
        # Setup mocks
        mock_get_key.return_value = "test-api-key-1234567890"
        mock_response = MagicMock()
        mock_response.text = "Test response from API"

        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        # Execute
        result = await execute_gemini_api(
            "Test prompt", "gemini-2.5-flash", show_progress=False
        )

        # Verify
        assert result["success"] is True
        assert result["output"] == "Test response from API"
        mock_genai.configure.assert_called_once_with(api_key="test-api-key-1234567890")
        mock_genai.GenerativeModel.assert_called_once_with("gemini-2.5-flash")
        mock_model.generate_content_async.assert_called_once_with("Test prompt")

    @patch("claude_gemini_mcp.helpers.gemini_api_client.get_api_key")
    @pytest.mark.asyncio
    async def test_execute_gemini_api_no_key(self, mock_get_key):
        """Test API call when no API key is available."""
        mock_get_key.return_value = None

        result = await execute_gemini_api(
            "Test prompt", "gemini-2.5-flash", show_progress=False
        )

        assert result["success"] is False
        assert "No API key found" in result["error"]

    @patch("claude_gemini_mcp.helpers.gemini_api_client.get_api_key")
    @pytest.mark.asyncio
    async def test_execute_gemini_api_invalid_model(self, mock_get_key):
        """Test API call with invalid model name."""
        mock_get_key.return_value = "test-api-key-1234567890"

        result = await execute_gemini_api(
            "Test prompt", "invalid@model", show_progress=False
        )

        assert result["success"] is False
        assert "Invalid model name" in result["error"]

    @patch(
        "claude_gemini_mcp.helpers.gemini_api_client.GOOGLE_GENERATIVEAI_AVAILABLE",
        False,
    )
    @patch("claude_gemini_mcp.helpers.gemini_api_client.get_api_key")
    @pytest.mark.asyncio
    async def test_execute_gemini_api_library_unavailable(self, mock_get_key):
        """Test API call when google-generativeai library is unavailable."""
        mock_get_key.return_value = "test-api-key-1234567890"

        result = await execute_gemini_api(
            "Test prompt", "gemini-2.5-flash", show_progress=False
        )

        assert result["success"] is False
        assert "google-generativeai package not available" in result["error"]

    @patch("claude_gemini_mcp.helpers.gemini_api_client.get_api_key")
    @patch("claude_gemini_mcp.helpers.gemini_api_client.genai")
    @pytest.mark.asyncio
    async def test_execute_gemini_api_exception_handling(
        self, mock_genai, mock_get_key
    ):
        """Test exception handling during API call."""
        # Setup mocks
        mock_get_key.return_value = "test-api-key-1234567890"
        mock_genai.GenerativeModel.side_effect = Exception(
            "API error with AIzaSy1234567890123456789012345678901234567890"
        )

        result = await execute_gemini_api(
            "Test prompt", "gemini-2.5-flash", show_progress=False
        )

        assert result["success"] is False
        assert "[API_KEY_REDACTED]" in result["error"]
        assert "AIzaSy1234567890123456789012345678901234567890" not in result["error"]

    @patch("claude_gemini_mcp.helpers.gemini_api_client.get_api_key")
    @patch("claude_gemini_mcp.helpers.gemini_api_client.genai")
    @pytest.mark.asyncio
    async def test_execute_gemini_api_with_provided_key(self, mock_genai, mock_get_key):
        """Test API call with explicitly provided API key."""
        # Setup mocks - get_api_key should not be called
        provided_key = "provided-api-key-1234567890"
        mock_response = MagicMock()
        mock_response.text = "Test response"

        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        # Execute with provided key
        result = await execute_gemini_api(
            "Test prompt", "gemini-2.5-flash", api_key=provided_key, show_progress=False
        )

        # Verify
        assert result["success"] is True
        mock_genai.configure.assert_called_once_with(api_key=provided_key)
        mock_get_key.assert_not_called()  # Should not call auto-discovery

    @patch("claude_gemini_mcp.helpers.gemini_api_client.get_api_key")
    @patch("claude_gemini_mcp.helpers.gemini_api_client.genai")
    @pytest.mark.asyncio
    async def test_execute_gemini_api_import_error(self, mock_genai, mock_get_key):
        """Test handling of ImportError during API call."""
        mock_get_key.return_value = "test-api-key-1234567890"
        mock_genai.configure.side_effect = ImportError("Module not found")

        result = await execute_gemini_api(
            "Test prompt", "gemini-2.5-flash", show_progress=False
        )

        assert result["success"] is False
        assert "API library not available" in result["error"]


class TestAPIConnectionTesting:
    """Test API connection testing functionality."""

    @patch("claude_gemini_mcp.helpers.gemini_api_client.execute_gemini_api")
    @pytest.mark.asyncio
    async def test_test_api_connection_success(self, mock_execute):
        """Test successful API connection test."""
        mock_execute.return_value = {"success": True, "output": "OK"}

        result = await test_api_connection("test-api-key-1234567890")

        assert result["success"] is True
        mock_execute.assert_called_once()

        # Verify the call was made with correct parameters
        call_args = mock_execute.call_args
        assert "Hello, please respond with just 'OK'" in call_args[1]["prompt"]
        assert call_args[1]["model_name"] == "gemini-2.5-flash"
        assert call_args[1]["api_key"] == "test-api-key-1234567890"
        assert call_args[1]["show_progress"] is False

    @patch("claude_gemini_mcp.helpers.gemini_api_client.execute_gemini_api")
    @pytest.mark.asyncio
    async def test_test_api_connection_failure(self, mock_execute):
        """Test failed API connection test."""
        mock_execute.return_value = {"success": False, "error": "Connection failed"}

        result = await test_api_connection("test-api-key-1234567890")

        assert result["success"] is False
        assert result["error"] == "Connection failed"

    @patch("claude_gemini_mcp.helpers.gemini_api_client.execute_gemini_api")
    @pytest.mark.asyncio
    async def test_test_api_connection_auto_discover_key(self, mock_execute):
        """Test API connection test with auto-discovered key."""
        mock_execute.return_value = {"success": True, "output": "OK"}

        # Call without providing api_key (should auto-discover)
        result = await test_api_connection()

        assert result["success"] is True

        # Verify the call was made with None api_key (auto-discovery)
        call_args = mock_execute.call_args
        assert call_args[1]["api_key"] is None

    @patch("claude_gemini_mcp.helpers.gemini_api_client.execute_gemini_api")
    @pytest.mark.asyncio
    async def test_test_api_connection_custom_model(self, mock_execute):
        """Test API connection test with custom model."""
        mock_execute.return_value = {"success": True, "output": "OK"}

        result = await test_api_connection("test-key", "gemini-2.5-pro")

        assert result["success"] is True

        # Verify custom model was used
        call_args = mock_execute.call_args
        assert call_args[1]["model_name"] == "gemini-2.5-pro"


class TestSupportedModels:
    """Test supported models functionality."""

    def test_get_supported_models(self):
        """Test that supported models list is returned correctly."""
        models = get_supported_models()

        assert isinstance(models, list)
        assert len(models) > 0

        # Check for expected models
        expected_models = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
            "gemini-pro-vision",
        ]

        for model in expected_models:
            assert model in models

    def test_get_supported_models_are_valid(self):
        """Test that all supported models pass validation."""
        models = get_supported_models()

        for model in models:
            assert validate_model_name(model) is True


class TestTokenEstimation:
    """Test token counting estimation functionality."""

    def test_estimate_token_count_short_text(self):
        """Test token estimation for short text."""
        text = "Hello world"
        tokens = estimate_token_count(text)

        assert isinstance(tokens, int)
        assert tokens > 0
        assert tokens < 100  # Should be reasonable for short text

    def test_estimate_token_count_long_text(self):
        """Test token estimation for longer text."""
        text = (
            "This is a much longer piece of text that should result in more tokens. "
            * 10
        )
        tokens = estimate_token_count(text)

        assert isinstance(tokens, int)
        assert tokens > 50  # Should be higher for longer text

    def test_estimate_token_count_empty_text(self):
        """Test token estimation for empty text."""
        tokens = estimate_token_count("")
        assert tokens == 0

    def test_estimate_token_count_whitespace_only(self):
        """Test token estimation for whitespace-only text."""
        tokens = estimate_token_count("   ")
        assert tokens >= 0  # Should handle gracefully

    def test_estimate_token_count_consistency(self):
        """Test that token estimation is consistent."""
        text = "Consistent test text for token counting"

        # Multiple calls should return same result
        tokens1 = estimate_token_count(text)
        tokens2 = estimate_token_count(text)

        assert tokens1 == tokens2

    def test_estimate_token_count_scaling(self):
        """Test that token count scales reasonably with text length."""
        short_text = "Short text"
        long_text = short_text * 10

        short_tokens = estimate_token_count(short_text)
        long_tokens = estimate_token_count(long_text)

        # Longer text should have more tokens
        assert long_tokens > short_tokens
        # But not necessarily exactly 10x due to estimation algorithm
        assert long_tokens >= short_tokens * 5  # At least 5x more


if __name__ == "__main__":
    pytest.main([__file__])
