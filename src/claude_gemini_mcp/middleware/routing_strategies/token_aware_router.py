#!/usr/bin/env python3
"""
Token Aware Router - Route based on context window requirements.

This module implements token-aware routing, analyzing request size and
selecting providers/models with appropriate context window capabilities
to handle large inputs efficiently.

Features:
- Token count estimation and analysis
- Context window requirement matching
- Automatic model selection for large contexts
- Optimization for token efficiency
- Fallback handling for oversized requests
"""

import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class TokenAwareRouter:
    """Token-aware routing engine

    This class implements intelligent routing based on token requirements,
    analyzing request size and selecting models with appropriate context windows.
    """

    def __init__(self, providers: Dict[str, Any]):
        """Initialize token aware router

        Args:
            providers: Dictionary of available providers with their capabilities
        """
        self.providers = providers
        self.model_capabilities = self._build_capability_map()

        logger.debug(f"Initialized token aware router with {len(self.model_capabilities)} model capabilities")

    def _build_capability_map(self) -> Dict[str, Dict[str, Any]]:
        """Build map of model capabilities from providers

        Returns:
            Dictionary mapping model names to their capabilities
        """
        capabilities = {}

        for provider_name, provider in self.providers.items():
            if hasattr(provider, 'supported_models'):
                for model_name, model_info in provider.supported_models.items():
                    capabilities[f"{provider_name}/{model_name}"] = {
                        "provider": provider_name,
                        "model": model_name,
                        "context_window": model_info.get("context_window", 0),
                        "capabilities": model_info.get("capabilities", []),
                        "description": model_info.get("description", "")
                    }

        return capabilities

    def route_by_tokens(
        self,
        estimated_tokens: int,
        context: Dict[str, Any],
        require_reasoning: bool = False
    ) -> Tuple[str, str, str]:
        """Route request based on token requirements

        Args:
            estimated_tokens: Estimated token count for the request
            context: Request context analysis
            require_reasoning: Whether reasoning capabilities are required

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        # Find suitable models
        suitable_models = self._find_suitable_models(
            estimated_tokens,
            require_reasoning,
            context
        )

        if not suitable_models:
            # No suitable models found, return largest available
            return self._get_largest_context_model(
                f"No models found for {estimated_tokens} tokens, using largest available"
            )

        # Select best model from suitable options
        selected = self._select_optimal_model(suitable_models, context)

        provider_name = selected["provider"]
        model_name = selected["model"]
        context_window = selected["context_window"]

        reason = (f"Token-aware routing: {estimated_tokens} tokens → "
                 f"{context_window} context window")

        return provider_name, model_name, reason

    def _find_suitable_models(
        self,
        estimated_tokens: int,
        require_reasoning: bool,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find models that can handle the token requirement

        Args:
            estimated_tokens: Required token count
            require_reasoning: Whether reasoning is required
            context: Request context

        Returns:
            List of suitable model configurations
        """
        suitable = []

        # Add buffer for response generation (20% of input or min 1000 tokens)
        buffer_tokens = max(int(estimated_tokens * 0.2), 1000)
        required_context = estimated_tokens + buffer_tokens

        for model_info in self.model_capabilities.values():
            context_window = model_info["context_window"]
            capabilities = model_info["capabilities"]

            # Check context window requirement
            if context_window < required_context:
                continue

            # Check reasoning requirement
            if require_reasoning and "reasoning" not in capabilities:
                continue

            # Check content type compatibility
            content_type = context.get("content_type", "text")
            if content_type == "code" and "code" not in capabilities:
                continue

            suitable.append(model_info)

        # Sort by context window (prefer models with appropriate size, not necessarily largest)
        suitable.sort(key=lambda x: abs(x["context_window"] - required_context * 2))

        return suitable

    def _select_optimal_model(
        self,
        suitable_models: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select the optimal model from suitable candidates

        Args:
            suitable_models: List of suitable model configurations
            context: Request context analysis

        Returns:
            Selected model configuration
        """
        if not suitable_models:
            return self._get_fallback_model()

        # Consider context preferences for selection
        priority = context.get("priority", "balanced")

        if priority == "speed":
            # Prefer models with smaller context windows (faster)
            return min(suitable_models, key=lambda x: x["context_window"])
        elif priority == "cost":
            # Prefer most cost-effective models (smallest suitable context)
            return suitable_models[0]  # Already sorted by preference
        else:
            # Balanced approach: first suitable model
            return suitable_models[0]

    def _get_largest_context_model(self, reason: str) -> Tuple[str, str, str]:
        """Get model with largest context window

        Args:
            reason: Routing reason description

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        if not self.model_capabilities:
            return "gemini", "gemini-2.5-pro", f"{reason} (no model info, using fallback)"

        # Find model with largest context window
        largest = max(
            self.model_capabilities.values(),
            key=lambda x: x["context_window"]
        )

        return largest["provider"], largest["model"], reason

    def _get_fallback_model(self) -> Dict[str, Any]:
        """Get fallback model configuration

        Returns:
            Fallback model configuration
        """
        return {
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "context_window": 1048576,
            "capabilities": ["text", "code"],
            "description": "Fallback model"
        }

    def estimate_token_efficiency(
        self,
        estimated_tokens: int,
        model_info: Dict[str, Any]
    ) -> float:
        """Estimate token efficiency for a model

        Args:
            estimated_tokens: Required token count
            model_info: Model configuration

        Returns:
            Efficiency score (0.0 to 1.0)
        """
        context_window = model_info["context_window"]

        if context_window <= 0:
            return 0.0

        # Efficiency is better when using more of the available context
        # but penalize massive over-allocation
        utilization = estimated_tokens / context_window

        if utilization > 1.0:
            return 0.0  # Can't handle the request
        elif utilization > 0.8:
            return 1.0  # Good utilization
        elif utilization > 0.5:
            return 0.8  # Reasonable utilization
        elif utilization > 0.2:
            return 0.6  # Under-utilized but acceptable
        else:
            return 0.3  # Significant over-allocation

    def get_token_requirements(self, context: Dict[str, Any]) -> Dict[str, int]:
        """Get token requirements analysis

        Args:
            context: Request context analysis

        Returns:
            Dictionary with token requirement details
        """
        estimated_tokens = context.get("estimated_tokens", 0)
        buffer_tokens = max(int(estimated_tokens * 0.2), 1000)

        return {
            "input_tokens": estimated_tokens,
            "buffer_tokens": buffer_tokens,
            "total_required": estimated_tokens + buffer_tokens,
            "minimum_context_window": estimated_tokens + buffer_tokens
        }

    def validate_token_requirements(
        self,
        estimated_tokens: int,
        provider_name: str,
        model_name: str
    ) -> bool:
        """Validate that a model can handle token requirements

        Args:
            estimated_tokens: Required token count
            provider_name: Provider name
            model_name: Model name

        Returns:
            True if model can handle the requirements
        """
        model_key = f"{provider_name}/{model_name}"
        model_info = self.model_capabilities.get(model_key)

        if not model_info:
            return False

        context_window = model_info["context_window"]
        buffer_tokens = max(int(estimated_tokens * 0.2), 1000)
        required_context = estimated_tokens + buffer_tokens

        return context_window >= required_context
