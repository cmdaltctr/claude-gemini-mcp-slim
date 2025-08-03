#!/usr/bin/env python3
"""
Gemini Helper Configuration System

This module provides a comprehensive configuration management system with:
- Load precedence: explicit args › env vars › config.json › hard-coded defaults
- Typed accessors: get_model(tool_name), get_limit(name), get_timeout(name)
- Nickname support with environment overrides (GEMINI_FLASH_MODEL, GEMINI_PRO_MODEL)
- Force-model logic: FORCE_MODEL environment variable override
- Validation with logging warnings and safe fallbacks
- Thread-safe configuration caching

Date: 2025-01-21
Architecture: Configuration Management Pattern
"""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Thread-safe singleton pattern for configuration
_config_lock = threading.Lock()
_config_instance: Optional["GeminiConfig"] = None


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails"""

    pass


class GeminiConfig:
    """
    Comprehensive configuration management for Gemini Helper

    Implements load precedence:
    1. Explicit function arguments (highest priority)
    2. Environment variables
    3. config.json file
    4. Hard-coded defaults (lowest priority)
    """

    # Hard-coded defaults (lowest priority)
    DEFAULT_CONFIG = {
        # Model configurations
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
                ".py",
                ".js",
                ".ts",
                ".java",
                ".cpp",
                ".c",
                ".rs",
                ".vue",
                ".html",
                ".css",
                ".scss",
                ".sass",
                ".jsx",
                ".tsx",
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".md",
                ".txt",
                ".go",
                ".php",
                ".rb",
                ".swift",
                ".kt",
                ".scala",
                ".sh",
                ".bat",
                ".ps1",
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
        # Routing and provider configurations
        "routing": {
            "enabled": False,  # Disabled by default for backward compatibility
            "providers": {
                "gemini": {
                    "name": "gemini",
                    "api_base_url": "https://generativelanguage.googleapis.com/v1beta/models/",
                    "api_key_env": "GEMINI_API_KEY",
                    "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-8b", "gemini-2.5-flash-exp-0827", "gemini-2.5-pro-exp-0827"],
                    "transformers": ["gemini"],
                    "enabled": True,
                },
                "openrouter": {
                    "name": "openrouter",
                    "api_base_url": "https://openrouter.ai/api/v1/chat/completions",
                    "api_key_env": "OPENROUTER_API_KEY",
                    "models": ["google/gemini-2.5-pro-preview", "anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku"],
                    "transformers": ["openrouter"],
                    "enabled": False,
                },
                "deepseek": {
                    "name": "deepseek",
                    "api_base_url": "https://api.deepseek.com/chat/completions",
                    "api_key_env": "DEEPSEEK_API_KEY",
                    "models": ["deepseek-chat", "deepseek-reasoner"],
                    "transformers": ["deepseek"],
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
                "long_context_tokens": 60000,  # Token count threshold for longContext scenario
                "background_task_size": 1000,   # Content size threshold for background scenario
            },
            "fallback_strategy": "provider_cascade",  # "provider_cascade", "cli_fallback", "fail_fast"
            "retry_attempts": 2,
            "timeout_ms": 30000,
        },
    }

    # Hard-coded defaults (lowest priority)
    def __init__(self):
        """Initialize configuration with load precedence"""
        self._config: Dict[str, Any] = {}
        self._config_file_path: Optional[Path] = None
        self._load_timestamp: float = 0
        self._reload()

    # Private method to reload configuration
    def _reload(self) -> None:
        """Reload configuration from all sources with proper precedence"""
        try:
            # Start with hard-coded defaults
            self._config = self._deep_copy_dict(self.DEFAULT_CONFIG)

            # Layer 3: config.json file (if exists)
            config_file = self._find_config_file()
            if config_file:
                self._config_file_path = config_file
                file_config = self._load_config_file(config_file)
                self._merge_config(self._config, file_config)
                logger.info(f"Loaded configuration from: {config_file}")

            # Layer 2: Environment variables
            env_config = self._load_env_config()
            self._merge_config(self._config, env_config)

            # Apply validation and normalization
            self._validate_and_normalize()

            # Apply force-model override if present
            self._apply_force_model_override()

            import time

            self._load_timestamp = time.time()

            logger.info("Configuration loaded successfully")

        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            # Fallback to defaults if loading fails
            self._config = self._deep_copy_dict(self.DEFAULT_CONFIG)
            raise ConfigurationError(f"Failed to load configuration: {e}")

    # Private method to find configuration file
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

    # Private method to load configuration file
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config file {config_path}: {e}")
            return {}

    # Private method to load environment variables
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config: Dict[str, Any] = {}

        # Model environment variables
        if os.getenv("GEMINI_FLASH_MODEL"):
            env_config.setdefault("models", {}).setdefault("nicknames", {})["flash"] = (
                os.getenv("GEMINI_FLASH_MODEL")
            )

        if os.getenv("GEMINI_PRO_MODEL"):
            env_config.setdefault("models", {}).setdefault("nicknames", {})["pro"] = (
                os.getenv("GEMINI_PRO_MODEL")
            )

        # Timeout overrides
        if os.getenv("CLI_TIMEOUT"):
            try:
                env_config.setdefault("timeouts", {})["cli_timeout"] = int(
                    os.getenv("CLI_TIMEOUT")
                )
            except ValueError:
                logger.warning(f"Invalid CLI_TIMEOUT value: {os.getenv('CLI_TIMEOUT')}")

        if os.getenv("API_TIMEOUT"):
            try:
                env_config.setdefault("timeouts", {})["api_timeout"] = int(
                    os.getenv("API_TIMEOUT")
                )
            except ValueError:
                logger.warning(f"Invalid API_TIMEOUT value: {os.getenv('API_TIMEOUT')}")

        # Size limit overrides
        if os.getenv("MAX_FILE_SIZE"):
            try:
                env_config.setdefault("limits", {})["max_file_size"] = int(
                    os.getenv("MAX_FILE_SIZE")
                )
            except ValueError:
                logger.warning(
                    f"Invalid MAX_FILE_SIZE value: {os.getenv('MAX_FILE_SIZE')}"
                )

        if os.getenv("MAX_LINES"):
            try:
                env_config.setdefault("limits", {})["max_lines"] = int(
                    os.getenv("MAX_LINES")
                )
            except ValueError:
                logger.warning(f"Invalid MAX_LINES value: {os.getenv('MAX_LINES')}")

        if os.getenv("MAX_PROMPT_SIZE"):
            try:
                env_config.setdefault("limits", {})["max_prompt_size"] = int(
                    os.getenv("MAX_PROMPT_SIZE")
                )
            except ValueError:
                logger.warning(
                    f"Invalid MAX_PROMPT_SIZE value: {os.getenv('MAX_PROMPT_SIZE')}"
                )

        if os.getenv("MAX_CODEBASE_SIZE"):
            try:
                env_config.setdefault("limits", {})["max_codebase_size"] = int(
                    os.getenv("MAX_CODEBASE_SIZE")
                )
            except ValueError:
                logger.warning(
                    f"Invalid MAX_CODEBASE_SIZE value: {os.getenv('MAX_CODEBASE_SIZE')}"
                )

        if os.getenv("MAX_CONTEXT_WINDOW"):
            try:
                env_config.setdefault("limits", {})["max_context_window"] = int(
                    os.getenv("MAX_CONTEXT_WINDOW")
                )
            except ValueError:
                logger.warning(
                    f"Invalid MAX_CONTEXT_WINDOW value: {os.getenv('MAX_CONTEXT_WINDOW')}"
                )

        if os.getenv("SANITIZATION_MAX_LENGTH"):
            try:
                env_config.setdefault("limits", {})["sanitization_max_length"] = int(
                    os.getenv("SANITIZATION_MAX_LENGTH")
                )
            except ValueError:
                logger.warning(
                    f"Invalid SANITIZATION_MAX_LENGTH value: {os.getenv('SANITIZATION_MAX_LENGTH')}"
                )

        if os.getenv("MAX_CODEBASE_ANALYSIS_SIZE"):
            try:
                env_config.setdefault("limits", {})["max_codebase_analysis_size"] = int(
                    os.getenv("MAX_CODEBASE_ANALYSIS_SIZE")
                )
            except ValueError:
                logger.warning(
                    f"Invalid MAX_CODEBASE_ANALYSIS_SIZE value: {os.getenv('MAX_CODEBASE_ANALYSIS_SIZE')}"
                )

        if os.getenv("SANITIZATION_QUERY_DIVISOR"):
            try:
                env_config.setdefault("limits", {})["sanitization_query_divisor"] = int(
                    os.getenv("SANITIZATION_QUERY_DIVISOR")
                )
            except ValueError:
                logger.warning(
                    f"Invalid SANITIZATION_QUERY_DIVISOR value: {os.getenv('SANITIZATION_QUERY_DIVISOR')}"
                )

        if os.getenv("SANITIZATION_CONTEXT_DIVISOR"):
            try:
                env_config.setdefault("limits", {})["sanitization_context_divisor"] = int(
                    os.getenv("SANITIZATION_CONTEXT_DIVISOR")
                )
            except ValueError:
                logger.warning(
                    f"Invalid SANITIZATION_CONTEXT_DIVISOR value: {os.getenv('SANITIZATION_CONTEXT_DIVISOR')}"
                )

        # Boolean feature flags
        if os.getenv("ENABLE_MARKDOWN_CONVERSION"):
            value = os.getenv("ENABLE_MARKDOWN_CONVERSION", "").lower()
            parsed_value = value in ("true", "1", "yes", "on")
            # Only set if it's a recognized boolean value
            if value in ("true", "1", "yes", "on", "false", "0", "no", "off"):
                env_config.setdefault("execution", {})[
                    "enable_markdown_conversion"
                ] = parsed_value

        if os.getenv("ENABLE_SANITIZATION"):
            value = os.getenv("ENABLE_SANITIZATION", "").lower()
            parsed_value = value in ("true", "1", "yes", "on")
            # Only set if it's a recognized boolean value
            if value in ("true", "1", "yes", "on", "false", "0", "no", "off"):
                env_config.setdefault("security", {})[
                    "enable_sanitization"
                ] = parsed_value

        return env_config

    # Private method to merge configuration dictionaries
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    # Private method to create a deep copy of a dictionary
    def _deep_copy_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of a dictionary"""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy_dict(value)
            elif isinstance(value, list):
                result[key] = value.copy()
            else:
                result[key] = value
        return result

    # Private method to validate and normalize configuration values
    def _validate_and_normalize(self) -> None:
        """Validate configuration values and apply normalization"""
        # Validate timeout values
        timeouts = self._config.get("timeouts", {})
        for timeout_key, timeout_value in timeouts.items():
            if not isinstance(timeout_value, (int, float)) or timeout_value <= 0:
                logger.warning(
                    f"Invalid timeout value for {timeout_key}: {timeout_value}, using default"
                )
                timeouts[timeout_key] = self.DEFAULT_CONFIG["timeouts"][timeout_key]

        # Validate limits
        limits = self._config.get("limits", {})
        for limit_key, limit_value in limits.items():
            if not isinstance(limit_value, int) or limit_value <= 0:
                logger.warning(
                    f"Invalid limit value for {limit_key}: {limit_value}, using default"
                )
                limits[limit_key] = self.DEFAULT_CONFIG["limits"][limit_key]

        # Validate model nicknames
        models = self._config.get("models", {})
        nicknames = models.get("nicknames", {})
        for nickname, model_name in nicknames.items():
            if not isinstance(model_name, str) or not model_name.strip():
                logger.warning(
                    f"Invalid model name for nickname {nickname}: {model_name}"
                )
                nicknames[nickname] = self.DEFAULT_CONFIG["models"]["nicknames"].get(
                    nickname, "gemini-2.5-flash"
                )

        # Validate model assignments
        assignments = models.get("assignments", {})
        valid_nicknames = set(nicknames.keys())
        for tool_name, assigned_nickname in assignments.items():
            if assigned_nickname not in valid_nicknames:
                logger.warning(
                    f"Invalid model assignment for {tool_name}: {assigned_nickname}, using 'flash'"
                )
                assignments[tool_name] = "flash"

    # Private method to apply FORCE_MODEL environment variable override
    def _apply_force_model_override(self) -> None:
        """Apply FORCE_MODEL environment variable override"""
        force_model = os.getenv("FORCE_MODEL")
        if force_model:
            logger.info(f"Applying FORCE_MODEL override: {force_model}")

            # Validate that the forced model exists in nicknames or is a valid model name
            nicknames = self._config.get("models", {}).get("nicknames", {})

            if force_model in nicknames:
                # It's a nickname, override all assignments to use this nickname
                assignments = self._config.setdefault("models", {}).setdefault(
                    "assignments", {}
                )
                for tool_name in assignments.keys():
                    assignments[tool_name] = force_model
            elif force_model.startswith("gemini-"):
                # It's a direct model name, create a custom nickname for it
                nicknames = self._config.setdefault("models", {}).setdefault(
                    "nicknames", {}
                )
                nicknames["custom"] = force_model
                assignments = self._config.setdefault("models", {}).setdefault(
                    "assignments", {}
                )
                for tool_name in assignments.keys():
                    assignments[tool_name] = "custom"
            else:
                logger.warning(f"Invalid FORCE_MODEL value: {force_model}, ignoring")
                return

    # Typed accessor methods (main public API)
    def get_model(self, tool_name: str, explicit_model: Optional[str] = None) -> str:
        """
        Get model name for a specific tool with load precedence

        Args:
            tool_name: Name of the tool (e.g., 'quick_query', 'analyze_code')
            explicit_model: Explicit model override (highest priority)

        Returns:
            str: Resolved model name (e.g., 'gemini-2.5-flash')
        """
        # Priority 1: Explicit function argument
        if explicit_model is not None:
            if isinstance(explicit_model, str) and explicit_model.strip():
                # Check if it's a nickname
                nicknames = self._config.get("models", {}).get("nicknames", {})
                return nicknames.get(explicit_model, explicit_model)
            elif explicit_model is not None:  # Non-string or empty string
                logger.warning(
                    f"Invalid explicit model for {tool_name}: {explicit_model}, falling back to default"
                )

        # Priority 2-4: Configuration system (env vars, config file, defaults)
        assignments = self._config.get("models", {}).get("assignments", {})
        nicknames = self._config.get("models", {}).get("nicknames", {})

        # Get assigned nickname for the tool
        assigned_nickname = assignments.get(tool_name, "flash")

        # Resolve nickname to actual model name
        model_name = nicknames.get(assigned_nickname, assigned_nickname)

        # Validate model name format
        if not model_name or not isinstance(model_name, str):
            logger.warning(
                f"Invalid model name for {tool_name}, falling back to default"
            )
            return self.DEFAULT_CONFIG["models"]["nicknames"]["flash"]

        return model_name

    # Typed accessor methods for limits
    def get_limit(self, limit_name: str, explicit_limit: Optional[int] = None) -> int:
        """
        Get configuration limit with load precedence

        Args:
            limit_name: Name of the limit (e.g., 'max_file_size', 'max_lines')
            explicit_limit: Explicit limit override (highest priority)

        Returns:
            int: Resolved limit value
        """
        # Priority 1: Explicit function argument
        if explicit_limit is not None:
            if isinstance(explicit_limit, int) and explicit_limit > 0:
                return explicit_limit
            else:
                logger.warning(
                    f"Invalid explicit limit for {limit_name}: {explicit_limit}"
                )

        # Priority 2-4: Configuration system
        limits = self._config.get("limits", {})
        limit_value = limits.get(limit_name)

        if isinstance(limit_value, int) and limit_value > 0:
            return limit_value

        # Fallback to default
        default_limits = self.DEFAULT_CONFIG.get("limits", {})
        default_value = default_limits.get(limit_name, 1000)

        logger.warning(
            f"Invalid or missing limit for {limit_name}, using default: {default_value}"
        )
        return default_value

    # Typed accessor methods for timeouts
    def get_timeout(
        self, timeout_name: str, explicit_timeout: Optional[int] = None
    ) -> int:
        """
        Get timeout configuration with load precedence

        Args:
            timeout_name: Name of the timeout (e.g., 'cli_timeout', 'api_timeout')
            explicit_timeout: Explicit timeout override (highest priority)

        Returns:
            int: Resolved timeout value in seconds
        """
        # Priority 1: Explicit function argument
        if explicit_timeout is not None:
            if isinstance(explicit_timeout, (int, float)) and explicit_timeout > 0:
                return int(explicit_timeout)
            else:
                logger.warning(
                    f"Invalid explicit timeout for {timeout_name}: {explicit_timeout}"
                )

        # Priority 2-4: Configuration system
        timeouts = self._config.get("timeouts", {})
        timeout_value = timeouts.get(timeout_name)

        if isinstance(timeout_value, (int, float)) and timeout_value > 0:
            return int(timeout_value)

        # Fallback to default
        default_timeouts = self.DEFAULT_CONFIG.get("timeouts", {})
        default_value = default_timeouts.get(timeout_name, 60)

        logger.warning(
            f"Invalid or missing timeout for {timeout_name}, using default: {default_value}"
        )
        return default_value

    # Typed accessor methods for security settings
    def get_security_setting(
        self, setting_name: str, explicit_value: Optional[bool] = None
    ) -> bool:
        """Get security setting with load precedence"""
        if explicit_value is not None:
            return bool(explicit_value)

        security = self._config.get("security", {})
        setting_value = security.get(setting_name)

        if isinstance(setting_value, bool):
            return setting_value

        # Fallback to default
        default_security = self.DEFAULT_CONFIG.get("security", {})
        default_value = default_security.get(setting_name, True)

        return bool(default_value)

    # Typed accessor methods for execution settings
    def get_execution_setting(
        self, setting_name: str, explicit_value: Optional[bool] = None
    ) -> bool:
        """Get execution setting with load precedence"""
        if explicit_value is not None:
            return bool(explicit_value)

        execution = self._config.get("execution", {})
        setting_value = execution.get(setting_name)

        if isinstance(setting_value, bool):
            return setting_value

        # Fallback to default
        default_execution = self.DEFAULT_CONFIG.get("execution", {})
        default_value = default_execution.get(setting_name, True)

        return bool(default_value)

    # Utility methods
    def reload_config(self) -> None:
        """Force reload configuration from all sources"""
        logger.info("Reloading configuration...")
        self._reload()

    def get_raw_config(self) -> Dict[str, Any]:
        """Get the raw configuration dictionary (for debugging)"""
        return self._deep_copy_dict(self._config)

    def save_config(self, config_path: Optional[Path] = None) -> None:
        """Save current configuration to file"""
        if config_path is None:
            config_path = Path.cwd() / "gemini_config.json"

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, sort_keys=True)
            logger.info(f"Configuration saved to: {config_path}")
        except IOError as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(
                f"Failed to save configuration to {config_path}: {e}"
            )

    # Utility methods
    def validate_model_name(self, model_name: str) -> bool:
        """Validate that a model name is acceptable"""
        if not isinstance(model_name, str) or not model_name.strip():
            return False

        # Allow direct gemini model names
        if model_name.startswith("gemini-"):
            return True

        # Allow configured nicknames
        nicknames = self._config.get("models", {}).get("nicknames", {})
        if model_name in nicknames:
            return True

        return False

    # Routing configuration accessors
    def is_routing_enabled(self) -> bool:
        """Check if routing is enabled"""
        return self._config.get("routing", {}).get("enabled", False)

    def get_routing_config(self) -> Dict[str, Any]:
        """Get the complete routing configuration"""
        return self._config.get("routing", {})

    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific provider"""
        providers = self._config.get("routing", {}).get("providers", {})
        return providers.get(provider_name)

    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names"""
        providers = self._config.get("routing", {}).get("providers", {})
        return [name for name, config in providers.items() if config.get("enabled", False)]

    def get_scenario_config(self, scenario: str) -> Optional[str]:
        """Get model configuration for a specific scenario"""
        scenarios = self._config.get("routing", {}).get("scenarios", {})
        return scenarios.get(scenario)

    def get_routing_threshold(self, threshold_name: str) -> int:
        """Get routing threshold value"""
        thresholds = self._config.get("routing", {}).get("thresholds", {})
        defaults = {
            "long_context_tokens": 60000,
            "background_task_size": 1000,
        }
        return thresholds.get(threshold_name, defaults.get(threshold_name, 0))

    def get_fallback_strategy(self) -> str:
        """Get the configured fallback strategy"""
        return self._config.get("routing", {}).get("fallback_strategy", "provider_cascade")


