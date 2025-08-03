#!/usr/bin/env python3
"""
Scenario Router - Route requests based on predefined scenarios.

This module implements scenario-based routing following claude-code-router
patterns, enabling intelligent model selection based on task characteristics
and performance requirements.

Routing Scenarios:
- default: General-purpose tasks
- background: Simple, fast tasks (documentation, basic queries)
- think: Complex reasoning tasks requiring advanced models
- longContext: Large context window requirements
- webSearch: Tasks involving web search or real-time information

Features:
- Configuration-driven scenario mappings
- Context analysis for automatic scenario detection
- Fallback handling for undefined scenarios
- Performance optimization per scenario type
"""

import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ScenarioRouter:
    """Scenario-based routing engine

    This class implements intelligent routing based on predefined scenarios,
    analyzing request characteristics to select optimal provider/model combinations.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize scenario router

        Args:
            config: Routing configuration containing scenario mappings
        """
        self.config = config
        self.scenarios = config.get("scenarios", {})
        self.thresholds = config.get("thresholds", {})

        # Scenario detection rules
        self.scenario_rules = {
            "background": self._is_background_task,
            "think": self._is_thinking_task,
            "longContext": self._is_long_context_task,
            "webSearch": self._is_web_search_task,
        }

        logger.debug(f"Initialized scenario router with {len(self.scenarios)} scenarios")

    def route_by_scenario(
        self,
        scenario: Optional[str],
        context: Dict[str, Any],
        prompt: str
    ) -> Tuple[str, str, str]:
        """Route request based on scenario

        Args:
            scenario: Explicit scenario name (if provided)
            context: Request context analysis
            prompt: Original prompt text

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        # Use explicit scenario if provided
        if scenario and scenario in self.scenarios:
            return self._resolve_scenario_config(scenario, f"Explicit scenario: {scenario}")

        # Auto-detect scenario from context
        detected_scenario = self._detect_scenario(context, prompt)
        if detected_scenario:
            return self._resolve_scenario_config(
                detected_scenario,
                f"Auto-detected scenario: {detected_scenario}"
            )

        # Default fallback
        return self._resolve_scenario_config("default", "Default scenario (no specific match)")

    def _detect_scenario(self, context: Dict[str, Any], prompt: str) -> Optional[str]:
        """Automatically detect scenario from request context

        Args:
            context: Request context analysis
            prompt: Original prompt text

        Returns:
            Detected scenario name or None
        """
        # Check scenarios in priority order
        scenario_priority = ["longContext", "think", "webSearch", "background"]

        for scenario in scenario_priority:
            rule_func = self.scenario_rules.get(scenario)
            if rule_func and rule_func(context, prompt):
                logger.debug(f"Detected scenario: {scenario}")
                return scenario

        return None

    def _is_background_task(self, context: Dict[str, Any], prompt: str) -> bool:
        """Check if task is suitable for background processing

        Args:
            context: Request context analysis
            prompt: Original prompt text

        Returns:
            True if this is a background task
        """
        # Simple tasks with low complexity
        if context.get("complexity_score", 0) <= 3:
            return True

        # Small content size
        background_threshold = self.thresholds.get("background_task_size", 1000)
        if context.get("estimated_tokens", 0) <= background_threshold:
            return True

        # Simple query patterns
        simple_patterns = [
            "what is", "who is", "define", "explain briefly",
            "quick question", "simple", "basic"
        ]
        prompt_lower = prompt.lower()
        if any(pattern in prompt_lower for pattern in simple_patterns):
            return True

        return False

    def _is_thinking_task(self, context: Dict[str, Any], prompt: str) -> bool:
        """Check if task requires advanced reasoning

        Args:
            context: Request context analysis
            prompt: Original prompt text

        Returns:
            True if this requires thinking/reasoning
        """
        # Explicit reasoning requirement
        if context.get("requires_reasoning", False):
            return True

        # High complexity content
        if context.get("complexity_score", 0) >= 7:
            return True

        # Reasoning-related keywords
        thinking_patterns = [
            "analyze", "reasoning", "logic", "explain why", "because",
            "compare", "evaluate", "assess", "critique", "judge",
            "solve", "problem", "strategy", "approach", "method"
        ]
        prompt_lower = prompt.lower()
        if any(pattern in prompt_lower for pattern in thinking_patterns):
            return True

        return False

    def _is_long_context_task(self, context: Dict[str, Any], prompt: str) -> bool:
        """Check if task requires large context window

        Args:
            context: Request context analysis
            prompt: Original prompt text

        Returns:
            True if this requires long context
        """
        long_context_threshold = self.thresholds.get("long_context_tokens", 60000)
        estimated_tokens = context.get("estimated_tokens", 0)

        return estimated_tokens > long_context_threshold

    def _is_web_search_task(self, context: Dict[str, Any], prompt: str) -> bool:
        """Check if task involves web search or real-time information

        Args:
            context: Request context analysis
            prompt: Original prompt text

        Returns:
            True if this involves web search
        """
        # Web search indicators
        web_patterns = [
            "search", "latest", "recent", "current", "today",
            "news", "update", "what's new", "trending",
            "real-time", "live", "now", "currently"
        ]
        prompt_lower = prompt.lower()

        return any(pattern in prompt_lower for pattern in web_patterns)

    def _resolve_scenario_config(self, scenario: str, reason: str) -> Tuple[str, str, str]:
        """Resolve scenario configuration to provider/model

        Args:
            scenario: Scenario name
            reason: Routing reason description

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        scenario_config = self.scenarios.get(scenario)

        if not scenario_config:
            # Fallback to default scenario
            scenario_config = self.scenarios.get("default", "gemini,gemini-2.5-flash")
            reason += " (scenario not configured, using default)"

        try:
            # Parse scenario config (format: "provider,model")
            provider_name, model_name = scenario_config.split(",", 1)
            return provider_name.strip(), model_name.strip(), reason

        except ValueError:
            logger.warning(f"Invalid scenario config format: {scenario_config}")
            return "gemini", "gemini-2.5-flash", f"{reason} (invalid config, using fallback)"

    def get_available_scenarios(self) -> Dict[str, str]:
        """Get all available scenarios and their configurations

        Returns:
            Dictionary mapping scenario names to their configurations
        """
        return self.scenarios.copy()

    def validate_scenario_config(self) -> Dict[str, bool]:
        """Validate all scenario configurations

        Returns:
            Dictionary mapping scenario names to validation results
        """
        validation_results = {}

        for scenario, config in self.scenarios.items():
            try:
                provider, model = config.split(",", 1)
                validation_results[scenario] = bool(provider.strip() and model.strip())
            except ValueError:
                validation_results[scenario] = False

        return validation_results
