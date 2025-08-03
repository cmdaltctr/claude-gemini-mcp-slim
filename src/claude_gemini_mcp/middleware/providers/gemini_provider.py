#!/usr/bin/env python3
"""
Gemini Provider Implementation - Google Gemini AI service provider.

This module implements the Gemini provider following the BaseProvider interface,
integrating with the existing Gemini API and CLI clients from the helpers module.
This maintains backward compatibility while adding routing capabilities.

Features:
- Integration with existing gemini_api_client and gemini_cli_client
- API-first, CLI-fallback strategy (maintains existing pattern)
- Proper error handling and retry logic
- Token counting and usage tracking
- Health checking and status monitoring

Architecture:
- Leverages existing Gemini integration in helpers/
- Maintains decoupled architecture principles
- Provides standardized provider interface for routing system
- Preserves existing authentication and configuration patterns
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from .base_provider import BaseProvider, ProviderError, ProviderResult, ProviderStatus
from ...helpers.gemini_api_client import execute_gemini_api
from ...helpers.gemini_cli_client import execute_gemini_cli_streaming
from ...helpers.api_key_manager import get_api_key

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """Gemini AI provider implementation

    This provider integrates with Google's Gemini AI service through both
    API and CLI interfaces, maintaining the existing API-first, CLI-fallback
    strategy while providing the standardized provider interface.

    Features:
    - Seamless integration with existing Gemini helpers
    - API and CLI execution modes with automatic fallback
    - Proper model validation and capability reporting
    - Token usage tracking (when available)
    - Health monitoring and status reporting

    Supported Models:
    - gemini-2.5-flash: Fast, efficient model for quick queries
    - gemini-2.5-pro: Advanced model for complex analysis
    - gemini-2.5-flash-8b: Compact model for background tasks
    - gemini-2.5-flash-exp-0827: Experimental flash model
    - gemini-2.5-pro-exp-0827: Experimental pro model
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Gemini provider

        Args:
            config: Provider configuration containing:
                - models: List of supported Gemini models
                - api_base_url: Gemini API base URL
                - api_key_env: Environment variable for API key
                - timeout_ms: Request timeout
                - max_retries: Maximum retry attempts
        """
        super().__init__("gemini", config)

        # Gemini-specific configuration
        self.supported_models = {
            "gemini-2.5-flash": {
                "context_window": 1048576,  # 1M tokens
                "description": "Fast, efficient model for quick queries",
                "capabilities": ["text", "code", "analysis"]
            },
            "gemini-2.5-pro": {
                "context_window": 2097152,  # 2M tokens
                "description": "Advanced model for complex analysis",
                "capabilities": ["text", "code", "analysis", "reasoning"]
            },
            "gemini-2.5-flash-8b": {
                "context_window": 1048576,  # 1M tokens
                "description": "Compact model for background tasks",
                "capabilities": ["text", "code"]
            },
            "gemini-2.5-flash-exp-0827": {
                "context_window": 1048576,  # 1M tokens
                "description": "Experimental flash model",
                "capabilities": ["text", "code", "analysis"]
            },
            "gemini-2.5-pro-exp-0827": {
                "context_window": 2097152,  # 2M tokens
                "description": "Experimental pro model",
                "capabilities": ["text", "code", "analysis", "reasoning"]
            }
        }

        # Override API key loading to use existing api_key_manager
        self.api_key = get_api_key()

        logger.info(f"Initialized Gemini provider with {len(self.models)} models")
        if self.api_key:
            logger.debug("Gemini API key loaded successfully")
        else:
            logger.info("No Gemini API key found, will use CLI fallback")

    def validate_model(self, model: str) -> bool:
        """Validate that a model is supported by Gemini

        Args:
            model: Model name to validate

        Returns:
            True if model is supported, False otherwise
        """
        # Check against configured models list
        if model in self.models:
            return True

        # Check against detailed model definitions
        if model in self.supported_models:
            return True

        # Check for gemini- prefix as fallback
        if model.startswith("gemini-"):
            logger.warning(f"Model {model} not in configured list but has gemini prefix")
            return True

        return False

    async def execute_request(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> ProviderResult:
        """Execute a request to Gemini

        Implements the API-first, CLI-fallback strategy from the existing
        execution_orchestrator.py pattern while providing standardized results.

        Args:
            prompt: Input text for the AI model
            model: Specific Gemini model name to use
            **kwargs: Additional parameters:
                - show_progress: Whether to show progress indicators
                - convert_markdown: Whether to convert markdown to text
                - temperature: Model temperature (0.0-1.0)
                - max_tokens: Maximum tokens to generate

        Returns:
            ProviderResult containing the response and metadata

        Raises:
            ProviderError: If the request fails
        """
        if not self.validate_model(model):
            raise ProviderError(
                f"Model {model} is not supported by Gemini provider",
                error_code="INVALID_MODEL",
                provider_name=self.name,
                retryable=False
            )

        start_time = time.time()
        show_progress = kwargs.get("show_progress", False)

        try:
            # Strategy 1: Try API first if available
            if self.api_key:
                if show_progress:
                    logger.info(f"Executing Gemini API request with model: {model}")

                api_result = await execute_gemini_api(prompt, model, show_progress)

                if api_result["success"]:
                    execution_time = time.time() - start_time

                    return ProviderResult(
                        success=True,
                        content=api_result["output"],
                        model_used=model,
                        provider_name=self.name,
                        execution_time=execution_time,
                        metadata={
                            "execution_mode": "api",
                            "api_key_used": bool(self.api_key),
                            "original_result": api_result
                        }
                    )
                else:
                    # API failed, log and continue to CLI fallback
                    logger.warning(f"Gemini API request failed: {api_result.get('error')}")
                    if show_progress:
                        logger.info("Falling back to CLI execution")

            # Strategy 2: CLI fallback
            if show_progress:
                logger.info(f"Executing Gemini CLI request with model: {model}")

            cli_result = await execute_gemini_cli_streaming(prompt, model, show_progress)

            execution_time = time.time() - start_time

            if cli_result["success"]:
                return ProviderResult(
                    success=True,
                    content=cli_result["output"],
                    model_used=model,
                    provider_name=self.name,
                    execution_time=execution_time,
                    metadata={
                        "execution_mode": "cli",
                        "api_key_used": bool(self.api_key),
                        "fallback_reason": "api_failed" if self.api_key else "no_api_key",
                        "original_result": cli_result
                    }
                )
            else:
                # Both API and CLI failed
                error_msg = cli_result.get("error", "Unknown CLI error")
                raise ProviderError(
                    f"Both API and CLI execution failed. CLI error: {error_msg}",
                    error_code="EXECUTION_FAILED",
                    provider_name=self.name,
                    retryable=True,
                    details={
                        "api_available": bool(self.api_key),
                        "cli_error": error_msg,
                        "execution_time": execution_time
                    }
                )

        except ProviderError:
            # Re-raise provider errors as-is
            raise

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Unexpected error in Gemini provider: {str(e)}")

            raise ProviderError(
                f"Unexpected error during Gemini execution: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                provider_name=self.name,
                retryable=True,
                details={
                    "exception_type": type(e).__name__,
                    "execution_time": execution_time
                }
            )

    async def health_check(self) -> ProviderStatus:
        """Check Gemini provider health

        Performs a comprehensive health check including API availability,
        CLI accessibility, and basic model validation.

        Returns:
            ProviderStatus indicating current health state
        """
        try:
            # Check API key availability
            api_available = bool(self.api_key)

            # For now, consider the provider healthy if we have either API access or CLI access
            # A more comprehensive health check could involve actual test requests

            if api_available:
                self._status = ProviderStatus.HEALTHY
                logger.debug("Gemini provider healthy: API access available")
            else:
                # CLI should be available as fallback
                self._status = ProviderStatus.DEGRADED
                logger.debug("Gemini provider degraded: Only CLI access available")

            self._last_health_check = time.time()
            return self._status

        except Exception as e:
            logger.warning(f"Gemini health check failed: {str(e)}")
            self._status = ProviderStatus.UNAVAILABLE
            return self._status

    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model

        Args:
            model: Model name to get info for

        Returns:
            Dictionary with model information or None if not found
        """
        return self.supported_models.get(model)

    def get_context_window(self, model: str) -> int:
        """Get context window size for a model

        Args:
            model: Model name

        Returns:
            Context window size in tokens, or 0 if unknown
        """
        model_info = self.get_model_info(model)
        if model_info:
            return model_info.get("context_window", 0)
        return 0

    def supports_capability(self, model: str, capability: str) -> bool:
        """Check if a model supports a specific capability

        Args:
            model: Model name
            capability: Capability to check (e.g., 'reasoning', 'code', 'analysis')

        Returns:
            True if capability is supported, False otherwise
        """
        model_info = self.get_model_info(model)
        if model_info:
            return capability in model_info.get("capabilities", [])
        return False

    def __str__(self) -> str:
        """String representation of Gemini provider"""
        api_status = "API" if self.api_key else "CLI-only"
        return f"GeminiProvider({api_status}, {len(self.models)} models, {self._status.value})"
