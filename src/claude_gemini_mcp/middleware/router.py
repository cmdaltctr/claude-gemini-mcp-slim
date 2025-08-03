#!/usr/bin/env python3
"""
Core Router Engine - Intelligent model routing and provider orchestration.

This module implements the central routing engine inspired by claude-code-router,
providing intelligent model selection, provider routing, and request orchestration
with scenario-based routing, token-aware selection, and fallback strategies.

Key Features:
- Scenario-based routing (default, background, think, longContext, webSearch)
- Token-aware model selection with automatic context window optimization
- Provider health monitoring and intelligent fallback
- Request context analysis for optimal routing decisions
- Comprehensive error handling and retry logic
- Performance monitoring and telemetry

Architecture:
- Router: Central orchestration engine
- RouteRequest: Standardized request format
- RouteResult: Standardized response format
- Integration with BaseProvider interface
- Configuration-driven routing rules
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from enum import Enum

from .providers.base_provider import BaseProvider, ProviderError, ProviderResult, ProviderStatus
from .providers.gemini_provider import GeminiProvider
from ..config import get_config

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategy types"""
    SCENARIO_BASED = "scenario_based"
    TOKEN_AWARE = "token_aware"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    COST_OPTIMIZED = "cost_optimized"
    FALLBACK_CASCADE = "fallback_cascade"


