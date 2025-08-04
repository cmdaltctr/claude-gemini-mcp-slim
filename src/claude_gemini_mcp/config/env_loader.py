#!/usr/bin/env python3
"""
Environment Configuration Loader - Specialized component for environment variable processing.

This module provides environment variable processing following the project's
decoupled architecture pattern. It handles loading, validation, and type conversion
of environment variables into configuration dictionaries.

Features:
- Efficient environment variable mapping and processing
- Type-aware conversion (strings, integers, booleans)
- Nested configuration structure handling
- Validation and error handling for invalid values
- Extensible mapping system for new environment variables

Date: 2025-08-04
Architecture: Configuration Specialist Pattern
"""

import logging
import os
from typing import Any, Dict, Tuple, Union

logger = logging.getLogger(__name__)


class EnvironmentConfigLoader:
    """
    Specialized loader for environment variable configuration.

    This class processes environment variables into structured configuration
    dictionaries, handling type conversion and validation. It replaces the
    complex nested environment loading logic from the monolithic config.py.
    """

    def __init__(self):
        """Initialize environment configuration loader"""
        # Define environment variable mappings
        self._env_mappings = {
            # Model variables (string values)
            "GEMINI_FLASH_MODEL": ("models", "nicknames", "flash"),
            "GEMINI_PRO_MODEL": ("models", "nicknames", "pro"),

            # OpenRouter routing scenario models - you can choose any OpenRouter model
            "OPENROUTER_DEFAULT_MODEL": ("routing", "scenarios", "default"),
            "OPENROUTER_BACKGROUND_MODEL": ("routing", "scenarios", "background"),
            "OPENROUTER_THINK_MODEL": ("routing", "scenarios", "think"),
            "OPENROUTER_LONGCONTEXT_MODEL": ("routing", "scenarios", "longContext"),
            "OPENROUTER_WEBSEARCH_MODEL": ("routing", "scenarios", "webSearch"),
            "OPENROUTER_CODING_MODEL": ("routing", "scenarios", "coding"),
            "OPENROUTER_ANALYSIS_MODEL": ("routing", "scenarios", "analysis"),
            "OPENROUTER_MULTIMODAL_MODEL": ("routing", "scenarios", "multimodal"),
            "OPENROUTER_REASONING_MODEL": ("routing", "scenarios", "reasoning"),

            # OpenRouter provider configuration
            "OPENROUTER_API_BASE_URL": ("routing", "providers", "openrouter", "api_base_url"),

            # Timeout variables (integer values)
            "CLI_TIMEOUT": ("timeouts", "cli_timeout"),
            "API_TIMEOUT": ("timeouts", "api_timeout"),

            # Limit variables (integer values)
            "MAX_FILE_SIZE": ("limits", "max_file_size"),
            "MAX_LINES": ("limits", "max_lines"),
            "MAX_PROMPT_SIZE": ("limits", "max_prompt_size"),
            "MAX_CODEBASE_SIZE": ("limits", "max_codebase_size"),
            "MAX_CONTEXT_WINDOW": ("limits", "max_context_window"),
            "SANITIZATION_MAX_LENGTH": ("limits", "sanitization_max_length"),
            "MAX_CODEBASE_ANALYSIS_SIZE": ("limits", "max_codebase_analysis_size"),
            "SANITIZATION_QUERY_DIVISOR": ("limits", "sanitization_query_divisor"),
            "SANITIZATION_CONTEXT_DIVISOR": ("limits", "sanitization_context_divisor"),
        }

        # Boolean environment variable mappings
        self._boolean_mappings = {
            "ENABLE_MARKDOWN_CONVERSION": ("execution", "enable_markdown_conversion"),
            "ENABLE_SANITIZATION": ("security", "enable_sanitization"),

            # Routing feature toggles
            "ENABLE_ROUTING": ("routing", "enabled"),
            "ENABLE_OPENROUTER": ("routing", "providers", "openrouter", "enabled"),
            "ENABLE_PERFORMANCE_MONITORING": ("routing", "performance", "enable_performance_monitoring"),
            "ENABLE_COST_TRACKING": ("routing", "cost_optimization", "enable_cost_tracking"),
            "ENABLE_TELEMETRY": ("routing", "telemetry", "enabled"),
        }

        # Define sections that should have integer values
        self._integer_sections = {"timeouts", "limits"}

        logger.debug("Initialized environment configuration loader")

    def load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables

        Returns:
            Dictionary containing environment-based configuration
        """
        env_config: Dict[str, Any] = {}

        # Process string and integer environment variables
        for env_var, config_path in self._env_mappings.items():
            value = os.getenv(env_var)
            if not value:
                continue

            try:
                self._set_nested_config(env_config, config_path, value)
            except Exception as e:
                logger.warning(f"Failed to process {env_var}: {e}")

        # Process boolean environment variables
        for env_var, config_path in self._boolean_mappings.items():
            value = os.getenv(env_var)
            if not value:
                continue

            parsed_value = self._parse_boolean_value(env_var, value)
            if parsed_value is not None:
                self._set_nested_config_boolean(env_config, config_path, parsed_value)

        return env_config

    def _set_nested_config(self, config: Dict[str, Any], path: Tuple[str, ...], value: Any) -> None:
        """Set nested configuration value using path tuple

        Args:
            config: Configuration dictionary to update
            path: Tuple representing nested path (e.g., ("models", "nicknames", "flash"))
            value: Value to set
        """
        if len(path) == 2:  # section.key
            section, key = path
            processed_value = self._process_value_by_section(section, key, value)
            config.setdefault(section, {})[key] = processed_value

        elif len(path) == 3:  # models.nicknames.key OR routing.scenarios.key
            section, subsection, key = path
            config.setdefault(section, {}).setdefault(subsection, {})[key] = value

        elif len(path) == 4:  # routing.providers.openrouter.key
            section, subsection, subsubsection, key = path
            config.setdefault(section, {}).setdefault(subsection, {}).setdefault(subsubsection, {})[key] = value

        elif len(path) == 5:  # routing.providers.openrouter.section.key
            section, subsection, subsubsection, subsubsubsection, key = path
            config.setdefault(section, {}).setdefault(subsection, {}).setdefault(subsubsection, {}).setdefault(subsubsubsection, {})[key] = value

        else:
            raise ValueError(f"Invalid config path length: {path} (supported: 2-5 levels)")

    def _set_nested_config_boolean(self, config: Dict[str, Any], path: Tuple[str, ...], value: bool) -> None:
        """Set nested boolean configuration value using path tuple

        Args:
            config: Configuration dictionary to update
            path: Tuple representing nested path
            value: Boolean value to set
        """
        if len(path) == 2:  # section.key
            section, key = path
            config.setdefault(section, {})[key] = value

        elif len(path) == 3:  # routing.section.key
            section, subsection, key = path
            config.setdefault(section, {}).setdefault(subsection, {})[key] = value

        elif len(path) == 4:  # routing.providers.openrouter.enabled
            section, subsection, subsubsection, key = path
            config.setdefault(section, {}).setdefault(subsection, {}).setdefault(subsubsection, {})[key] = value

        elif len(path) == 5:  # routing.providers.openrouter.section.key
            section, subsection, subsubsection, subsubsubsection, key = path
            config.setdefault(section, {}).setdefault(subsection, {}).setdefault(subsubsection, {}).setdefault(subsubsubsection, {})[key] = value

        else:
            raise ValueError(f"Invalid boolean config path length: {path} (supported: 2-5 levels)")

    def _process_value_by_section(self, section: str, key: str, value: str) -> Union[str, int]:
        """Process value based on section type

        Args:
            section: Configuration section name
            key: Configuration key name
            value: String value from environment

        Returns:
            Processed value (string or integer)
        """
        if section in self._integer_sections:
            return self._convert_to_integer(f"{section}.{key}", value)
        return value

    def _convert_to_integer(self, config_name: str, value: str) -> int:
        """Convert string value to integer with error handling

        Args:
            config_name: Configuration name for error reporting
            value: String value to convert

        Returns:
            Integer value

        Raises:
            ValueError: If conversion fails
        """
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid {config_name} value: {value}")
            raise ValueError(f"Cannot convert {config_name} value '{value}' to integer")

    def _parse_boolean_value(self, env_var: str, value: str) -> Union[bool, None]:
        """Parse boolean value from environment variable

        Args:
            env_var: Environment variable name
            value: String value to parse

        Returns:
            Boolean value if valid, None if invalid
        """
        value_lower = value.lower()

        # Valid boolean values
        true_values = {"true", "1", "yes", "on"}
        false_values = {"false", "0", "no", "off"}
        valid_values = true_values | false_values

        if value_lower not in valid_values:
            logger.warning(f"Invalid boolean value for {env_var}: {value}")
            return None

        return value_lower in true_values

    def add_env_mapping(self, env_var: str, config_path: Tuple[str, ...]) -> None:
        """Add new environment variable mapping

        Args:
            env_var: Environment variable name
            config_path: Configuration path tuple
        """
        self._env_mappings[env_var] = config_path
        logger.debug(f"Added environment mapping: {env_var} -> {config_path}")

    def add_boolean_mapping(self, env_var: str, config_path: Tuple[str, str]) -> None:
        """Add new boolean environment variable mapping

        Args:
            env_var: Environment variable name
            config_path: Configuration path tuple (section, key)
        """
        self._boolean_mappings[env_var] = config_path
        logger.debug(f"Added boolean mapping: {env_var} -> {config_path}")

    def get_env_mappings(self) -> Dict[str, Tuple[str, ...]]:
        """Get all environment variable mappings

        Returns:
            Dictionary of environment variable mappings
        """
        return self._env_mappings.copy()

    def get_boolean_mappings(self) -> Dict[str, Tuple[str, str]]:
        """Get all boolean environment variable mappings

        Returns:
            Dictionary of boolean environment variable mappings
        """
        return self._boolean_mappings.copy()

    def validate_environment_config(self, env_config: Dict[str, Any]) -> Dict[str, str]:
        """Validate loaded environment configuration

        Args:
            env_config: Environment configuration to validate

        Returns:
            Dictionary mapping config keys to validation issues
        """
        issues = {}

        # Validate timeout values
        timeouts = env_config.get("timeouts", {})
        for timeout_key, timeout_value in timeouts.items():
            if not isinstance(timeout_value, int) or timeout_value <= 0:
                issues[f"timeouts.{timeout_key}"] = f"Invalid timeout value: {timeout_value}"

        # Validate limit values
        limits = env_config.get("limits", {})
        for limit_key, limit_value in limits.items():
            if not isinstance(limit_value, int) or limit_value <= 0:
                issues[f"limits.{limit_key}"] = f"Invalid limit value: {limit_value}"

        # Validate model names
        models = env_config.get("models", {})
        nicknames = models.get("nicknames", {})
        for nickname, model_name in nicknames.items():
            if not isinstance(model_name, str) or not model_name.strip():
                issues[f"models.nicknames.{nickname}"] = f"Invalid model name: {model_name}"

        if issues:
            for key, issue in issues.items():
                logger.warning(f"Environment config validation: {key} - {issue}")

        return issues

    def get_env_summary(self) -> Dict[str, Any]:
        """Get summary of environment variable processing

        Returns:
            Dictionary with environment processing summary
        """
        env_vars_set = []
        env_vars_available = []

        # Check which environment variables are set
        all_env_vars = set(self._env_mappings.keys()) | set(self._boolean_mappings.keys())

        for env_var in all_env_vars:
            if os.getenv(env_var):
                env_vars_set.append(env_var)
            env_vars_available.append(env_var)

        return {
            "total_mappings": len(self._env_mappings),
            "boolean_mappings": len(self._boolean_mappings),
            "env_vars_available": env_vars_available,
            "env_vars_set": env_vars_set,
            "env_vars_set_count": len(env_vars_set),
            "coverage": len(env_vars_set) / len(env_vars_available) if env_vars_available else 0,
        }

    def debug_env_var(self, env_var: str) -> Dict[str, Any]:
        """Debug specific environment variable processing

        Args:
            env_var: Environment variable name to debug

        Returns:
            Dictionary with debug information
        """
        value = os.getenv(env_var)

        debug_info = {
            "env_var": env_var,
            "value": value,
            "is_set": value is not None,
            "mapping_exists": False,
            "mapping_type": None,
            "config_path": None,
            "processed_value": None,
        }

        # Check regular mappings
        if env_var in self._env_mappings:
            debug_info["mapping_exists"] = True
            debug_info["mapping_type"] = "regular"
            debug_info["config_path"] = self._env_mappings[env_var]

            if value:
                path = self._env_mappings[env_var]
                if len(path) == 2:
                    section, key = path
                    try:
                        debug_info["processed_value"] = self._process_value_by_section(section, key, value)
                    except Exception as e:
                        debug_info["processing_error"] = str(e)
                else:
                    debug_info["processed_value"] = value

        # Check boolean mappings
        elif env_var in self._boolean_mappings:
            debug_info["mapping_exists"] = True
            debug_info["mapping_type"] = "boolean"
            debug_info["config_path"] = self._boolean_mappings[env_var]

            if value:
                debug_info["processed_value"] = self._parse_boolean_value(env_var, value)

        return debug_info


# Export main API
__all__ = [
    "EnvironmentConfigLoader",
]
