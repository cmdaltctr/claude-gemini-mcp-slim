#!/usr/bin/env python3
"""
Base Provider Abstract Class - Provider interface definition.

This module defines the abstract base class for all AI service providers,
establishing a consistent interface for provider implementations and
standardizing error handling, authentication, and response formats.

Based on claude-code-router patterns, this provides:
- Standardized provider interface
- Consistent error handling
- Authentication abstraction
- Request/response transformation hooks
- Provider health checking
- Retry and fallback logic

Architecture:
- Abstract base class ensures consistent provider implementation
- Standardized result format for downstream processing
- Extensible authentication mechanism
- Built-in retry and error handling patterns
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Provider operational status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class ProviderResult:
    """Standardized provider response format

    This dataclass provides a consistent response format across all providers,
    enabling seamless provider switching and standardized error handling.

    Attributes:
        success: Whether the request was successful
        content: Response content (text or structured data)
        model_used: Actual model that processed the request
        provider_name: Name of the provider that handled the request
        tokens_used: Token consumption information (if available)
        error: Error message if request failed
        metadata: Additional provider-specific metadata
        execution_time: Request processing time in seconds
    """
    success: bool
    content: str = ""
    model_used: str = ""
    provider_name: str = ""
    tokens_used: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None


class ProviderError(Exception):
    """Base exception for provider-related errors

    This exception class provides structured error handling for provider
    operations, including error categorization and retry guidance.

    Attributes:
        message: Human-readable error description
        error_code: Provider-specific error code
        provider_name: Name of the provider that generated the error
        retryable: Whether the error condition is retryable
        details: Additional error context
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        provider_name: Optional[str] = None,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.provider_name = provider_name
        self.retryable = retryable
        self.details = details or {}


class BaseProvider(ABC):
    """Abstract base class for AI service providers

    This class defines the standard interface that all provider implementations
    must follow, ensuring consistent behavior across different AI services.

    Key responsibilities:
    - Request processing and response handling
    - Authentication and API key management
    - Error handling and retry logic
    - Health checking and status reporting
    - Model validation and capability reporting

    Attributes:
        name: Provider identifier
        config: Provider configuration from settings
        models: List of supported models
        api_key: Authentication credential
        base_url: API endpoint URL
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for failed requests
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize provider with configuration

        Args:
            name: Provider identifier (e.g., 'gemini', 'openrouter')
            config: Provider configuration dictionary containing:
                - api_key_env: Environment variable name for API key
                - api_base_url: Base URL for API endpoints
                - models: List of supported model names
                - transformers: List of transformer names to apply
                - timeout_ms: Request timeout in milliseconds
                - max_retries: Maximum retry attempts
        """
        self.name = name
        self.config = config
        self.models = config.get("models", [])
        self.base_url = config.get("api_base_url", "")
        self.timeout = config.get("timeout_ms", 30000) / 1000  # Convert to seconds
        self.max_retries = config.get("max_retries", 2)

        # Initialize API key from environment
        self.api_key = self._load_api_key()

        # Provider state
        self._status = ProviderStatus.UNKNOWN
        self._last_health_check: Optional[float] = None

        logger.info(f"Initialized {self.name} provider with {len(self.models)} models")

    def _load_api_key(self) -> Optional[str]:
        """Load API key from environment variable

        Returns:
            API key string if found, None otherwise
        """
        import os

        api_key_env = self.config.get("api_key_env")
        if not api_key_env:
            logger.warning(f"No API key environment variable configured for {self.name}")
            return None

        api_key = os.getenv(api_key_env)
        if not api_key:
            logger.warning(f"API key not found in environment variable: {api_key_env}")
            return None

        logger.debug(f"Loaded API key for {self.name} from {api_key_env}")
        return api_key

    @abstractmethod
    async def execute_request(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> ProviderResult:
        """Execute a request to the provider

        This is the main method that concrete providers must implement to
        handle AI requests. The method should handle authentication, request
        formatting, API communication, and response processing.

        Args:
            prompt: Input text for the AI model
            model: Specific model name to use
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            ProviderResult containing the response and metadata

        Raises:
            ProviderError: If the request fails or encounters an error
        """
        pass

    @abstractmethod
    def validate_model(self, model: str) -> bool:
        """Validate that a model is supported by this provider

        Args:
            model: Model name to validate

        Returns:
            True if model is supported, False otherwise
        """
        pass

    async def health_check(self) -> ProviderStatus:
        """Check provider health and availability

        Performs a lightweight health check to determine if the provider
        is operational. This can be used for provider selection and
        fallback decisions.

        Returns:
            ProviderStatus indicating current health state
        """
        import time

        try:
            # Simple API availability check
            start_time = time.time()

            # Concrete providers should override this with actual health check
            if not self.api_key and self.config.get("api_key_env"):
                self._status = ProviderStatus.UNAVAILABLE
                return self._status

            # Default to healthy if basic checks pass
            self._status = ProviderStatus.HEALTHY
            self._last_health_check = start_time

            logger.debug(f"Health check for {self.name}: {self._status.value}")
            return self._status

        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {str(e)}")
            self._status = ProviderStatus.DEGRADED
            return self._status

    def get_status(self) -> ProviderStatus:
        """Get current provider status

        Returns:
            Current ProviderStatus
        """
        return self._status

    def get_models(self) -> List[str]:
        """Get list of supported models

        Returns:
            List of model names supported by this provider
        """
        return self.models.copy()

    def supports_model(self, model: str) -> bool:
        """Check if provider supports a specific model

        Args:
            model: Model name to check

        Returns:
            True if model is supported, False otherwise
        """
        return self.validate_model(model)

    async def execute_with_retry(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> ProviderResult:
        """Execute request with retry logic

        Wrapper around execute_request that implements retry logic for
        transient failures. This method should be used by the router
        instead of calling execute_request directly.

        Args:
            prompt: Input text for the AI model
            model: Specific model name to use
            **kwargs: Additional parameters

        Returns:
            ProviderResult containing the response and metadata

        Raises:
            ProviderError: If all retry attempts fail
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    # Exponential backoff for retries
                    wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
                    logger.info(f"Retrying {self.name} request (attempt {attempt + 1}) after {wait_time}s")
                    await asyncio.sleep(wait_time)

                result = await self.execute_request(prompt, model, **kwargs)

                if result.success:
                    return result
                else:
                    # Request completed but returned an error
                    last_error = ProviderError(
                        f"Request failed: {result.error}",
                        provider_name=self.name,
                        retryable=False
                    )
                    break

            except ProviderError as e:
                last_error = e
                if not e.retryable or attempt == self.max_retries:
                    break

            except Exception as e:
                last_error = ProviderError(
                    f"Unexpected error: {str(e)}",
                    provider_name=self.name,
                    retryable=True
                )
                if attempt == self.max_retries:
                    break

        # All retry attempts failed
        if last_error:
            raise last_error
        else:
            raise ProviderError(
                f"Request failed after {self.max_retries + 1} attempts",
                provider_name=self.name,
                retryable=False
            )

    def __str__(self) -> str:
        """String representation of provider"""
        return f"{self.name}Provider(models={len(self.models)}, status={self._status.value})"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"models={self.models}, status='{self._status.value}')")
