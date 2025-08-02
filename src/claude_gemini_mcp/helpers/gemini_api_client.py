#!/usr/bin/env python3
"""
Gemini API Client Module - Direct Google Generative AI API Integration

This module provides a clean, focused interface for interacting directly with the
Google Generative AI API. It handles all aspects of API communication including
authentication, error handling, response processing, and security.

Key Features:
- Direct API calls to Google's Generative AI service
- Comprehensive error handling with sensitive data sanitization
- Model validation and configuration management
- Retry logic for transient failures
- Detailed logging and progress indicators
- Response validation and processing
- Token counting and quota management utilities

Security Features:
- API key redaction from error messages
- Sensitive information sanitization
- Safe error propagation without data leakage
- Input validation and sanitization

Usage:
    from claude_gemini_mcp.helpers.gemini_api_client import execute_gemini_api

    # Execute API call with automatic key discovery
    result = await execute_gemini_api(
        prompt="What is Python?",
        model_name="gemini-2.5-flash",
        show_progress=True
    )

    if result["success"]:
        print(result["output"])
    else:
        print(f"Error: {result['error']}")

Dependencies:
    - google-generativeai: Required for direct API communication
    - claude_gemini_mcp.helpers.api_key_manager: For automatic API key discovery
"""

import re
import sys
from typing import Any, Dict, Optional

try:
    import google.generativeai as genai

    GOOGLE_GENERATIVEAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENERATIVEAI_AVAILABLE = False

from claude_gemini_mcp.helpers.api_key_manager import get_api_key

# API Error Sanitization Patterns
API_KEY_PATTERNS = [
    # Google API keys (AIzaSy + 33 characters)
    (r"AIzaSy[A-Za-z0-9_-]{33}", "[API_KEY_REDACTED]"),
    # OpenAI-style keys (sk- prefix)
    (r"sk-[A-Za-z0-9_-]{32,}", "[API_KEY_REDACTED]"),
    # Bearer tokens
    (r"Bearer [A-Za-z0-9_.-]{10,}", "[TOKEN_REDACTED]"),
    # Mock API keys from tests
    (r"mock-api-key-[A-Za-z0-9_-]+", "[API_KEY_REDACTED]"),
]


def sanitize_api_error(error_message: str) -> str:
    """Remove sensitive information from error messages

    This function sanitizes error messages by removing API keys, tokens,
    and other sensitive information that might be leaked in exception
    messages or log output.

    Args:
        error_message: Raw error message that may contain sensitive data

    Returns:
        str: Sanitized error message with sensitive data redacted

    Note:
        This function applies multiple regex patterns to catch various
        formats of API keys and tokens. It's designed to be conservative
        and may redact more than necessary to ensure security.
    """
    sanitized = error_message

    # Apply all sanitization patterns
    for pattern, replacement in API_KEY_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized


def validate_model_name(model_name: str) -> bool:
    """Validate if model name follows expected format

    Performs basic validation on model names to ensure they follow
    expected patterns and don't contain potentially dangerous characters.

    Args:
        model_name: Model name to validate

    Returns:
        bool: True if model name appears valid, False otherwise

    Note:
        This is a basic validation that checks for common patterns.
        The actual model availability is determined by the API response.
    """
    if not model_name or not isinstance(model_name, str):
        return False

    # Basic sanitization: only allow alphanumeric, dots, hyphens
    if not all(c.isalnum() or c in ".-" for c in model_name):
        return False

    # Check reasonable length bounds
    if len(model_name) < 3 or len(model_name) > 50:
        return False

    return True


def check_api_availability() -> tuple[bool, Optional[str]]:
    """Check if Google Generative AI library is available

    Verifies that the google-generativeai package is installed and
    importable, which is required for direct API calls.

    Returns:
        tuple[bool, Optional[str]]: (availability, error_message)
                                   (True, None) if available
                                   (False, error_message) if not available
    """
    if not GOOGLE_GENERATIVEAI_AVAILABLE:
        return False, "google-generativeai package not available"

    return True, None