# Module-level singleton access functions
def get_config() -> GeminiConfig:
    """Get the global configuration instance (thread-safe singleton)"""
    global _config_instance

    if _config_instance is None:
        with _config_lock:
            # Double-check locking pattern
            if _config_instance is None:
                _config_instance = GeminiConfig()

    return _config_instance


# Utility functions
def register_tool_if_missing(tool_name: str, default_model_nickname: str) -> None:
    """
    Register a new tool with default model assignment if it's missing from config.

    This is the recommended pattern for new tools:
    1. Call register_tool_if_missing("my_new_tool", "flash") during initialization
    2. Use cfg.get_model("my_new_tool") to get the model for your tool

    Args:
        tool_name: Name of the tool to register (e.g., 'pre_edit', 'analyze_code')
        default_model_nickname: Default model nickname to use ('flash', 'pro', etc.)
    """
    config = get_config()

    # Get current assignments
    assignments = config._config.setdefault("models", {}).setdefault("assignments", {})

    # Only add if not already present
    if tool_name not in assignments:
        # Validate the default nickname exists
        nicknames = config._config.get("models", {}).get("nicknames", {})
        if default_model_nickname not in nicknames:
            logger.warning(
                f"Unknown model nickname '{default_model_nickname}' for tool '{tool_name}', using 'flash'"
            )
            default_model_nickname = "flash"

        assignments[tool_name] = default_model_nickname
        logger.info(
            f"Registered new tool '{tool_name}' with default model '{default_model_nickname}'"
        )
    else:
        logger.debug(
            f"Tool '{tool_name}' already registered with model '{assignments[tool_name]}'"
        )


