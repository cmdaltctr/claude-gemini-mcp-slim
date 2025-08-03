#!/usr/bin/env python3
"""
Cost Optimizer - Route requests for optimal cost efficiency.

This module implements cost-aware routing, selecting providers and models
that provide the best cost-to-performance ratio for different types of
requests while maintaining quality requirements.

Features:
- Cost-per-token analysis for different models
- Quality vs cost trade-off optimization
- Task-specific cost optimization
- Budget-aware routing decisions
- Performance monitoring for cost effectiveness
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class CostOptimizer:
    """Cost optimization routing engine

    This class implements intelligent routing based on cost efficiency,
    analyzing request requirements and selecting cost-optimal provider/model
    combinations while maintaining quality standards.
    """

    def __init__(self, providers: Dict[str, Any], cost_config: Optional[Dict[str, Any]] = None):
        """Initialize cost optimizer

        Args:
            providers: Dictionary of available providers
            cost_config: Cost configuration with pricing information
        """
        self.providers = providers
        self.cost_config = cost_config or {}
        self.cost_matrix = self._build_cost_matrix()

        logger.debug(f"Initialized cost optimizer with {len(self.cost_matrix)} cost entries")

    def _build_cost_matrix(self) -> Dict[str, Dict[str, float]]:
        """Build cost matrix from configuration

        Returns:
            Dictionary mapping provider/model to cost information
        """
        # Default cost estimates (relative costs, not actual pricing)
        # These would typically come from configuration or external pricing API
        default_costs = {
            "gemini/gemini-2.5-flash": {
                "input_cost_per_1k": 0.075,  # Relative cost units
                "output_cost_per_1k": 0.3,
                "quality_score": 7.0,
                "speed_score": 9.0
            },
            "gemini/gemini-2.5-pro": {
                "input_cost_per_1k": 1.25,
                "output_cost_per_1k": 5.0,
                "quality_score": 9.0,
                "speed_score": 6.0
            },
            "gemini/gemini-2.5-flash-8b": {
                "input_cost_per_1k": 0.037,
                "output_cost_per_1k": 0.15,
                "quality_score": 6.0,
                "speed_score": 10.0
            }
        }

        # Merge with user configuration if provided
        cost_matrix = default_costs.copy()
        if "models" in self.cost_config:
            cost_matrix.update(self.cost_config["models"])

        return cost_matrix

    def route_by_cost(
        self,
        estimated_tokens: int,
        context: Dict[str, Any],
        budget_constraint: Optional[float] = None,
        quality_threshold: float = 5.0
    ) -> Tuple[str, str, str]:
        """Route request based on cost optimization

        Args:
            estimated_tokens: Estimated token count for the request
            context: Request context analysis
            budget_constraint: Maximum cost constraint (optional)
            quality_threshold: Minimum quality score required

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        # Analyze cost requirements
        cost_analysis = self._analyze_cost_requirements(estimated_tokens, context)

        # Find cost-optimal models
        optimal_models = self._find_cost_optimal_models(
            cost_analysis,
            budget_constraint,
            quality_threshold,
            context
        )

        if not optimal_models:
            # No models meet constraints, return cheapest available
            return self._get_cheapest_model(
                f"No models meet budget/quality constraints, using cheapest available"
            )

        # Select best cost-optimal model
        selected = self._select_cost_optimal_model(optimal_models, context)

        provider_name, model_name = selected["key"].split("/", 1)
        estimated_cost = selected["estimated_cost"]
        quality_score = selected["quality_score"]

        reason = (f"Cost-optimized routing: ~{estimated_cost:.3f} cost units, "
                 f"quality {quality_score}/10")

        return provider_name, model_name, reason

    def _analyze_cost_requirements(
        self,
        estimated_tokens: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze cost requirements for the request

        Args:
            estimated_tokens: Estimated input tokens
            context: Request context analysis

        Returns:
            Cost analysis dictionary
        """
        # Estimate output tokens based on task type and complexity
        complexity_score = context.get("complexity_score", 5)
        output_multiplier = {
            "code": 0.8,      # Code tasks typically have focused outputs
            "analysis": 1.5,  # Analysis tasks generate longer responses
            "text": 1.0       # General text tasks
        }.get(context.get("content_type", "text"), 1.0)

        # Adjust for complexity (more complex tasks generate longer outputs)
        complexity_multiplier = 0.5 + (complexity_score / 10.0)

        estimated_output_tokens = int(
            estimated_tokens * 0.3 * output_multiplier * complexity_multiplier
        )

        return {
            "input_tokens": estimated_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "complexity_score": complexity_score,
            "content_type": context.get("content_type", "text"),
            "requires_quality": complexity_score >= 7 or context.get("requires_reasoning", False)
        }

    def _find_cost_optimal_models(
        self,
        cost_analysis: Dict[str, Any],
        budget_constraint: Optional[float],
        quality_threshold: float,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find models that meet cost and quality constraints

        Args:
            cost_analysis: Cost analysis results
            budget_constraint: Maximum cost limit
            quality_threshold: Minimum quality requirement
            context: Request context

        Returns:
            List of suitable models with cost information
        """
        suitable_models = []
        input_tokens = cost_analysis["input_tokens"]
        output_tokens = cost_analysis["estimated_output_tokens"]

        for model_key, cost_info in self.cost_matrix.items():
            # Calculate estimated cost
            input_cost = (input_tokens / 1000.0) * cost_info["input_cost_per_1k"]
            output_cost = (output_tokens / 1000.0) * cost_info["output_cost_per_1k"]
            total_cost = input_cost + output_cost

            # Check budget constraint
            if budget_constraint and total_cost > budget_constraint:
                continue

            # Check quality threshold
            quality_score = cost_info["quality_score"]
            if quality_score < quality_threshold:
                continue

            # Check capability requirements
            if cost_analysis["requires_quality"] and quality_score < 7.0:
                continue

            suitable_models.append({
                "key": model_key,
                "estimated_cost": total_cost,
                "quality_score": quality_score,
                "speed_score": cost_info["speed_score"],
                "cost_efficiency": quality_score / total_cost if total_cost > 0 else 0,
                "cost_info": cost_info
            })

        # Sort by cost efficiency (quality per cost unit)
        suitable_models.sort(key=lambda x: x["cost_efficiency"], reverse=True)

        return suitable_models

    def _select_cost_optimal_model(
        self,
        suitable_models: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select the most cost-optimal model from candidates

        Args:
            suitable_models: List of suitable models with cost info
            context: Request context

        Returns:
            Selected model with cost information
        """
        if not suitable_models:
            return self._get_fallback_model_info()

        # For simple tasks, prefer the most cost-efficient option
        if context.get("complexity_score", 5) <= 4:
            return suitable_models[0]  # Already sorted by cost efficiency

        # For complex tasks, balance cost efficiency with quality
        # Weight cost efficiency 60%, quality 40%
        def scoring_func(model):
            cost_eff_score = model["cost_efficiency"]
            quality_score = model["quality_score"]
            return (cost_eff_score * 0.6) + (quality_score * 0.4)

        best_model = max(suitable_models, key=scoring_func)
        return best_model

    def _get_cheapest_model(self, reason: str) -> Tuple[str, str, str]:
        """Get the cheapest available model

        Args:
            reason: Routing reason description

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        if not self.cost_matrix:
            return "gemini", "gemini-2.5-flash", f"{reason} (no cost info)"

        # Find cheapest model (lowest input cost as proxy)
        cheapest = min(
            self.cost_matrix.items(),
            key=lambda x: x[1]["input_cost_per_1k"]
        )

        provider_name, model_name = cheapest[0].split("/", 1)
        return provider_name, model_name, reason

    def _get_fallback_model_info(self) -> Dict[str, Any]:
        """Get fallback model information

        Returns:
            Fallback model configuration with cost info
        """
        return {
            "key": "gemini/gemini-2.5-flash",
            "estimated_cost": 0.1,
            "quality_score": 7.0,
            "speed_score": 9.0,
            "cost_efficiency": 70.0
        }

    def estimate_request_cost(
        self,
        provider_name: str,
        model_name: str,
        input_tokens: int,
        estimated_output_tokens: int
    ) -> Dict[str, float]:
        """Estimate cost for a specific request

        Args:
            provider_name: Provider name
            model_name: Model name
            input_tokens: Input token count
            estimated_output_tokens: Estimated output token count

        Returns:
            Cost breakdown dictionary
        """
        model_key = f"{provider_name}/{model_name}"
        cost_info = self.cost_matrix.get(model_key)

        if not cost_info:
            return {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "available": False
            }

        input_cost = (input_tokens / 1000.0) * cost_info["input_cost_per_1k"]
        output_cost = (estimated_output_tokens / 1000.0) * cost_info["output_cost_per_1k"]

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "available": True,
            "quality_score": cost_info["quality_score"],
            "speed_score": cost_info["speed_score"]
        }

    def get_cost_comparison(
        self,
        input_tokens: int,
        estimated_output_tokens: int
    ) -> Dict[str, Dict[str, float]]:
        """Get cost comparison across all available models

        Args:
            input_tokens: Input token count
            estimated_output_tokens: Estimated output token count

        Returns:
            Dictionary mapping model keys to cost information
        """
        comparison = {}

        for model_key in self.cost_matrix.keys():
            provider_name, model_name = model_key.split("/", 1)
            cost_info = self.estimate_request_cost(
                provider_name, model_name, input_tokens, estimated_output_tokens
            )
            comparison[model_key] = cost_info

        return comparison

    def update_cost_matrix(self, updates: Dict[str, Dict[str, float]]) -> None:
        """Update cost matrix with new pricing information

        Args:
            updates: Dictionary of cost updates to apply
        """
        self.cost_matrix.update(updates)
        logger.info(f"Updated cost matrix with {len(updates)} entries")
