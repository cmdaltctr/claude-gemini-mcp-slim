#!/usr/bin/env python3
"""
Routing Configuration Manager - Specialized component for routing-related configuration.

This module provides routing-specific configuration management following the
project's decoupled architecture pattern. It handles all routing preferences,
performance settings, cost optimization, and telemetry configurations.

Features:
- Routing strategy configuration (performance, cost, quality, balanced)
- Performance monitoring settings and thresholds
- Cost optimization models and budget constraints
- Telemetry and analytics configuration
- Provider and scenario management
- Granular routing preferences and thresholds

Date: 2025-08-04
Architecture: Configuration Specialist Pattern
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RoutingConfigManager:
    """
    Specialized configuration manager for routing-related settings.

    This class manages all 26+ routing configuration methods that were previously
    in the monolithic config.py, following single responsibility principle and
    the project's decoupled architecture pattern.
    """

    def __init__(self, routing_config: Dict[str, Any]):
        """Initialize routing configuration manager

        Args:
            routing_config: Complete routing configuration dictionary
        """
        self._routing_config = routing_config or {}
        logger.debug("Initialized routing configuration manager")

    # Core routing configuration
    def is_routing_enabled(self) -> bool:
        """Check if routing is enabled"""
        return self._routing_config.get("enabled", False)

    def get_routing_config(self) -> Dict[str, Any]:
        """Get the complete routing configuration"""
        return self._routing_config

    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific provider"""
        providers = self._routing_config.get("providers", {})
        return providers.get(provider_name)

    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names"""
        providers = self._routing_config.get("providers", {})
        return [name for name, config in providers.items() if config.get("enabled", False)]

    def get_scenario_config(self, scenario: str) -> Optional[str]:
        """Get model configuration for a specific scenario"""
        scenarios = self._routing_config.get("scenarios", {})
        return scenarios.get(scenario)

    def get_routing_threshold(self, threshold_name: str) -> int:
        """Get routing threshold value"""
        thresholds = self._routing_config.get("thresholds", {})
        defaults = {
            "long_context_tokens": 60000,
            "background_task_size": 1000,
        }
        return thresholds.get(threshold_name, defaults.get(threshold_name, 0))

    def get_fallback_strategy(self) -> str:
        """Get the configured fallback strategy"""
        return self._routing_config.get("fallback_strategy", "provider_cascade")

    # Advanced routing preferences
    def get_routing_preferences(self) -> Dict[str, Any]:
        """Get routing preferences configuration"""
        return self._routing_config.get("preferences", {})

    def get_routing_strategy(self) -> str:
        """Get the configured routing strategy"""
        return self._routing_config.get("preferences", {}).get("routing_strategy", "balanced")

    def get_speed_priority(self) -> float:
        """Get speed priority weight (0.0-1.0)"""
        return self._routing_config.get("preferences", {}).get("speed_priority", 0.7)

    def get_cost_sensitivity(self) -> float:
        """Get cost sensitivity (0.0-1.0)"""
        return self._routing_config.get("preferences", {}).get("cost_sensitivity", 0.5)

    def get_quality_threshold(self) -> float:
        """Get minimum quality threshold (0-10)"""
        return self._routing_config.get("preferences", {}).get("quality_threshold", 6.0)

    def get_max_acceptable_response_time(self) -> float:
        """Get maximum acceptable response time in seconds"""
        return self._routing_config.get("preferences", {}).get("max_acceptable_response_time", 30.0)

    def is_adaptive_routing_enabled(self) -> bool:
        """Check if adaptive routing is enabled"""
        return self._routing_config.get("preferences", {}).get("enable_adaptive_routing", True)

    def is_load_balancing_enabled(self) -> bool:
        """Check if load balancing is enabled"""
        return self._routing_config.get("preferences", {}).get("enable_load_balancing", False)

    # Performance monitoring configuration
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance monitoring configuration"""
        return self._routing_config.get("performance", {})

    def get_max_response_time(self) -> float:
        """Get maximum response time in seconds"""
        return self._routing_config.get("performance", {}).get("max_response_time", 30.0)

    def get_min_success_rate(self) -> float:
        """Get minimum success rate"""
        return self._routing_config.get("performance", {}).get("min_success_rate", 0.85)

    def get_metrics_window_size(self) -> int:
        """Get metrics window size for performance tracking"""
        return self._routing_config.get("performance", {}).get("metrics_window_size", 100)

    def is_performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled"""
        return self._routing_config.get("performance", {}).get("enable_performance_monitoring", True)

    # Cost optimization configuration
    def get_cost_optimization_config(self) -> Dict[str, Any]:
        """Get cost optimization configuration"""
        return self._routing_config.get("cost_optimization", {})

    def is_cost_tracking_enabled(self) -> bool:
        """Check if cost tracking is enabled"""
        return self._routing_config.get("cost_optimization", {}).get("enable_cost_tracking", True)

    def get_cost_models(self) -> Dict[str, Dict[str, float]]:
        """Get cost models configuration"""
        return self._routing_config.get("cost_optimization", {}).get("cost_models", {})

    def get_quality_scores(self) -> Dict[str, float]:
        """Get quality scores configuration"""
        return self._routing_config.get("cost_optimization", {}).get("quality_scores", {})

    def get_daily_budget(self) -> Optional[float]:
        """Get daily budget limit"""
        return (self._routing_config.get("cost_optimization", {})
                .get("budget_constraints", {}).get("daily_budget"))

    def get_request_budget(self) -> Optional[float]:
        """Get per-request budget limit"""
        return (self._routing_config.get("cost_optimization", {})
                .get("budget_constraints", {}).get("request_budget"))

    # Telemetry configuration
    def get_telemetry_config(self) -> Dict[str, Any]:
        """Get telemetry configuration"""
        return self._routing_config.get("telemetry", {})

    def is_telemetry_enabled(self) -> bool:
        """Check if telemetry is enabled"""
        return self._routing_config.get("telemetry", {}).get("enabled", True)

    def get_telemetry_max_records(self) -> int:
        """Get maximum telemetry records to keep"""
        return self._routing_config.get("telemetry", {}).get("max_records", 10000)

    def get_analytics_window_hours(self) -> int:
        """Get analytics window in hours"""
        return self._routing_config.get("telemetry", {}).get("analytics_window_hours", 24)

    def is_detailed_logging_enabled(self) -> bool:
        """Check if detailed logging is enabled"""
        return self._routing_config.get("telemetry", {}).get("enable_detailed_logging", True)

    def are_alerts_enabled(self) -> bool:
        """Check if alerts are enabled"""
        return self._routing_config.get("telemetry", {}).get("enable_alerts", True)

    def get_alert_thresholds(self) -> Dict[str, float]:
        """Get alert thresholds configuration"""
        return self._routing_config.get("telemetry", {}).get("alert_thresholds", {})

    # Configuration validation
    def validate_routing_config(self) -> List[str]:
        """Validate routing configuration and return any warnings

        Returns:
            List of validation warning messages
        """
        warnings = []

        # Validate routing strategy
        valid_strategies = {"performance", "cost", "quality", "balanced"}
        strategy = self.get_routing_strategy()
        if strategy not in valid_strategies:
            warnings.append(f"Invalid routing strategy '{strategy}', should be one of {valid_strategies}")

        # Validate speed priority
        speed_priority = self.get_speed_priority()
        if not 0.0 <= speed_priority <= 1.0:
            warnings.append(f"Speed priority {speed_priority} should be between 0.0 and 1.0")

        # Validate cost sensitivity
        cost_sensitivity = self.get_cost_sensitivity()
        if not 0.0 <= cost_sensitivity <= 1.0:
            warnings.append(f"Cost sensitivity {cost_sensitivity} should be between 0.0 and 1.0")

        # Validate quality threshold
        quality_threshold = self.get_quality_threshold()
        if not 0.0 <= quality_threshold <= 10.0:
            warnings.append(f"Quality threshold {quality_threshold} should be between 0.0 and 10.0")

        # Validate response time limits
        max_response_time = self.get_max_response_time()
        if max_response_time <= 0:
            warnings.append(f"Max response time {max_response_time} should be positive")

        max_acceptable_time = self.get_max_acceptable_response_time()
        if max_acceptable_time <= 0:
            warnings.append(f"Max acceptable response time {max_acceptable_time} should be positive")

        # Validate success rate
        min_success_rate = self.get_min_success_rate()
        if not 0.0 <= min_success_rate <= 1.0:
            warnings.append(f"Min success rate {min_success_rate} should be between 0.0 and 1.0")

        # Validate telemetry settings
        max_records = self.get_telemetry_max_records()
        if max_records <= 0:
            warnings.append(f"Telemetry max records {max_records} should be positive")

        window_hours = self.get_analytics_window_hours()
        if window_hours <= 0:
            warnings.append(f"Analytics window hours {window_hours} should be positive")

        if warnings:
            for warning in warnings:
                logger.warning(f"Routing config validation: {warning}")

        return warnings

    # Configuration updating methods
    def update_routing_preferences(self, **kwargs) -> None:
        """Update routing preferences

        Args:
            **kwargs: Routing preference key-value pairs to update
        """
        preferences = self._routing_config.setdefault("preferences", {})
        preferences.update(kwargs)
        logger.debug(f"Updated routing preferences: {kwargs}")

    def update_performance_config(self, **kwargs) -> None:
        """Update performance configuration

        Args:
            **kwargs: Performance config key-value pairs to update
        """
        performance = self._routing_config.setdefault("performance", {})
        performance.update(kwargs)
        logger.debug(f"Updated performance config: {kwargs}")

    def update_telemetry_config(self, **kwargs) -> None:
        """Update telemetry configuration

        Args:
            **kwargs: Telemetry config key-value pairs to update
        """
        telemetry = self._routing_config.setdefault("telemetry", {})
        telemetry.update(kwargs)
        logger.debug(f"Updated telemetry config: {kwargs}")

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current routing configuration

        Returns:
            Dictionary with key routing configuration values
        """
        return {
            "routing_enabled": self.is_routing_enabled(),
            "routing_strategy": self.get_routing_strategy(),
            "enabled_providers": self.get_enabled_providers(),
            "performance_monitoring": self.is_performance_monitoring_enabled(),
            "cost_tracking": self.is_cost_tracking_enabled(),
            "telemetry_enabled": self.is_telemetry_enabled(),
            "adaptive_routing": self.is_adaptive_routing_enabled(),
            "load_balancing": self.is_load_balancing_enabled(),
            "speed_priority": self.get_speed_priority(),
            "quality_threshold": self.get_quality_threshold(),
            "max_response_time": self.get_max_response_time(),
        }


# Export main API
__all__ = [
    "RoutingConfigManager",
]