# Utility functions
def reload_config() -> None:
    """Force reload the global configuration"""
    global _config_instance

    with _config_lock:
        if _config_instance is not None:
            _config_instance.reload_config()
        else:
            _config_instance = GeminiConfig()


# Convenience functions for common operations
def get_model(tool_name: str, explicit_model: Optional[str] = None) -> str:
    """Get model name for a tool (convenience function)"""
    return get_config().get_model(tool_name, explicit_model)


# Typed accessor methods for limits
def get_limit(limit_name: str, explicit_limit: Optional[int] = None) -> int:
    """Get configuration limit (convenience function)"""
    return get_config().get_limit(limit_name, explicit_limit)


# Typed accessor methods for timeouts
def get_timeout(timeout_name: str, explicit_timeout: Optional[int] = None) -> int:
    """Get timeout configuration (convenience function)"""
    return get_config().get_timeout(timeout_name, explicit_timeout)


# Typed accessor methods for security settings
def is_security_enabled(
    setting_name: str, explicit_value: Optional[bool] = None
) -> bool:
    """Check if security setting is enabled (convenience function)"""
    return get_config().get_security_setting(setting_name, explicit_value)


def is_execution_enabled(
    setting_name: str, explicit_value: Optional[bool] = None
) -> bool:
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


# Context manager for temporary configuration override
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


# Export main public API
__all__ = [
    "GeminiConfig",
    "ConfigurationError",
    "get_config",
    "reload_config",
    "register_tool_if_missing",
    "get_model",
    "get_limit",
    "get_timeout",
    "is_security_enabled",
    "is_execution_enabled",
    "ConfigOverride",
]
