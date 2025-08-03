#!/usr/bin/env python3
"""
Request Transformer - Standardize requests for different providers.

This module handles transformation of standardized requests into provider-specific
formats, enabling seamless provider switching while maintaining consistent
interface patterns across different AI services.

Transformation Features:
- Provider-specific request format adaptation
- Parameter mapping and validation
- Content type detection and specialized handling
- Authentication header management
- Request size and limit validation

Supported Providers:
- Gemini: Google Gemini API format
- OpenRouter: OpenRouter API format (future)
- DeepSeek: DeepSeek API format (future)
"""

import logging
from typing import Any, Dict, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class RequestTransformer:
    """Request transformation coordinator

    This class manages request transformation for different providers,
    applying provider-specific formatting rules and parameter mapping.
    """

    def __init__(self):
        """Initialize request transformer"""
        self.transformers = {
            "gemini": GeminiRequestTransformer(),
            "openrouter": OpenRouterRequestTransformer(),
        }

        logger.debug(f"Initialized request transformer with {len(self.transformers)} provider transformers")

    def transform_request(
        self,
        provider_name: str,
        prompt: str,
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Transform request for specific provider

        Args:
            provider_name: Target provider name
            prompt: Input prompt text
            model: Model name to use
            **kwargs: Additional parameters

        Returns:
            Transformed request dictionary

        Raises:
            ValueError: If provider transformer not found
        """
        transformer = self.transformers.get(provider_name)
        if not transformer:
            raise ValueError(f"No transformer available for provider: {provider_name}")

        return transformer.transform(prompt, model, **kwargs)

    def validate_request(
        self,
        provider_name: str,
        request_data: Dict[str, Any]
    ) -> bool:
        """Validate transformed request

        Args:
            provider_name: Provider name
            request_data: Transformed request data

        Returns:
            True if request is valid, False otherwise
        """
        transformer = self.transformers.get(provider_name)
        if not transformer:
            return False

        return transformer.validate(request_data)


class BaseRequestTransformer(ABC):
    """Abstract base class for provider-specific request transformers"""

    @abstractmethod
    def transform(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Transform request to provider format

        Args:
            prompt: Input prompt text
            model: Model name
            **kwargs: Additional parameters

        Returns:
            Provider-specific request dictionary
        """
        pass

    @abstractmethod
    def validate(self, request_data: Dict[str, Any]) -> bool:
        """Validate transformed request

        Args:
            request_data: Transformed request data

        Returns:
            True if valid, False otherwise
        """
        pass


class GeminiRequestTransformer(BaseRequestTransformer):
    """Request transformer for Google Gemini API

    Transforms standardized requests into Gemini API format, handling
    parameter mapping and format requirements.
    """

    def transform(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Transform request to Gemini API format

        Args:
            prompt: Input prompt text
            model: Gemini model name
            **kwargs: Additional parameters:
                - temperature: Model temperature (0.0-1.0)
                - max_tokens: Maximum tokens to generate
                - top_p: Top-p sampling parameter
                - top_k: Top-k sampling parameter

        Returns:
            Gemini API request dictionary
        """
        # Build Gemini API request format
        request_data = {
            "model": model,
            "prompt": prompt,
            "parameters": {}
        }

        # Map parameters to Gemini format
        if "temperature" in kwargs:
            temperature = kwargs["temperature"]
            if isinstance(temperature, (int, float)) and 0.0 <= temperature <= 1.0:
                request_data["parameters"]["temperature"] = temperature

        if "max_tokens" in kwargs:
            max_tokens = kwargs["max_tokens"]
            if isinstance(max_tokens, int) and max_tokens > 0:
                request_data["parameters"]["max_output_tokens"] = max_tokens

        if "top_p" in kwargs:
            top_p = kwargs["top_p"]
            if isinstance(top_p, (int, float)) and 0.0 <= top_p <= 1.0:
                request_data["parameters"]["top_p"] = top_p

        if "top_k" in kwargs:
            top_k = kwargs["top_k"]
            if isinstance(top_k, int) and top_k > 0:
                request_data["parameters"]["top_k"] = top_k

        # Add safety settings if not provided
        if "safety_settings" not in kwargs:
            request_data["safety_settings"] = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]

        logger.debug(f"Transformed request for Gemini: {model} with {len(request_data['parameters'])} parameters")
        return request_data

    def validate(self, request_data: Dict[str, Any]) -> bool:
        """Validate Gemini request format

        Args:
            request_data: Gemini request data

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not isinstance(request_data.get("model"), str):
                logger.warning("Invalid model field in Gemini request")
                return False

            if not isinstance(request_data.get("prompt"), str):
                logger.warning("Invalid prompt field in Gemini request")
                return False

            # Validate parameters if present
            parameters = request_data.get("parameters", {})
            if not isinstance(parameters, dict):
                logger.warning("Invalid parameters field in Gemini request")
                return False

            # Validate temperature
            if "temperature" in parameters:
                temp = parameters["temperature"]
                if not isinstance(temp, (int, float)) or not (0.0 <= temp <= 1.0):
                    logger.warning(f"Invalid temperature value: {temp}")
                    return False

            # Validate max_output_tokens
            if "max_output_tokens" in parameters:
                max_tokens = parameters["max_output_tokens"]
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    logger.warning(f"Invalid max_output_tokens value: {max_tokens}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating Gemini request: {str(e)}")
            return False


class OpenRouterRequestTransformer(BaseRequestTransformer):
    """Request transformer for OpenRouter API

    Transforms standardized requests into OpenRouter format, compatible
    with OpenAI-style chat completions API.
    """

    def transform(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Transform request to OpenRouter format

        Args:
            prompt: Input prompt text
            model: OpenRouter model name
            **kwargs: Additional parameters

        Returns:
            OpenRouter API request dictionary
        """
        # Build OpenRouter request (OpenAI-compatible format)
        request_data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # Map optional parameters
        if "temperature" in kwargs:
            temperature = kwargs["temperature"]
            if isinstance(temperature, (int, float)) and 0.0 <= temperature <= 2.0:
                request_data["temperature"] = temperature

        if "max_tokens" in kwargs:
            max_tokens = kwargs["max_tokens"]
            if isinstance(max_tokens, int) and max_tokens > 0:
                request_data["max_tokens"] = max_tokens

        if "top_p" in kwargs:
            top_p = kwargs["top_p"]
            if isinstance(top_p, (int, float)) and 0.0 <= top_p <= 1.0:
                request_data["top_p"] = top_p

        # Add provider preferences if specified
        if "provider_preferences" in kwargs:
            request_data["provider"] = kwargs["provider_preferences"]

        logger.debug(f"Transformed request for OpenRouter: {model}")
        return request_data

    def validate(self, request_data: Dict[str, Any]) -> bool:
        """Validate OpenRouter request format

        Args:
            request_data: OpenRouter request data

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not isinstance(request_data.get("model"), str):
                logger.warning("Invalid model field in OpenRouter request")
                return False

            messages = request_data.get("messages")
            if not isinstance(messages, list) or len(messages) == 0:
                logger.warning("Invalid messages field in OpenRouter request")
                return False

            # Validate message format
            for msg in messages:
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    logger.warning("Invalid message format in OpenRouter request")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating OpenRouter request: {str(e)}")
            return False


