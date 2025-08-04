#!/usr/bin/env python3
"""
Configuration Registry - Intelligent orchestrator for decoupled configuration management.

This module serves as the intelligent orchestrator for the decoupled configuration
system, coordinating between specialized configuration components while maintaining
backward compatibility with the original monolithic config.py interface.

Architecture Pattern: Intelligent Orchestrator with Decoupled Specialists
- CoreConfigManager: Foundation configuration management
- RoutingConfigManager: Routing-specific configuration (26+ methods)
- ModelConfigManager: Model resolution and assignments
- EnvironmentConfigLoader: Environment variable processing

Features:
- Thread-safe singleton pattern for global configuration access
- Backward-compatible public API preservation
- Configuration component coordination and lifecycle management
- Unified configuration loading with proper precedence
- Context managers for temporary configuration overrides
- Comprehensive validation and debugging utilities

Date: 2025-08-04
Architecture: Configuration Registry Pattern (Intelligent Orchestrator)
"""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import specialized configuration components
from .core_config import CoreConfigManager, ConfigurationError
from .routing_config import RoutingConfigManager
from .model_config import ModelConfigManager
from .env_loader import EnvironmentConfigLoader

logger = logging.getLogger(__name__)

# Thread-safe singleton pattern for configuration
_config_lock = threading.Lock()
_config_instance: Optional["GeminiConfig"] = None


