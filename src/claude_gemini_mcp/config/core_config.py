#!/usr/bin/env python3
"""
Core Configuration Manager - Foundation component for basic configuration management.

This module provides the core configuration management functionality following the
project's decoupled architecture pattern. It handles configuration loading, merging,
validation, and basic accessor methods for limits, timeouts, and settings.

Features:
- Configuration file loading and merging
- Deep configuration merging with precedence
- Validation and normalization of core settings
- Basic accessor methods for limits, timeouts, security, execution
- Configuration persistence and debugging utilities

Date: 2025-08-04
Architecture: Configuration Foundation Pattern
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails"""
    pass


class CoreConfigManager:
    """
    Foundation configuration manager for core settings.

    This class handles the fundamental configuration management operations:
    loading, merging, validation, and basic accessors. It serves as the base
    for the specialized configuration components.
    """

    # Hard-coded defaults (lowest priority)
    DEFAULT_CONFIG = {
        # Size and content limits
        "limits": {
            "max_file_size": 81920,  # 80KB
            "max_lines": 800,
            "max_prompt_size": 1000000,  # 1MB
            "max_codebase_size": 500000,  # 500KB
            "max_context_window": 1048576,  # 1M tokens equivalent
            "sanitization_max_length": 100000,
            "max_codebase_analysis_size": 300000,  # 300KB for codebase analysis
            "sanitization_query_divisor": 100,  # Division factor for query sanitization
            "sanitization_context_divisor": 20,  # Division factor for context sanitization
        },
        # Timeout configurations
        "timeouts": {
            "cli_timeout": 60,  # seconds
            "api_timeout": 30,  # seconds
            "stream_timeout": 90,  # seconds
            "analysis_timeout": 300,  # 5 minutes for large analysis
        },
        # API configuration paths
        "api_config_paths": [
            "~/.config/claude-code/mcp_config.json",
            "~/Library/Application Support/Claude/claude_desktop_config.json",
            ".env",
            "gemini/.env",
        ],
        # Security settings
        "security": {
            "enable_sanitization": True,
            "allow_path_traversal": False,
            "allowed_extensions": [
                ".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs", ".vue",
                ".html", ".css", ".scss", ".sass", ".jsx", ".tsx", ".json",
                ".yaml", ".yml", ".toml", ".md", ".txt", ".go", ".php",
                ".rb", ".swift", ".kt", ".scala", ".sh", ".bat", ".ps1",
            ],
        },
        # CLI and execution settings
        "execution": {
            "prefer_api_over_cli": True,
            "enable_progress_indicators": True,
            "enable_markdown_conversion": True,
            "enable_streaming": True,
            "max_parallel_processes": 4,
        },
    }

    def __init__(self):
        """Initialize core configuration manager"""
        self._config: Dict[str, Any] = {}
        self._config_file_path: Optional[Path] = None
        self._load_timestamp: float = 0
        logger.debug("Initialized core configuration manager")

    def load_base_config(self) -> Dict[str, Any]:
        """Load base configuration with defaults and file config

        Returns:
            Base configuration dictionary
        """
        try:
            # Start with hard-coded defaults
            base_config = self._deep_copy_dict(self.DEFAULT_CONFIG)

            # Layer: config.json file (if exists)
            config_file = self._find_config_file()
            if config_file:
                self._config_file_path = config_file
                file_config = self._load_config_file(config_file)
                self._merge_config(base_config, file_config)
                logger.info(f"Loaded configuration from: {config_file}")

            self._load_timestamp = time.time()
            logger.debug("Base configuration loaded successfully")
            return base_config

        except Exception as e:
            logger.error(f"Base configuration loading failed: {e}")
            # Fallback to defaults if loading fails
            return self._deep_copy_dict(self.DEFAULT_CONFIG)

    def merge_config(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> None:
        """Merge override configuration into base configuration

        Args:
            base_config: Base configuration to merge into
            override_config: Override configuration to merge
        """
        self._merge_config(base_config, override_config)

    def validate_and_normalize(self, config: Dict[str, Any]) -> List[str]:
        """Validate and normalize configuration values

        Args:
            config: Configuration to validate

        Returns:
            List of validation warnings
        """
        warnings = []

        # Validate timeout values
        timeouts = config.get("timeouts", {})
        for timeout_key, timeout_value in timeouts.items():
            if not isinstance(timeout_value, (int, float)) or timeout_value <= 0:
                warning = f"Invalid timeout value for {timeout_key}: {timeout_value}, using default"
                warnings.append(warning)
                logger.warning(warning)
                if timeout_key in self.DEFAULT_CONFIG["timeouts"]:
                    timeouts[timeout_key] = self.DEFAULT_CONFIG["timeouts"][timeout_key]

        # Validate limits
        limits = config.get("limits", {})
        for limit_key, limit_value in limits.items():
            if not isinstance(limit_value, int) or limit_value <= 0:
                warning = f"Invalid limit value for {limit_key}: {limit_value}, using default"
                warnings.append(warning)
                logger.warning(warning)
                if limit_key in self.DEFAULT_CONFIG["limits"]:
                    limits[limit_key] = self.DEFAULT_CONFIG["limits"][limit_key]

        return warnings

    # Basic accessor methods
    def get_limit(self, config: Dict[str, Any], limit_name: str, explicit_limit: Optional[int] = None) -> int:
        """
        Get configuration limit with precedence

        Args:
            config: Configuration dictionary
            limit_name: Name of the limit
            explicit_limit: Explicit limit override (highest priority)

        Returns:
            Resolved limit value
        """
        # Priority 1: Explicit function argument
        if explicit_limit is not None:
            if isinstance(explicit_limit, int) and explicit_limit > 0:
                return explicit_limit
            else:
                logger.warning(f"Invalid explicit limit for {limit_name}: {explicit_limit}")

        # Priority 2-4: Configuration system
        limits = config.get("limits", {})
        limit_value = limits.get(limit_name)

        if isinstance(limit_value, int) and limit_value > 0:
            return limit_value

        # Fallback to default
        default_limits = self.DEFAULT_CONFIG.get("limits", {})
        default_value = default_limits.get(limit_name, 1000)

        logger.warning(f"Invalid or missing limit for {limit_name}, using default: {default_value}")
        return default_value

    def get_timeout(self, config: Dict[str, Any], timeout_name: str, explicit_timeout: Optional[int] = None) -> int:
        """
        Get timeout configuration with precedence

        Args:
            config: Configuration dictionary
            timeout_name: Name of the timeout
            explicit_timeout: Explicit timeout override (highest priority)

        Returns:
            Resolved timeout value in seconds
        """
        # Priority 1: Explicit function argument
        if explicit_timeout is not None:
            if isinstance(explicit_timeout, (int, float)) and explicit_timeout > 0:
                return int(explicit_timeout)
            else:
                logger.warning(f"Invalid explicit timeout for {timeout_name}: {explicit_timeout}")

        # Priority 2-4: Configuration system
        timeouts = config.get("timeouts", {})
        timeout_value = timeouts.get(timeout_name)

        if isinstance(timeout_value, (int, float)) and timeout_value > 0:
            return int(timeout_value)

        # Fallback to default
        default_timeouts = self.DEFAULT_CONFIG.get("timeouts", {})
        default_value = default_timeouts.get(timeout_name, 60)

        logger.warning(f"Invalid or missing timeout for {timeout_name}, using default: {default_value}")
        return default_value

    def get_security_setting(self, config: Dict[str, Any], setting_name: str, explicit_value: Optional[bool] = None) -> bool:
        """Get security setting with precedence

        Args:
            config: Configuration dictionary
            setting_name: Name of the security setting
            explicit_value: Explicit value override

        Returns:
            Security setting value
        """
        if explicit_value is not None:
            return bool(explicit_value)

        security = config.get("security", {})
        setting_value = security.get(setting_name)

        if isinstance(setting_value, bool):
            return setting_value

        # Fallback to default
        default_security = self.DEFAULT_CONFIG.get("security", {})
        default_value = default_security.get(setting_name, True)

        return bool(default_value)

    def get_execution_setting(self, config: Dict[str, Any], setting_name: str, explicit_value: Optional[bool] = None) -> bool:
        """Get execution setting with precedence

        Args:
            config: Configuration dictionary
            setting_name: Name of the execution setting
            explicit_value: Explicit value override

        Returns:
            Execution setting value
        """
        if explicit_value is not None:
            return bool(explicit_value)

        execution = config.get("execution", {})
        setting_value = execution.get(setting_name)

        if isinstance(setting_value, bool):
            return setting_value

        # Fallback to default
        default_execution = self.DEFAULT_CONFIG.get("execution", {})
        default_value = default_execution.get(setting_name, True)

        return bool(default_value)

    # Configuration file management
    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in standard locations"""
        possible_locations = [
            Path.cwd() / "config.json",
            Path.cwd() / "gemini_config.json",
            Path.home() / ".gemini" / "config.json",
            Path.cwd() / ".config" / "gemini.json",
        ]

        for location in possible_locations:
            try:
                if location.exists() and location.is_file():
                    return location
            except (OSError, PermissionError):
                continue

        return None

    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from JSON file

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config file {config_path}: {e}")
            return {}

    def save_config(self, config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
        """Save configuration to file

        Args:
            config: Configuration to save
            config_path: Path to save configuration (optional)
        """
        if config_path is None:
            config_path = Path.cwd() / "gemini_config.json"

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, sort_keys=True)
            logger.info(f"Configuration saved to: {config_path}")
        except IOError as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration to {config_path}: {e}")

    # Utility methods
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge configuration dictionaries

        Args:
            base: Base configuration to merge into
            override: Override configuration
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _deep_copy_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of a dictionary

        Args:
            d: Dictionary to copy

        Returns:
            Deep copy of dictionary
        """
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy_dict(value)
            elif isinstance(value, list):
                result[key] = value.copy()
            else:
                result[key] = value
        return result

    # Configuration debugging and summary
    def get_config_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of core configuration

        Args:
            config: Configuration to summarize

        Returns:
            Configuration summary
        """
        return {
            "config_file_path": str(self._config_file_path) if self._config_file_path else None,
            "load_timestamp": self._load_timestamp,
            "limits_count": len(config.get("limits", {})),
            "timeouts_count": len(config.get("timeouts", {})),
            "security_settings_count": len(config.get("security", {})),
            "execution_settings_count": len(config.get("execution", {})),
            "api_config_paths": config.get("api_config_paths", []),
            "allowed_extensions_count": len(config.get("security", {}).get("allowed_extensions", [])),
        }

    def validate_core_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate core configuration sections

        Args:
            config: Configuration to validate

        Returns:
            Dictionary mapping section names to validation issues
        """
        validation_results = {
            "limits": [],
            "timeouts": [],
            "security": [],
            "execution": [],
        }

        # Validate limits
        limits = config.get("limits", {})
        for limit_name, limit_value in limits.items():
            if not isinstance(limit_value, int) or limit_value <= 0:
                validation_results["limits"].append(f"Invalid {limit_name}: {limit_value}")

        # Validate timeouts
        timeouts = config.get("timeouts", {})
        for timeout_name, timeout_value in timeouts.items():
            if not isinstance(timeout_value, (int, float)) or timeout_value <= 0:
                validation_results["timeouts"].append(f"Invalid {timeout_name}: {timeout_value}")

        # Validate security settings
        security = config.get("security", {})
        for setting_name, setting_value in security.items():
            if setting_name == "allowed_extensions":
                if not isinstance(setting_value, list):
                    validation_results["security"].append(f"allowed_extensions should be a list")
            elif setting_name in ["enable_sanitization", "allow_path_traversal"]:
                if not isinstance(setting_value, bool):
                    validation_results["security"].append(f"{setting_name} should be boolean")

        # Validate execution settings
        execution = config.get("execution", {})
        for setting_name, setting_value in execution.items():
            if setting_name == "max_parallel_processes":
                if not isinstance(setting_value, int) or setting_value <= 0:
                    validation_results["execution"].append(f"Invalid max_parallel_processes: {setting_value}")
            elif isinstance(setting_value, str):
                # Should be boolean
                validation_results["execution"].append(f"{setting_name} should be boolean, got string")

        # Remove empty validation results
        return {k: v for k, v in validation_results.items() if v}


# Export main API
__all__ = [
    "CoreConfigManager",
    "ConfigurationError",
]