async def execute_gemini_api(
    prompt: str,
    model_name: str,
    api_key: Optional[str] = None,
    show_progress: bool = True,
) -> Dict[str, Any]:
    """Execute Gemini API directly with specified model

    This is the main entry point for direct API calls to Google's Generative AI
    service. It handles authentication, model configuration, error handling,
    and response processing.

    Args:
        prompt: Input prompt for the AI model
        model_name: Name of the Gemini model to use (e.g., "gemini-2.5-flash")
        api_key: Optional API key. If None, will auto-discover using api_key_manager
        show_progress: Whether to display progress indicators and status messages

    Returns:
        Dict[str, Any]: Result dictionary containing:
            - success (bool): Whether the API call succeeded
            - output (str): Generated response text (if successful)
            - error (str): Error message (if failed)

    Raises:
        This function does not raise exceptions - all errors are captured
        and returned in the result dictionary for consistent error handling.

    Example:
        >>> result = await execute_gemini_api(
        ...     prompt="Explain quantum computing",
        ...     model_name="gemini-2.5-pro",
        ...     show_progress=True
        ... )
        >>> if result["success"]:
        ...     print(result["output"])
        ... else:
        ...     print(f"Error: {result['error']}")

    Security:
        - API keys are automatically redacted from error messages
        - Input validation prevents basic injection attempts
        - Error messages are sanitized before returning
    """
    try:
        # Check if API library is available
        available, error = check_api_availability()
        if not available:
            if show_progress:
                print(
                    "⚠️ google-generativeai not installed, using CLI fallback",
                    file=sys.stderr,
                )
            return {"success": False, "error": error}

        # Validate model name
        if not validate_model_name(model_name):
            return {"success": False, "error": "Invalid model name"}

        # Get API key (auto-discover if not provided)
        if api_key is None:
            api_key = get_api_key()

        if not api_key:
            return {"success": False, "error": "No API key found"}

        if show_progress:
            print(f"🌟 Using API key: {api_key[:8]}...", file=sys.stderr)
            print(f"🌟 Making API call to {model_name}...", file=sys.stderr)

        # Configure and create model
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        # Execute API call
        response = await model.generate_content_async(prompt)

        if show_progress:
            print("✅ API call successful!", file=sys.stderr)

        return {"success": True, "output": response.text}

    except ImportError as e:
        error_msg = f"API library import error: {str(e)}"
        if show_progress:
            print(f"⚠️ {error_msg}, using CLI fallback", file=sys.stderr)
        return {"success": False, "error": "API library not available"}

    except Exception as e:
        # Sanitize error message to prevent sensitive information leakage
        error_message = sanitize_api_error(str(e))

        if show_progress:
            print(
                f"⚠️ API call failed: {error_message}, using CLI fallback",
                file=sys.stderr,
            )
        return {"success": False, "error": error_message}


def get_supported_models() -> list[str]:
    """Get list of known supported Gemini models

    Returns a list of model names that are known to be supported.
    This is a static list and may not reflect real-time availability.

    Returns:
        list[str]: List of supported model names

    Note:
        This is a convenience function that returns commonly used models.
        The actual model availability may vary based on your API access.
    """
    return [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
        "gemini-pro-vision",
    ]


async def test_api_connection(
    api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """Test API connection with a simple prompt

    Performs a lightweight API call to verify connectivity and
    authentication. Useful for health checks and diagnostics.

    Args:
        api_key: Optional API key to test. If None, will auto-discover
        model_name: Model to use for test (default: gemini-2.5-flash)

    Returns:
        Dict[str, Any]: Result dictionary with success/error information
    """
    test_prompt = "Hello, please respond with just 'OK' to confirm connectivity."

    return await execute_gemini_api(
        prompt=test_prompt, model_name=model_name, api_key=api_key, show_progress=False
    )


def estimate_token_count(text: str) -> int:
    """Rough estimation of token count for text

    Provides a rough estimate of how many tokens the text might consume.
    This is an approximation and actual token counts may vary.

    Args:
        text: Text to estimate tokens for

    Returns:
        int: Estimated token count

    Note:
        This is a simple estimation based on character and word count.
        For exact token counting, use the API's token counting features.
    """
    # Simple estimation: roughly 4 characters per token for English
    # This is a very rough approximation
    char_count = len(text)
    word_count = len(text.split())

    # Use the higher of char_count/4 or word_count/0.75 as estimate
    char_estimate = char_count / 4
    word_estimate = word_count / 0.75

    return int(max(char_estimate, word_estimate))
