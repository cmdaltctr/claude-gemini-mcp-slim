#!/usr/bin/env python3
"""
Performance Optimizer - Advanced routing for optimal performance and speed.

This module implements performance-aware routing, dynamically selecting providers
and models based on real-time performance metrics, response time requirements,
and throughput optimization while maintaining quality standards.

Features:
- Performance-based model selection
- Response time optimization
- Throughput analysis and routing
- Real-time performance monitoring
- Adaptive routing based on historical performance
- Load balancing across providers
"""

import logging
import time
from typing import Dict, Any, List, Tuple, Optional, NamedTuple
from collections import defaultdict, deque
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a provider/model combination"""
    response_times: deque
    success_rate: float
    throughput: float  # requests per minute
    error_count: int
    total_requests: int
    last_updated: float
    average_response_time: float
    p95_response_time: float


class PerformanceOptimizerError(Exception):
    """Custom exception for performance optimizer errors"""
    pass


class PerformanceOptimizer:
    """Performance optimization routing engine

    This class implements intelligent routing based on performance metrics,
    analyzing real-time performance data and selecting optimal provider/model
    combinations for speed and reliability requirements.
    """

    def __init__(self, providers: Dict[str, Any], performance_config: Optional[Dict[str, Any]] = None):
        """Initialize performance optimizer

        Args:
            providers: Dictionary of available providers
            performance_config: Performance configuration with thresholds and preferences
        """
        self.providers = providers
        self.performance_config = performance_config or {}
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.lock = threading.Lock()

        # Configuration defaults
        self.max_response_time = self.performance_config.get("max_response_time", 30.0)  # seconds
        self.min_success_rate = self.performance_config.get("min_success_rate", 0.85)
        self.metrics_window_size = self.performance_config.get("metrics_window_size", 100)
        self.performance_weight = self.performance_config.get("performance_weight", 0.7)
        self.quality_weight = self.performance_config.get("quality_weight", 0.3)

        # Initialize default performance baselines
        self._initialize_performance_baselines()

        logger.debug(f"Initialized performance optimizer with {len(self.performance_metrics)} model entries")

    def _initialize_performance_baselines(self) -> None:
        """Initialize performance baselines for known models"""
        baselines = {
            "gemini/gemini-2.5-flash": {
                "expected_response_time": 2.5,
                "success_rate": 0.95,
                "throughput": 30.0,
                "quality_score": 7.0,
                "capabilities": ["code", "text", "analysis"]
            },
            "gemini/gemini-2.5-pro": {
                "expected_response_time": 8.0,
                "success_rate": 0.92,
                "throughput": 15.0,
                "quality_score": 9.0,
                "capabilities": ["code", "text", "analysis", "reasoning"]
            },
            "gemini/gemini-2.5-flash-8b": {
                "expected_response_time": 1.5,
                "success_rate": 0.93,
                "throughput": 50.0,
                "quality_score": 6.0,
                "capabilities": ["text", "simple_code"]
            },
            "openrouter/openai/gpt-4o-mini": {
                "expected_response_time": 3.0,
                "success_rate": 0.94,
                "throughput": 25.0,
                "quality_score": 7.5,
                "capabilities": ["code", "text", "analysis"]
            },
            "openrouter/anthropic/claude-3-haiku": {
                "expected_response_time": 2.0,
                "success_rate": 0.96,
                "throughput": 35.0,
                "quality_score": 8.0,
                "capabilities": ["text", "analysis", "reasoning"]
            },
            "openrouter/deepseek/deepseek-chat": {
                "expected_response_time": 4.0,
                "success_rate": 0.90,
                "throughput": 20.0,
                "quality_score": 6.5,
                "capabilities": ["text", "code"]
            },
            "openrouter/qwen/qwen3-coder-30b-instruct": {
                "expected_response_time": 5.0,
                "success_rate": 0.88,
                "throughput": 18.0,
                "quality_score": 8.5,
                "capabilities": ["code", "agentic_coding"]
            }
        }

        current_time = time.time()
        for model_key, baseline in baselines.items():
            self.performance_metrics[model_key] = PerformanceMetrics(
                response_times=deque(maxlen=self.metrics_window_size),
                success_rate=baseline["success_rate"],
                throughput=baseline["throughput"],
                error_count=0,
                total_requests=0,
                last_updated=current_time,
                average_response_time=baseline["expected_response_time"],
                p95_response_time=baseline["expected_response_time"] * 1.5
            )

    def route_by_performance(
        self,
        context: Dict[str, Any],
        speed_priority: float = 0.7,
        quality_threshold: float = 6.0,
        max_response_time: Optional[float] = None
    ) -> Tuple[str, str, str]:
        """Route request based on performance optimization

        Args:
            context: Request context analysis
            speed_priority: Weight for speed vs quality (0.0-1.0)
            quality_threshold: Minimum quality score required
            max_response_time: Maximum acceptable response time

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        try:
            with self.lock:
                # Use provided max response time or default
                max_time = max_response_time or self.max_response_time

                # Analyze performance requirements
                perf_requirements = self._analyze_performance_requirements(context, speed_priority)

                # Find performance-optimal models
                optimal_models = self._find_performance_optimal_models(
                    perf_requirements,
                    quality_threshold,
                    max_time,
                    context
                )

                if not optimal_models:
                    # No models meet performance constraints, return fastest available
                    return self._get_fastest_model("No models meet performance constraints")

                # Select best performance-optimal model
                selected = self._select_performance_optimal_model(optimal_models, perf_requirements)

                provider_name, model_name = selected["key"].split("/", 1)
                performance_score = selected["performance_score"]
                expected_time = selected["expected_response_time"]

                reason = (f"Performance-optimized routing: ~{expected_time:.1f}s expected, "
                         f"performance score {performance_score:.1f}/10")

                return provider_name, model_name, reason

        except Exception as e:
            logger.error(f"Error in performance routing: {str(e)}")
            return "gemini", "gemini-2.5-flash", f"Performance routing failed: {str(e)}"

    def _analyze_performance_requirements(
        self,
        context: Dict[str, Any],
        speed_priority: float
    ) -> Dict[str, Any]:
        """Analyze performance requirements for the request

        Args:
            context: Request context analysis
            speed_priority: Speed vs quality priority

        Returns:
            Performance requirements dictionary
        """
        # Determine urgency based on task type and context
        task_type = context.get("scenario", "default")
        urgency_map = {
            "background": 0.2,    # Background tasks can be slow
            "default": 0.5,       # Normal priority
            "think": 0.3,         # Reasoning tasks can take time for quality
            "longContext": 0.4,   # Large context may need time
            "webSearch": 0.8      # Search tasks should be fast
        }

        urgency = urgency_map.get(task_type, 0.5)

        # Adjust based on content complexity
        complexity_score = context.get("complexity_score", 5)
        complexity_adjustment = (10 - complexity_score) / 10  # Higher complexity = lower urgency

        final_urgency = (urgency + speed_priority + complexity_adjustment) / 3

        # Determine acceptable response time based on urgency
        if final_urgency >= 0.8:
            max_acceptable_time = 5.0   # Very urgent
        elif final_urgency >= 0.6:
            max_acceptable_time = 15.0  # Moderately urgent
        elif final_urgency >= 0.4:
            max_acceptable_time = 30.0  # Normal
        else:
            max_acceptable_time = 60.0  # Can wait for quality

        return {
            "urgency": final_urgency,
            "speed_priority": speed_priority,
            "max_acceptable_time": max_acceptable_time,
            "task_type": task_type,
            "complexity_score": complexity_score,
            "requires_speed": final_urgency >= 0.7,
            "accepts_slower_for_quality": final_urgency <= 0.4
        }

    def _find_performance_optimal_models(
        self,
        perf_requirements: Dict[str, Any],
        quality_threshold: float,
        max_response_time: float,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find models that meet performance and quality constraints

        Args:
            perf_requirements: Performance requirements analysis
            quality_threshold: Minimum quality requirement
            max_response_time: Maximum acceptable response time
            context: Request context

        Returns:
            List of suitable models with performance information
        """
        suitable_models = []

        for model_key, metrics in self.performance_metrics.items():
            # Check response time constraint
            if metrics.average_response_time > max_response_time:
                continue

            # Check success rate constraint
            if metrics.success_rate < self.min_success_rate:
                continue

            # Get quality score from baseline (would be enhanced with real-time quality tracking)
            quality_score = self._get_model_quality_score(model_key)
            if quality_score < quality_threshold:
                continue

            # Check capability requirements
            if not self._check_model_capabilities(model_key, context):
                continue

            # Calculate performance score
            performance_score = self._calculate_performance_score(
                model_key, metrics, perf_requirements
            )

            suitable_models.append({
                "key": model_key,
                "performance_score": performance_score,
                "quality_score": quality_score,
                "expected_response_time": metrics.average_response_time,
                "success_rate": metrics.success_rate,
                "throughput": metrics.throughput,
                "metrics": metrics
            })

        # Sort by performance score
        suitable_models.sort(key=lambda x: x["performance_score"], reverse=True)

        return suitable_models

    def _calculate_performance_score(
        self,
        model_key: str,
        metrics: PerformanceMetrics,
        requirements: Dict[str, Any]
    ) -> float:
        """Calculate performance score for a model

        Args:
            model_key: Model identifier
            metrics: Performance metrics
            requirements: Performance requirements

        Returns:
            Performance score (0-10)
        """
        # Base scores (normalized to 0-10)
        speed_score = max(0, 10 - (metrics.average_response_time / 3))  # 30s = 0, 0s = 10
        reliability_score = metrics.success_rate * 10
        throughput_score = min(10, metrics.throughput / 5)  # 50 req/min = 10

        # Weight based on requirements
        speed_weight = requirements["speed_priority"]
        reliability_weight = 0.3
        throughput_weight = 1.0 - speed_weight - reliability_weight

        # Calculate weighted score
        performance_score = (
            speed_score * speed_weight +
            reliability_score * reliability_weight +
            throughput_score * throughput_weight
        )

        # Bonus for models that are significantly faster than required
        if metrics.average_response_time < requirements["max_acceptable_time"] * 0.5:
            performance_score += 1.0

        # Penalty for models near the time limit
        if metrics.average_response_time > requirements["max_acceptable_time"] * 0.8:
            performance_score -= 1.0

        return max(0, min(10, performance_score))

    def _select_performance_optimal_model(
        self,
        suitable_models: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select the most performance-optimal model from candidates

        Args:
            suitable_models: List of suitable models with performance info
            requirements: Performance requirements

        Returns:
            Selected model with performance information
        """
        if not suitable_models:
            return self._get_fallback_performance_model()

        # For high-urgency tasks, select the fastest option
        if requirements["requires_speed"]:
            return min(suitable_models, key=lambda x: x["expected_response_time"])

        # For quality-focused tasks, balance performance and quality
        if requirements["accepts_slower_for_quality"]:
            def balanced_score(model):
                perf_score = model["performance_score"]
                quality_score = model["quality_score"]
                return (perf_score * 0.4) + (quality_score * 0.6)

            return max(suitable_models, key=balanced_score)

        # Default: use highest performance score
        return suitable_models[0]

    def _get_fastest_model(self, reason: str) -> Tuple[str, str, str]:
        """Get the fastest available model

        Args:
            reason: Routing reason description

        Returns:
            Tuple of (provider_name, model_name, routing_reason)
        """
        if not self.performance_metrics:
            return "gemini", "gemini-2.5-flash", f"{reason} (no performance info)"

        # Find fastest model (lowest average response time)
        fastest = min(
            self.performance_metrics.items(),
            key=lambda x: x[1].average_response_time
        )

        provider_name, model_name = fastest[0].split("/", 1)
        return provider_name, model_name, reason

    def _get_fallback_performance_model(self) -> Dict[str, Any]:
        """Get fallback performance model information

        Returns:
            Fallback model configuration with performance info
        """
        return {
            "key": "gemini/gemini-2.5-flash",
            "performance_score": 7.5,
            "quality_score": 7.0,
            "expected_response_time": 2.5,
            "success_rate": 0.95,
            "throughput": 30.0
        }

    def _get_model_quality_score(self, model_key: str) -> float:
        """Get quality score for a model (from configuration or defaults)

        Args:
            model_key: Model identifier

        Returns:
            Quality score (0-10)
        """
        # Default quality scores (would be enhanced with real-time quality tracking)
        quality_scores = {
            "gemini/gemini-2.5-pro": 9.0,
            "gemini/gemini-2.5-flash": 7.0,
            "gemini/gemini-2.5-flash-8b": 6.0,
            "openrouter/anthropic/claude-3-haiku": 8.0,
            "openrouter/openai/gpt-4o-mini": 7.5,
            "openrouter/qwen/qwen3-coder-30b-instruct": 8.5,
            "openrouter/deepseek/deepseek-chat": 6.5
        }

        return quality_scores.get(model_key, 6.0)

    def _check_model_capabilities(self, model_key: str, context: Dict[str, Any]) -> bool:
        """Check if model has required capabilities

        Args:
            model_key: Model identifier
            context: Request context

        Returns:
            True if model meets capability requirements
        """
        # Default capabilities (would be enhanced with dynamic capability detection)
        capabilities = {
            "gemini/gemini-2.5-pro": ["code", "text", "analysis", "reasoning"],
            "gemini/gemini-2.5-flash": ["code", "text", "analysis"],
            "gemini/gemini-2.5-flash-8b": ["text", "simple_code"],
            "openrouter/anthropic/claude-3-haiku": ["text", "analysis", "reasoning"],
            "openrouter/openai/gpt-4o-mini": ["code", "text", "analysis"],
            "openrouter/qwen/qwen3-coder-30b-instruct": ["code", "agentic_coding"],
            "openrouter/deepseek/deepseek-chat": ["text", "code"]
        }

        model_caps = capabilities.get(model_key, [])
        required_caps = context.get("required_capabilities", [])

        # If no specific requirements, model is suitable
        if not required_caps:
            return True

        # Check if model has all required capabilities
        return all(cap in model_caps for cap in required_caps)

    def record_performance_metrics(
        self,
        provider_name: str,
        model_name: str,
        response_time: float,
        success: bool,
        tokens_processed: int = 0
    ) -> None:
        """Record performance metrics for a model

        Args:
            provider_name: Provider name
            model_name: Model name
            response_time: Response time in seconds
            success: Whether the request was successful
            tokens_processed: Number of tokens processed (optional)
        """
        model_key = f"{provider_name}/{model_name}"
        current_time = time.time()

        with self.lock:
            if model_key not in self.performance_metrics:
                # Initialize new model metrics
                self.performance_metrics[model_key] = PerformanceMetrics(
                    response_times=deque(maxlen=self.metrics_window_size),
                    success_rate=1.0 if success else 0.0,
                    throughput=0.0,
                    error_count=0 if success else 1,
                    total_requests=1,
                    last_updated=current_time,
                    average_response_time=response_time,
                    p95_response_time=response_time
                )
            else:
                metrics = self.performance_metrics[model_key]

                # Update response times
                metrics.response_times.append(response_time)

                # Update request counters
                metrics.total_requests += 1
                if not success:
                    metrics.error_count += 1

                # Recalculate success rate
                metrics.success_rate = 1.0 - (metrics.error_count / metrics.total_requests)

                # Recalculate average response time
                if metrics.response_times:
                    metrics.average_response_time = sum(metrics.response_times) / len(metrics.response_times)

                    # Calculate 95th percentile
                    sorted_times = sorted(metrics.response_times)
                    p95_index = int(len(sorted_times) * 0.95)
                    metrics.p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]

                # Update throughput (requests per minute)
                time_window = current_time - metrics.last_updated
                if time_window > 0:
                    requests_in_window = len(metrics.response_times)
                    metrics.throughput = (requests_in_window / time_window) * 60

                metrics.last_updated = current_time

        logger.debug(f"Recorded performance: {model_key} - {response_time:.2f}s, success={success}")

    def get_performance_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get performance summary for all tracked models

        Returns:
            Dictionary mapping model keys to performance summaries
        """
        with self.lock:
            summary = {}
            for model_key, metrics in self.performance_metrics.items():
                summary[model_key] = {
                    "average_response_time": metrics.average_response_time,
                    "p95_response_time": metrics.p95_response_time,
                    "success_rate": metrics.success_rate,
                    "throughput": metrics.throughput,
                    "total_requests": metrics.total_requests,
                    "error_count": metrics.error_count,
                    "last_updated": metrics.last_updated
                }

            return summary

    def reset_performance_metrics(self, model_key: Optional[str] = None) -> None:
        """Reset performance metrics

        Args:
            model_key: Specific model to reset, or None to reset all
        """
        with self.lock:
            if model_key:
                if model_key in self.performance_metrics:
                    del self.performance_metrics[model_key]
                    logger.info(f"Reset performance metrics for {model_key}")
            else:
                self.performance_metrics.clear()
                logger.info("Reset all performance metrics")

                # Reinitialize baselines
                self._initialize_performance_baselines()
