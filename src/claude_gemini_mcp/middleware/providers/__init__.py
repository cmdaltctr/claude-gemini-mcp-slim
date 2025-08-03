#!/usr/bin/env python3
"""
Providers Module - Multi-provider AI backend abstractions.

This module implements provider abstractions following the claude-code-router
pattern, enabling seamless integration with multiple AI service providers
while maintaining a consistent interface.

Provider Architecture:
- BaseProvider: Abstract base class defining the provider interface
- Concrete Providers: Implementations for specific AI services (Gemini, OpenRouter, DeepSeek)
- Error Handling: Standardized error types and retry logic
- Authentication: Provider-specific authentication management

Design Principles:
- Provider abstraction allows easy addition of new AI services
- Standardized request/response format across providers
- Built-in error handling and retry mechanisms
- Configuration-driven provider selection and fallback
"""

from .base_provider import BaseProvider, ProviderError, ProviderResult
from .gemini_provider import GeminiProvider

__all__ = [
    "BaseProvider",
    "ProviderError",
    "ProviderResult",
    "GeminiProvider",
]
