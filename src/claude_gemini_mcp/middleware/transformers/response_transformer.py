#!/usr/bin/env python3
"""
Response Transformer - Normalize responses from different providers.

This module handles transformation of provider-specific responses into
standardized formats, enabling consistent response handling across
different AI services and maintaining compatibility with existing code.

Transformation Features:
- Provider-specific response format normalization
- Error message standardization
- Metadata extraction and standardization
- Content format consistency
- Token usage tracking normalization

Supported Providers:
- Gemini: Google Gemini API/CLI response format
- OpenRouter: OpenRouter API response format (future)
- DeepSeek: DeepSeek API response format (future)
"""

import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ResponseTransformer:
    """Response transformation coordinator

    This class manages response transformation from different providers,
    applying provider-specific normalization rules and standardizing output.
    """

    def __init__(self):
        """Initialize response transformer"""
        self.transformers = {
            "gemini": GeminiResponseTransformer(),
            # Future transformers will be added here
            # "openrouter": OpenRouterResponseTransformer(),
            # "deepseek": DeepSeekResponseTransformer(),
        }

        logger.debug(f"Initialized response transformer with {len(self.transformers)} provider transformers")

    def transform_response(
        self,
        provider_name: str,
        raw_response: Dict[str, Any],
        model_used: str
    ) -> Dict[str, Any]:
        """Transform provider response to standard format

        Args:
            provider_name: Source provider name
            raw_response: Raw provider response
            model_used: Model that generated the response

        Returns:
            Standardized response dictionary

        Raises:
            ValueError: If provider transformer not found
        """
        transformer = self.transformers.get(provider_name)
        if not transformer:
            raise ValueError(f"No transformer available for provider: {provider_name}")

        return transformer.transform(raw_response, model_used)


class BaseResponseTransformer(ABC):
    """Abstract base class for provider-specific response transformers"""

    @abstractmethod
    def transform(self, raw_response: Dict[str, Any], model_used: str) -> Dict[str, Any]:
        """Transform provider response to standard format

        Args:
            raw_response: Raw provider response
            model_used: Model that generated the response

        Returns:
            Standardized response dictionary
        """
        pass


class GeminiResponseTransformer(BaseResponseTransformer):
    """Response transformer for Google Gemini API/CLI responses

    Normalizes Gemini responses to the standard format expected by
    the existing codebase, ensuring compatibility with current patterns.
    """

    def transform(self, raw_response: Dict[str, Any], model_used: str) -> Dict[str, Any]:
        """Transform Gemini response to standard format

        Args:
            raw_response: Raw Gemini response (from API or CLI)
            model_used: Gemini model that generated the response

        Returns:
            Standardized response dictionary with:
                - success: Boolean indicating success/failure
                - content: Response text content
                - error: Error message if failed
                - metadata: Additional response metadata
        """
        try:
            # Gemini responses already come in the expected format from our existing helpers
            # This transformer mainly ensures consistency and adds metadata

            if not isinstance(raw_response, dict):
                logger.warning(f"Invalid Gemini response format: {type(raw_response)}")
                return {
                    "success": False,
                    "content": "",
                    "error": "Invalid response format",
                    "metadata": {
                        "model_used": model_used,
                        "provider": "gemini",
                        "transformation_error": "Invalid response type"
                    }
                }

            # Extract standard fields
            success = raw_response.get("success", False)
            content = raw_response.get("output", "") if success else ""
            error = raw_response.get("error") if not success else None

            # Build standardized response
            standardized = {
                "success": success,
                "content": content,
                "error": error,
                "metadata": {
                    "model_used": model_used,
                    "provider": "gemini",
                    "original_response": raw_response
                }
            }

            # Extract additional metadata if available
            if "metadata" in raw_response:
                standardized["metadata"].update(raw_response["metadata"])

            # Add token usage information if available
            if "tokens_used" in raw_response:
                standardized["tokens_used"] = raw_response["tokens_used"]

            logger.debug(f"Transformed Gemini response: success={success}, content_length={len(content)}")
            return standardized

        except Exception as e:
            logger.error(f"Error transforming Gemini response: {str(e)}")
            return {
                "success": False,
                "content": "",
                "error": f"Response transformation failed: {str(e)}",
                "metadata": {
                    "model_used": model_used,
                    "provider": "gemini",
                    "transformation_error": str(e)
                }
            }
