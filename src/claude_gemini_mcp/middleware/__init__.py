#!/usr/bin/env python3
"""
Middleware Module - Intelligent AI model routing and provider orchestration.

This module provides the middleware layer for the claude-gemini-mcp-slim project,
implementing claude-code-router concepts for dynamic model routing, multi-provider
support, and intelligent request orchestration.

Key Components:
- Router: Core routing engine for provider and model selection
- Providers: Abstract and concrete provider implementations
- Transformers: Request/response transformation layer
- Routing Strategies: Intelligent routing logic (scenario, token-aware, cost-optimization)

This module follows the Decoupled Module Pattern:
- Middleware acts as the intelligent orchestration layer
- Maintains separation between MCP server and AI backends
- Provides extensible architecture for new providers and routing strategies

Architecture Compliance:
- Follows CLAUDE.md architectural guidelines
- Implements Agentic Collaboration Protocol (ACP) principles
- Maintains backward compatibility with existing execution patterns
"""

from .router import Router, RouteRequest, RouteResult
from .providers.base_provider import BaseProvider, ProviderError, ProviderResult
from .providers.gemini_provider import GeminiProvider

# Public API exports
__all__ = [
    "Router",
    "RouteRequest",
    "RouteResult",
    "BaseProvider",
    "ProviderError",
    "ProviderResult",
    "GeminiProvider",
]