class GeminiConfig:
    """
    Intelligent Configuration Orchestrator

    This class orchestrates specialized configuration components while maintaining
    the original public API for backward compatibility. It follows the project's
    intelligent orchestrator pattern by coordinating between decoupled specialists.
    """

    # Hard-coded defaults for models (moved from core_config for specialization)
    DEFAULT_MODEL_CONFIG = {
        "models": {
            "nicknames": {
                "flash": "gemini-2.5-flash",
                "pro": "gemini-2.5-pro",
                "flash-8b": "gemini-2.5-flash-8b",
                "flash-exp": "gemini-2.5-flash-exp-0827",
                "pro-exp": "gemini-2.5-pro-exp-0827",
            },
            "assignments": {
                "quick_query": "flash",
                "analyze_code": "pro",
                "analyze_codebase": "pro",
                "gemini_quick_query": "flash",
                "gemini_analyze_code": "pro",
                "gemini_codebase_analysis": "pro",
                "pre_edit": "flash",
                "pre_commit": "pro",
                "session_summary": "flash",
            },
        },
    }

    # Default routing configuration
    DEFAULT_ROUTING_CONFIG = {
        "routing": {
            "enabled": False,  # Disabled by default for backward compatibility
            "providers": {
                "gemini": {
                    "name": "gemini",
                    "api_base_url": "https://generativelanguage.googleapis.com/v1beta/models/",
                    "api_key_env": "GEMINI_API_KEY",
                    "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-8b"],
                    "transformers": ["gemini"],
                    "enabled": True,
                },
                "openrouter": {
                    "name": "openrouter",
                    "api_base_url": "https://openrouter.ai/api/v1/chat/completions",
                    "api_key_env": "OPENROUTER_API_KEY",
                    "models": ["google/gemini-2.5-pro-preview", "anthropic/claude-3.5-sonnet"],
                    "transformers": ["openrouter"],
                    "enabled": False,
                },
            },
            "scenarios": {
                "default": "gemini,gemini-2.5-flash",
                "background": "gemini,gemini-2.5-flash-8b",
                "think": "gemini,gemini-2.5-pro",
                "longContext": "gemini,gemini-2.5-pro",
                "webSearch": "gemini,gemini-2.5-flash",
            },
            "thresholds": {
                "long_context_tokens": 60000,
                "background_task_size": 1000,
            },
            "fallback_strategy": "provider_cascade",
            "retry_attempts": 2,
            "timeout_ms": 30000,
            # Advanced routing configurations
            "preferences": {
                "routing_strategy": "balanced",
                "speed_priority": 0.7,
                "cost_sensitivity": 0.5,
                "quality_threshold": 6.0,
                "max_acceptable_response_time": 30.0,
                "enable_adaptive_routing": True,
                "enable_load_balancing": False,
            },
            "performance": {
                "max_response_time": 30.0,
                "min_success_rate": 0.85,
                "metrics_window_size": 100,
                "performance_weight": 0.7,
                "quality_weight": 0.3,
                "enable_performance_monitoring": True,
                "alert_on_degradation": True,
                "degradation_threshold": 0.8,
            },
            "cost_optimization": {
                "enable_cost_tracking": True,
                "budget_constraints": {
                    "daily_budget": None,
                    "request_budget": None,
                    "warn_at_percentage": 80,
                },
                "cost_models": {
                    "gemini/gemini-2.5-flash": {"input": 0.075, "output": 0.3},
                    "gemini/gemini-2.5-pro": {"input": 1.25, "output": 5.0},
                    "gemini/gemini-2.5-flash-8b": {"input": 0.037, "output": 0.15},
                },
                "quality_scores": {
                    "gemini/gemini-2.5-pro": 9.0,
                    "gemini/gemini-2.5-flash": 7.0,
                    "gemini/gemini-2.5-flash-8b": 6.0,
                },
            },
            "telemetry": {
                "enabled": True,
                "max_records": 10000,
                "analytics_window_hours": 24,
                "enable_detailed_logging": True,
                "enable_alerts": True,
                "alert_thresholds": {
                    "success_rate_warning": 0.90,
                    "success_rate_critical": 0.80,
                    "response_time_warning": 15.0,
                    "response_time_critical": 30.0,
                    "cost_increase_warning": 1.5,
                    "cost_increase_critical": 2.0,
                },
            },
        },
    }

    def __init__(self):
        """Initialize configuration orchestrator with specialized components"""
        self._config: Dict[str, Any] = {}
        self._load_timestamp: float = 0

        # Initialize specialized components
        self._core_manager = CoreConfigManager()
        self._env_loader = EnvironmentConfigLoader()
        self._routing_manager: Optional[RoutingConfigManager] = None
        self._model_manager: Optional[ModelConfigManager] = None

        # Load configuration
        self._reload()

        logger.info("Configuration orchestrator initialized with decoupled components")

    def _reload(self) -> None:
        """Reload configuration from all sources with proper precedence"""
        try:
            # Step 1: Load base configuration (defaults + file)
            self._config = self._core_manager.load_base_config()

            # Step 2: Merge model defaults
            self._merge_config(self._config, self.DEFAULT_MODEL_CONFIG)

            # Step 3: Merge routing defaults
            self._merge_config(self._config, self.DEFAULT_ROUTING_CONFIG)

            # Step 4: Layer environment variables
            env_config = self._env_loader.load_env_config()
            self._merge_config(self._config, env_config)

            # Step 5: Validate and normalize
            validation_warnings = self._core_manager.validate_and_normalize(self._config)

            # Step 6: Initialize specialized managers
            self._routing_manager = RoutingConfigManager(self._config.get("routing", {}))
            self._model_manager = ModelConfigManager(self._config.get("models", {}))

            # Step 7: Apply force-model override if present
            self._model_manager.apply_force_model_override()

            self._load_timestamp = time.time()

            # Validate specialized components
            routing_warnings = self._routing_manager.validate_routing_config()
            model_issues = self._model_manager.validate_assignments()

            if routing_warnings:
                logger.warning(f"Routing configuration issues: {len(routing_warnings)}")
            if model_issues:
                logger.warning(f"Model assignment issues: {len(model_issues)}")

            logger.info("Configuration loaded successfully with all components")

        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            # Fallback to safe defaults
            self._config = self._get_safe_fallback_config()
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def _get_safe_fallback_config(self) -> Dict[str, Any]:
        """Get safe fallback configuration"""
        safe_config = self._core_manager._deep_copy_dict(self._core_manager.DEFAULT_CONFIG)
        self._merge_config(safe_config, self.DEFAULT_MODEL_CONFIG)
        return safe_config

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge configuration dictionaries"""
        self._core_manager._merge_config(base, override)

    # ===== PUBLIC API - BACKWARD COMPATIBILITY =====
    # Model configuration methods (delegated to ModelConfigManager)

    def get_model(self, tool_name: str, explicit_model: Optional[str] = None) -> str:
        """Get model name for a specific tool with load precedence"""
        if self._model_manager:
            return self._model_manager.get_model(tool_name, explicit_model)
        return "gemini-2.5-flash"  # Safe fallback

    def validate_model_name(self, model_name: str) -> bool:
        """Validate that a model name is acceptable"""
        if self._model_manager:
            return self._model_manager.validate_model_name(model_name)
        return model_name.startswith("gemini-")  # Safe fallback

    # Core configuration methods (delegated to CoreConfigManager)

    def get_limit(self, limit_name: str, explicit_limit: Optional[int] = None) -> int:
        """Get configuration limit with load precedence"""
        return self._core_manager.get_limit(self._config, limit_name, explicit_limit)

    def get_timeout(self, timeout_name: str, explicit_timeout: Optional[int] = None) -> int:
        """Get timeout configuration with load precedence"""
        return self._core_manager.get_timeout(self._config, timeout_name, explicit_timeout)

    def get_security_setting(self, setting_name: str, explicit_value: Optional[bool] = None) -> bool:
        """Get security setting with load precedence"""
        return self._core_manager.get_security_setting(self._config, setting_name, explicit_value)

    def get_execution_setting(self, setting_name: str, explicit_value: Optional[bool] = None) -> bool:
        """Get execution setting with load precedence"""
        return self._core_manager.get_execution_setting(self._config, setting_name, explicit_value)

    # Routing configuration methods (delegated to RoutingConfigManager)

    def is_routing_enabled(self) -> bool:
        """Check if routing is enabled"""
        if self._routing_manager:
            return self._routing_manager.is_routing_enabled()
        return False

    def get_routing_config(self) -> Dict[str, Any]:
        """Get the complete routing configuration"""
        if self._routing_manager:
            return self._routing_manager.get_routing_config()
        return {}

    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific provider"""
        if self._routing_manager:
            return self._routing_manager.get_provider_config(provider_name)
        return None

    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names"""
        if self._routing_manager:
            return self._routing_manager.get_enabled_providers()
        return []

    def get_scenario_config(self, scenario: str) -> Optional[str]:
        """Get model configuration for a specific scenario"""
        if self._routing_manager:
            return self._routing_manager.get_scenario_config(scenario)
        return None

    def get_routing_threshold(self, threshold_name: str) -> int:
        """Get routing threshold value"""
        if self._routing_manager:
            return self._routing_manager.get_routing_threshold(threshold_name)
        return 0

    def get_fallback_strategy(self) -> str:
        """Get the configured fallback strategy"""
        if self._routing_manager:
            return self._routing_manager.get_fallback_strategy()
        return "provider_cascade"

    # Advanced routing configuration accessors (all 26 methods)

    def get_routing_preferences(self) -> Dict[str, Any]:
        """Get routing preferences configuration"""
        return self._routing_manager.get_routing_preferences() if self._routing_manager else {}

    def get_routing_strategy(self) -> str:
        """Get the configured routing strategy"""
        return self._routing_manager.get_routing_strategy() if self._routing_manager else "balanced"

    def get_speed_priority(self) -> float:
        """Get speed priority weight (0.0-1.0)"""
        return self._routing_manager.get_speed_priority() if self._routing_manager else 0.7

    def get_cost_sensitivity(self) -> float:
        """Get cost sensitivity (0.0-1.0)"""
        return self._routing_manager.get_cost_sensitivity() if self._routing_manager else 0.5

    def get_quality_threshold(self) -> float:
        """Get minimum quality threshold (0-10)"""
        return self._routing_manager.get_quality_threshold() if self._routing_manager else 6.0

    def get_max_acceptable_response_time(self) -> float:
        """Get maximum acceptable response time in seconds"""
        return self._routing_manager.get_max_acceptable_response_time() if self._routing_manager else 30.0

    def is_adaptive_routing_enabled(self) -> bool:
        """Check if adaptive routing is enabled"""
        return self._routing_manager.is_adaptive_routing_enabled() if self._routing_manager else True

    def is_load_balancing_enabled(self) -> bool:
        """Check if load balancing is enabled"""
        return self._routing_manager.is_load_balancing_enabled() if self._routing_manager else False

    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance monitoring configuration"""
        return self._routing_manager.get_performance_config() if self._routing_manager else {}

    def get_max_response_time(self) -> float:
        """Get maximum response time in seconds"""
        return self._routing_manager.get_max_response_time() if self._routing_manager else 30.0

    def get_min_success_rate(self) -> float:
        """Get minimum success rate"""
        return self._routing_manager.get_min_success_rate() if self._routing_manager else 0.85

    def get_metrics_window_size(self) -> int:
        """Get metrics window size for performance tracking"""
        return self._routing_manager.get_metrics_window_size() if self._routing_manager else 100

    def is_performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled"""
        return self._routing_manager.is_performance_monitoring_enabled() if self._routing_manager else True

    def get_cost_optimization_config(self) -> Dict[str, Any]:
        """Get cost optimization configuration"""
        return self._routing_manager.get_cost_optimization_config() if self._routing_manager else {}

    def is_cost_tracking_enabled(self) -> bool:
        """Check if cost tracking is enabled"""
        return self._routing_manager.is_cost_tracking_enabled() if self._routing_manager else True

    def get_cost_models(self) -> Dict[str, Dict[str, float]]:
        """Get cost models configuration"""
        return self._routing_manager.get_cost_models() if self._routing_manager else {}

    def get_quality_scores(self) -> Dict[str, float]:
        """Get quality scores configuration"""
        return self._routing_manager.get_quality_scores() if self._routing_manager else {}

    def get_daily_budget(self) -> Optional[float]:
        """Get daily budget limit"""
        return self._routing_manager.get_daily_budget() if self._routing_manager else None

    def get_request_budget(self) -> Optional[float]:
        """Get per-request budget limit"""
        return self._routing_manager.get_request_budget() if self._routing_manager else None

    def get_telemetry_config(self) -> Dict[str, Any]:
        """Get telemetry configuration"""
        return self._routing_manager.get_telemetry_config() if self._routing_manager else {}

    def is_telemetry_enabled(self) -> bool:
        """Check if telemetry is enabled"""
        return self._routing_manager.is_telemetry_enabled() if self._routing_manager else True

    def get_telemetry_max_records(self) -> int:
        """Get maximum telemetry records to keep"""
        return self._routing_manager.get_telemetry_max_records() if self._routing_manager else 10000

    def get_analytics_window_hours(self) -> int:
        """Get analytics window in hours"""
        return self._routing_manager.get_analytics_window_hours() if self._routing_manager else 24

    def is_detailed_logging_enabled(self) -> bool:
        """Check if detailed logging is enabled"""
        return self._routing_manager.is_detailed_logging_enabled() if self._routing_manager else True

    def are_alerts_enabled(self) -> bool:
        """Check if alerts are enabled"""
        return self._routing_manager.are_alerts_enabled() if self._routing_manager else True

    def get_alert_thresholds(self) -> Dict[str, float]:
        """Get alert thresholds configuration"""
        return self._routing_manager.get_alert_thresholds() if self._routing_manager else {}

    # Utility methods

    def reload_config(self) -> None:
        """Force reload configuration from all sources"""
        logger.info("Reloading configuration...")
        self._reload()

    def get_raw_config(self) -> Dict[str, Any]:
        """Get the raw configuration dictionary (for debugging)"""
        return self._core_manager._deep_copy_dict(self._config)

    def save_config(self, config_path: Optional[Path] = None) -> None:
        """Save current configuration to file"""
        self._core_manager.save_config(self._config, config_path)

    # Configuration summary and debugging

    def get_config_summary(self) -> Dict[str, Any]:
        """Get comprehensive configuration summary"""
        summary = {
            "load_timestamp": self._load_timestamp,
            "components_initialized": {
                "core_manager": self._core_manager is not None,
                "routing_manager": self._routing_manager is not None,
                "model_manager": self._model_manager is not None,
                "env_loader": self._env_loader is not None,
            }
        }

        # Add component summaries
        if self._core_manager:
            summary["core"] = self._core_manager.get_config_summary(self._config)
        if self._routing_manager:
            summary["routing"] = self._routing_manager.get_config_summary()
        if self._model_manager:
            summary["model"] = self._model_manager.get_model_summary()
        if self._env_loader:
            summary["environment"] = self._env_loader.get_env_summary()

        return summary


# ===== MODULE-LEVEL SINGLETON ACCESS =====

def get_config() -> GeminiConfig:
    """Get the global configuration instance (thread-safe singleton)"""
    global _config_instance

    if _config_instance is None:
        with _config_lock:
            # Double-check locking pattern
            if _config_instance is None:
                _config_instance = GeminiConfig()

    return _config_instance


def reload_config() -> None:
    """Force reload the global configuration"""
    global _config_instance

    with _config_lock:
        if _config_instance is not None:
            _config_instance.reload_config()
        else:
            _config_instance = GeminiConfig()


# ===== CONVENIENCE FUNCTIONS FOR BACKWARD COMPATIBILITY =====

# Model configuration convenience functions
def get_model(tool_name: str, explicit_model: Optional[str] = None) -> str:
    """Get model name for a tool (convenience function)"""
    return get_config().get_model(tool_name, explicit_model)

# Core configuration convenience functions
def get_limit(limit_name: str, explicit_limit: Optional[int] = None) -> int:
    """Get configuration limit (convenience function)"""
    return get_config().get_limit(limit_name, explicit_limit)

def get_timeout(timeout_name: str, explicit_timeout: Optional[int] = None) -> int:
    """Get timeout configuration (convenience function)"""
    return get_config().get_timeout(timeout_name, explicit_timeout)

def is_security_enabled(setting_name: str, explicit_value: Optional[bool] = None) -> bool:
    """Check if security setting is enabled (convenience function)"""
    return get_config().get_security_setting(setting_name, explicit_value)

def is_execution_enabled(setting_name: str, explicit_value: Optional[bool] = None) -> bool:
    """Check if execution setting is enabled (convenience function)"""
    return get_config().get_execution_setting(setting_name, explicit_value)

# Routing configuration convenience functions
def is_routing_enabled() -> bool:
    """Check if routing is enabled (convenience function)"""
    return get_config().is_routing_enabled()

def get_enabled_providers() -> List[str]:
    """Get list of enabled providers (convenience function)"""
    return get_config().get_enabled_providers()

def get_provider_config(provider_name: str) -> Optional[Dict[str, Any]]:
    """Get provider configuration (convenience function)"""
    return get_config().get_provider_config(provider_name)

def get_scenario_config(scenario: str) -> Optional[str]:
    """Get scenario configuration (convenience function)"""
    return get_config().get_scenario_config(scenario)

def get_routing_threshold(threshold_name: str) -> int:
    """Get routing threshold (convenience function)"""
    return get_config().get_routing_threshold(threshold_name)

def get_routing_strategy() -> str:
    """Get the configured routing strategy (convenience function)"""
    return get_config().get_routing_strategy()

# Tool registration convenience function
def register_tool_if_missing(tool_name: str, default_model_nickname: str) -> None:
    """Register a new tool with default model assignment if missing"""
    config = get_config()
    if config._model_manager:
        config._model_manager.register_tool_if_missing(tool_name, default_model_nickname)


# ===== CONTEXT MANAGER FOR TEMPORARY OVERRIDES =====

class ConfigOverride:
    """Context manager for temporary configuration overrides"""

    def __init__(self, **overrides):
        self.overrides = overrides
        self.original_config = None

    def __enter__(self):
        config = get_config()
        self.original_config = config.get_raw_config()

        # Apply overrides
        for key, value in self.overrides.items():
            if hasattr(config, "_config"):
                config._config[key] = value

        return config

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_config:
            config = get_config()
            if hasattr(config, "_config"):
                config._config = self.original_config


# ===== PUBLIC API EXPORTS =====

# Export main public API for backward compatibility
__all__ = [
    # Main classes
    "GeminiConfig",
    "ConfigurationError",
    "ConfigOverride",

    # Singleton access
    "get_config",
    "reload_config",

    # Convenience functions
    "get_model",
    "get_limit",
    "get_timeout",
    "is_security_enabled",
    "is_execution_enabled",
    "is_routing_enabled",
    "get_enabled_providers",
    "get_provider_config",
    "get_scenario_config",
    "get_routing_threshold",
    "get_routing_strategy",
    "register_tool_if_missing",

    # Specialized components (for advanced usage)
    "CoreConfigManager",
    "RoutingConfigManager",
    "ModelConfigManager",
    "EnvironmentConfigLoader",
]