@dataclass
class RouteRequest:
    """Standardized routing request format

    This dataclass encapsulates all information needed for intelligent routing
    decisions, including content analysis, context requirements, and preferences.

    Attributes:
        prompt: Input text for the AI model
        tool_name: Name of the calling tool (for tool-specific routing)
        scenario: Routing scenario hint (background, think, longContext, etc.)
        max_tokens: Maximum tokens to generate
        temperature: Model temperature setting
        preferred_provider: Preferred provider name (optional)
        preferred_model: Preferred model name (optional)
        require_reasoning: Whether reasoning capabilities are required
        context_size: Estimated context size in tokens
        priority: Request priority level (high, medium, low)
        metadata: Additional routing metadata
    """
    prompt: str
    tool_name: str = "default"
    scenario: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    require_reasoning: bool = False
    context_size: Optional[int] = None
    priority: str = "medium"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RouteResult:
    """Routing decision result

    Contains the routing decision and execution result, providing full
    transparency into the routing process and performance metrics.

    Attributes:
        success: Whether routing and execution succeeded
        provider_used: Name of provider that handled the request
        model_used: Specific model that processed the request
        content: Response content
        routing_strategy: Strategy used for routing decision
        routing_reason: Human-readable explanation of routing decision
        execution_time: Total time including routing and execution
        tokens_used: Token consumption information
        fallback_attempts: Number of fallback attempts made
        error: Error message if routing/execution failed
        metadata: Additional routing and execution metadata
    """
    success: bool
    provider_used: str = ""
    model_used: str = ""
    content: str = ""
    routing_strategy: str = ""
    routing_reason: str = ""
    execution_time: Optional[float] = None
    tokens_used: Optional[Dict[str, int]] = None
    fallback_attempts: int = 0
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Router:
    """Core routing engine for intelligent model and provider selection

    The Router class implements the central orchestration logic, analyzing
    requests and routing them to optimal providers and models based on
    content, context, performance requirements, and availability.

    Features:
    - Multi-provider support with health monitoring
    - Scenario-based routing with configurable rules
    - Token-aware model selection for context optimization
    - Intelligent fallback and retry strategies
    - Performance monitoring and telemetry
    - Request context analysis and optimization

    Routing Strategies:
    1. Scenario-based: Route based on predefined scenarios (background, think, etc.)
    2. Token-aware: Select models based on context window requirements
    3. Performance-optimized: Choose fastest available option
    4. Cost-optimized: Select most economical option
    5. Fallback-cascade: Systematic fallback through available providers
    """

    def __init__(self):
        """Initialize router with configuration and providers"""
        self.config = get_config()
        self.providers: Dict[str, BaseProvider] = {}
        self.routing_enabled = self.config.is_routing_enabled()

        # Initialize providers if routing is enabled
        if self.routing_enabled:
            self._initialize_providers()
        else:
            logger.info("Routing disabled, router in legacy compatibility mode")

        # Routing statistics
        self.stats = {
            "total_requests": 0,
            "successful_routes": 0,
            "fallback_attempts": 0,
            "provider_failures": {},
            "routing_strategies_used": {},
            "average_execution_time": 0.0
        }

        logger.info(f"Router initialized with {len(self.providers)} providers, routing_enabled={self.routing_enabled}")

    def _initialize_providers(self) -> None:
        """Initialize configured providers"""
        routing_config = self.config.get_routing_config()
        provider_configs = routing_config.get("providers", {})

        for provider_name, provider_config in provider_configs.items():
            if not provider_config.get("enabled", False):
                logger.debug(f"Skipping disabled provider: {provider_name}")
                continue

            try:
                # Initialize provider based on type
                if provider_name == "gemini":
                    provider = GeminiProvider(provider_config)
                    self.providers[provider_name] = provider
                    logger.info(f"Initialized {provider_name} provider")
                else:
                    # Future providers (OpenRouter, DeepSeek) will be added here
                    logger.warning(f"Provider type {provider_name} not yet implemented")

            except Exception as e:
                logger.error(f"Failed to initialize {provider_name} provider: {str(e)}")

    def estimate_token_count(self, text: str) -> int:
        """Estimate token count for text

        Provides a rough estimate of token count for routing decisions.
        This is a simplified implementation; more sophisticated token
        counting could be added using tiktoken or similar libraries.

        Args:
            text: Input text to estimate

        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token for English text
        # This is rough but sufficient for routing decisions
        return len(text) // 4

    def analyze_request_context(self, request: RouteRequest) -> Dict[str, Any]:
        """Analyze request to determine routing context

        Performs content analysis to inform routing decisions, including
        complexity assessment, capability requirements, and optimization hints.

        Args:
            request: Routing request to analyze

        Returns:
            Dictionary with analysis results:
                - estimated_tokens: Token count estimate
                - complexity_score: Content complexity (1-10)
                - requires_reasoning: Whether reasoning is needed
                - content_type: Type of content (code, text, analysis)
                - optimization_hint: Performance optimization suggestion
        """
        prompt = request.prompt
        estimated_tokens = request.context_size or self.estimate_token_count(prompt)

        # Simple content analysis
        complexity_indicators = [
            "analyze", "complex", "detailed", "comprehensive", "reasoning",
            "explain", "compare", "evaluate", "optimize", "refactor"
        ]

        code_indicators = [
            "def ", "class ", "function", "import", "const", "var", "let",
            "public", "private", "static", "{", "}", "//", "/*", "#"
        ]

        # Calculate complexity score (1-10)
        complexity_score = 1
        prompt_lower = prompt.lower()

        for indicator in complexity_indicators:
            if indicator in prompt_lower:
                complexity_score += 1

        complexity_score = min(complexity_score, 10)

        # Determine content type
        content_type = "text"
        if any(indicator in prompt for indicator in code_indicators):
            content_type = "code"
        elif any(word in prompt_lower for word in ["analyze", "analysis", "compare", "evaluate"]):
            content_type = "analysis"

        # Determine if reasoning is required
        requires_reasoning = (
            request.require_reasoning or
            complexity_score >= 7 or
            any(word in prompt_lower for word in ["reasoning", "logic", "explain why", "because"])
        )

        # Optimization hint
        optimization_hint = "balanced"
        if estimated_tokens > 50000:
            optimization_hint = "context_optimized"
        elif complexity_score <= 3:
            optimization_hint = "speed_optimized"
        elif requires_reasoning:
            optimization_hint = "quality_optimized"

        return {
            "estimated_tokens": estimated_tokens,
            "complexity_score": complexity_score,
            "requires_reasoning": requires_reasoning,
            "content_type": content_type,
            "optimization_hint": optimization_hint
        }

    def select_routing_strategy(self, request: RouteRequest, context: Dict[str, Any]) -> RoutingStrategy:
        """Select optimal routing strategy for request

        Determines the best routing strategy based on request characteristics,
        context analysis, and current system state.

        Args:
            request: Routing request
            context: Request context analysis

        Returns:
            Selected routing strategy
        """
        # Priority-based strategy selection

        # 1. Explicit scenario takes precedence
        if request.scenario:
            return RoutingStrategy.SCENARIO_BASED

        # 2. Large context requires token-aware routing
        if context["estimated_tokens"] > self.config.get_routing_threshold("long_context_tokens"):
            return RoutingStrategy.TOKEN_AWARE

        # 3. Simple requests can use performance optimization
        if context["complexity_score"] <= 3 and context["optimization_hint"] == "speed_optimized":
            return RoutingStrategy.PERFORMANCE_OPTIMIZED

        # 4. Default to scenario-based routing
        return RoutingStrategy.SCENARIO_BASED

    def route_by_scenario(self, request: RouteRequest, context: Dict[str, Any]) -> Tuple[str, str, str]:
        """Route request based on scenario

        Implements scenario-based routing using configured scenario mappings.

        Args:
            request: Routing request
            context: Request context analysis

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        # Determine scenario
        scenario = request.scenario

        if not scenario:
            # Infer scenario from context
            if context["estimated_tokens"] > self.config.get_routing_threshold("long_context_tokens"):
                scenario = "longContext"
            elif context["complexity_score"] <= 3:
                scenario = "background"
            elif context["requires_reasoning"]:
                scenario = "think"
            else:
                scenario = "default"

        # Get scenario configuration
        scenario_config = self.config.get_scenario_config(scenario) or self.config.get_scenario_config("default")

        if not scenario_config:
            # Fallback to first available provider
            if self.providers:
                provider_name = list(self.providers.keys())[0]
                provider = self.providers[provider_name]
                model_name = provider.get_models()[0] if provider.get_models() else "gemini-2.5-flash"
                return provider_name, model_name, f"Fallback to {provider_name} (no scenario config)"
            else:
                return "gemini", "gemini-2.5-flash", "Legacy fallback (no providers)"

        # Parse scenario config (format: "provider,model")
        try:
            provider_name, model_name = scenario_config.split(",", 1)
            return provider_name, model_name, f"Scenario-based routing: {scenario}"
        except ValueError:
            logger.warning(f"Invalid scenario config format: {scenario_config}")
            return "gemini", "gemini-2.5-flash", f"Invalid scenario config, using fallback"

    def route_by_tokens(self, request: RouteRequest, context: Dict[str, Any]) -> Tuple[str, str, str]:
        """Route request based on token requirements

        Selects providers and models based on context window requirements.

        Args:
            request: Routing request
            context: Request context analysis

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        estimated_tokens = context["estimated_tokens"]

        # Find providers that can handle the token count
        suitable_providers = []

        for provider_name, provider in self.providers.items():
            if hasattr(provider, 'get_context_window'):
                for model in provider.get_models():
                    context_window = provider.get_context_window(model)
                    if context_window >= estimated_tokens:
                        suitable_providers.append((provider_name, model, context_window))

        if not suitable_providers:
            # Fallback to largest available context window
            return self.route_by_scenario(request, context)

        # Sort by context window (prefer larger windows for complex content)
        suitable_providers.sort(key=lambda x: x[2], reverse=True)

        provider_name, model_name, context_window = suitable_providers[0]
        reason = f"Token-aware routing: {estimated_tokens} tokens, selected {context_window} window"

        return provider_name, model_name, reason

    def select_provider_and_model(self, request: RouteRequest) -> Tuple[str, str, str, RoutingStrategy]:
        """Select optimal provider and model for request

        Main routing logic that analyzes the request and selects the best
        provider and model combination based on multiple factors.

        Args:
            request: Routing request

        Returns:
            Tuple of (provider_name, model_name, routing_reason, strategy_used)
        """
        # Analyze request context
        context = self.analyze_request_context(request)

        # Select routing strategy
        strategy = self.select_routing_strategy(request, context)

        # Route based on strategy
        if strategy == RoutingStrategy.SCENARIO_BASED:
            provider_name, model_name, reason = self.route_by_scenario(request, context)
        elif strategy == RoutingStrategy.TOKEN_AWARE:
            provider_name, model_name, reason = self.route_by_tokens(request, context)
        else:
            # Default to scenario-based for unimplemented strategies
            provider_name, model_name, reason = self.route_by_scenario(request, context)

        # Handle explicit preferences
        if request.preferred_provider and request.preferred_provider in self.providers:
            provider_name = request.preferred_provider
            reason += f" (user preferred provider: {request.preferred_provider})"

        if request.preferred_model:
            # Validate model is supported by selected provider
            provider = self.providers.get(provider_name)
            if provider and provider.validate_model(request.preferred_model):
                model_name = request.preferred_model
                reason += f" (user preferred model: {request.preferred_model})"

        return provider_name, model_name, reason, strategy

    async def route_request(self, request: RouteRequest) -> RouteResult:
        """Route and execute a request

        Main entry point for request routing. Handles the complete flow from
        routing decision to execution, including fallback and error handling.

        Args:
            request: Routing request to process

        Returns:
            RouteResult with execution results and routing metadata
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        # Legacy mode: use existing execution_orchestrator pattern
        if not self.routing_enabled:
            return await self._legacy_route(request, start_time)

        try:
            # Select provider and model
            provider_name, model_name, routing_reason, strategy = self.select_provider_and_model(request)

            # Update statistics
            strategy_name = strategy.value
            self.stats["routing_strategies_used"][strategy_name] = self.stats["routing_strategies_used"].get(strategy_name, 0) + 1

            # Execute request with fallback
            result = await self._execute_with_fallback(
                request, provider_name, model_name, routing_reason, strategy_name, start_time
            )

            # Update statistics
            if result.success:
                self.stats["successful_routes"] += 1
                self.stats["average_execution_time"] = (
                    (self.stats["average_execution_time"] * (self.stats["successful_routes"] - 1) + result.execution_time) /
                    self.stats["successful_routes"]
                ) if result.execution_time else self.stats["average_execution_time"]

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Router encountered unexpected error: {str(e)}")

            return RouteResult(
                success=False,
                error=f"Router error: {str(e)}",
                execution_time=execution_time,
                routing_strategy="error",
                routing_reason="Unexpected router error"
            )

    async def _execute_with_fallback(
        self,
        request: RouteRequest,
        provider_name: str,
        model_name: str,
        routing_reason: str,
        strategy_name: str,
        start_time: float
    ) -> RouteResult:
        """Execute request with intelligent fallback

        Handles request execution with systematic fallback through available
        providers if the primary choice fails.

        Args:
            request: Original routing request
            provider_name: Selected provider name
            model_name: Selected model name
            routing_reason: Explanation of routing decision
            strategy_name: Name of routing strategy used
            start_time: Request start time

        Returns:
            RouteResult with execution results
        """
        fallback_attempts = 0
        last_error = None

        # Try primary provider
        provider = self.providers.get(provider_name)
        if provider:
            try:
                logger.debug(f"Executing request with {provider_name}/{model_name}")

                provider_result = await provider.execute_with_retry(
                    request.prompt,
                    model_name,
                    show_progress=False,  # Disable progress for router execution
                    **self._extract_provider_kwargs(request)
                )

                if provider_result.success:
                    execution_time = time.time() - start_time
                    return RouteResult(
                        success=True,
                        provider_used=provider_name,
                        model_used=model_name,
                        content=provider_result.content,
                        routing_strategy=strategy_name,
                        routing_reason=routing_reason,
                        execution_time=execution_time,
                        tokens_used=provider_result.tokens_used,
                        fallback_attempts=fallback_attempts,
                        metadata={
                            "provider_metadata": provider_result.metadata,
                            "request_metadata": request.metadata
                        }
                    )
                else:
                    last_error = provider_result.error

            except ProviderError as e:
                last_error = str(e)
                logger.warning(f"Provider {provider_name} failed: {last_error}")

                # Track provider failures
                self.stats["provider_failures"][provider_name] = self.stats["provider_failures"].get(provider_name, 0) + 1

        # Fallback strategy
        fallback_strategy = self.config.get_fallback_strategy()

        if fallback_strategy == "provider_cascade":
            return await self._cascade_fallback(request, provider_name, last_error, start_time)
        elif fallback_strategy == "cli_fallback":
            return await self._legacy_route(request, start_time)
        else:  # fail_fast
            execution_time = time.time() - start_time
            return RouteResult(
                success=False,
                provider_used=provider_name,
                model_used=model_name,
                routing_strategy=strategy_name,
                routing_reason=routing_reason,
                execution_time=execution_time,
                error=f"Primary provider failed: {last_error}",
                fallback_attempts=0
            )

    async def _cascade_fallback(
        self,
        request: RouteRequest,
        failed_provider: str,
        last_error: Optional[str],
        start_time: float
    ) -> RouteResult:
        """Implement cascade fallback through available providers

        Args:
            request: Original routing request
            failed_provider: Name of provider that failed
            last_error: Error from failed provider
            start_time: Request start time

        Returns:
            RouteResult with fallback execution results
        """
        fallback_attempts = 0

        # Try other available providers
        for provider_name, provider in self.providers.items():
            if provider_name == failed_provider:
                continue

            fallback_attempts += 1
            self.stats["fallback_attempts"] += 1

            try:
                # Use first available model from fallback provider
                models = provider.get_models()
                if not models:
                    continue

                model_name = models[0]  # Use first available model

                logger.info(f"Attempting fallback to {provider_name}/{model_name}")

                provider_result = await provider.execute_with_retry(
                    request.prompt,
                    model_name,
                    show_progress=False,
                    **self._extract_provider_kwargs(request)
                )

                if provider_result.success:
                    execution_time = time.time() - start_time
                    return RouteResult(
                        success=True,
                        provider_used=provider_name,
                        model_used=model_name,
                        content=provider_result.content,
                        routing_strategy="fallback_cascade",
                        routing_reason=f"Fallback after {failed_provider} failed",
                        execution_time=execution_time,
                        tokens_used=provider_result.tokens_used,
                        fallback_attempts=fallback_attempts,
                        metadata={
                            "original_provider": failed_provider,
                            "original_error": last_error,
                            "provider_metadata": provider_result.metadata
                        }
                    )
                else:
                    last_error = provider_result.error

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Fallback provider {provider_name} failed: {last_error}")

        # All providers failed, try legacy route as final fallback
        logger.warning("All providers failed, attempting legacy route")
        return await self._legacy_route(request, start_time)

    async def _legacy_route(self, request: RouteRequest, start_time: float) -> RouteResult:
        """Legacy routing using existing execution_orchestrator pattern

        Fallback to the original execution pattern when routing is disabled
        or all providers fail.

        Args:
            request: Routing request
            start_time: Request start time

        Returns:
            RouteResult using legacy execution
        """
        try:
            # Import here to avoid circular imports
            from ..helpers.execution_orchestrator import execute_gemini_smart

            logger.debug("Using legacy execution route")

            # Map tool_name to task_type for legacy compatibility
            task_type = request.tool_name if request.tool_name != "default" else "quick_query"

            legacy_result = await execute_gemini_smart(
                request.prompt,
                task_type=task_type,
                show_progress=False,
                convert_markdown=True
            )

            execution_time = time.time() - start_time

            return RouteResult(
                success=legacy_result["success"],
                provider_used="legacy",
                model_used="legacy",
                content=legacy_result.get("output", ""),
                routing_strategy="legacy_fallback",
                routing_reason="Using legacy execution pattern",
                execution_time=execution_time,
                error=legacy_result.get("error") if not legacy_result["success"] else None,
                metadata={"legacy_result": legacy_result}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return RouteResult(
                success=False,
                routing_strategy="legacy_fallback",
                routing_reason="Legacy execution failed",
                execution_time=execution_time,
                error=f"Legacy fallback failed: {str(e)}"
            )

    def _extract_provider_kwargs(self, request: RouteRequest) -> Dict[str, Any]:
        """Extract provider-specific kwargs from request

        Args:
            request: Routing request

        Returns:
            Dictionary of provider kwargs
        """
        kwargs = {}

        if request.temperature is not None:
            kwargs["temperature"] = request.temperature

        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens

        return kwargs

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics

        Returns:
            Dictionary with routing performance statistics
        """
        return self.stats.copy()

    def get_provider_status(self) -> Dict[str, str]:
        """Get status of all providers

        Returns:
            Dictionary mapping provider names to status strings
        """
        status = {}
        for name, provider in self.providers.items():
            status[name] = provider.get_status().value
        return status

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive router health check

        Returns:
            Dictionary with router and provider health information
        """
        health_info = {
            "router_enabled": self.routing_enabled,
            "providers": {},
            "stats": self.get_stats(),
            "config_valid": True
        }

        # Check provider health
        for name, provider in self.providers.items():
            try:
                status = await provider.health_check()
                health_info["providers"][name] = {
                    "status": status.value,
                    "models": len(provider.get_models()),
                    "last_check": provider._last_health_check
                }
            except Exception as e:
                health_info["providers"][name] = {
                    "status": "error",
                    "error": str(e)
                }

        return health_info
