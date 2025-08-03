#!/usr/bin/env python3
"""
Transformers Module - Request/Response transformation layer.

This module implements the transformation layer for standardizing requests
and responses across different AI providers, following claude-code-router
patterns for provider abstraction and format normalization.

Key Components:
- RequestTransformer: Standardize requests to provider-specific formats
- ResponseTransformer: Normalize responses to consistent format
- Provider-specific transformers for different API formats
- Content type detection and specialized handling

Architecture:
- Pluggable transformer system for extensibility
- Provider-specific format adaptation
- Content-aware transformation rules
- Error handling and format validation
"""

from .request_transformer import RequestTransformer
from .response_transformer import ResponseTransformer

__all__ = [
    "RequestTransformer",
    "ResponseTransformer",
]
