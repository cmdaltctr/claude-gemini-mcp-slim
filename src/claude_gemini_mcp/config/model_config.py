#!/usr/bin/env python3
"""
Model Configuration Manager - Specialized component for model-related configuration.

This module provides model-specific configuration management following the
project's decoupled architecture pattern. It handles model resolution, nickname
management, tool assignments, and force-model logic.

Features:
- Model nickname resolution and management
- Tool-to-model assignment mapping
- Force-model override logic
- Model validation and verification
- Dynamic model registration for new tools

Date: 2025-08-04
Architecture: Configuration Specialist Pattern
"""

import logging
import os
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)


class ModelConfigManager:
    """
    Specialized configuration manager for model-related settings.

    This class manages model resolution, nicknames, assignments, and validation
    that were previously scattered in the monolithic config.py, following the
    single responsibility principle.
    """

    def __init__(self, models_config: Dict[str, Any]):
        """Initialize model configuration manager

        Args:
            models_config: Complete models configuration dictionary
        """
        self._models_config = models_config or {}
        self._nicknames = self._models_config.get("nicknames", {})
        self._assignments = self._models_config.get("assignments", {})
        logger.debug("Initialized model configuration manager")

    # Core model resolution
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
                # Check if it's a nickname first
                return self._nicknames.get(explicit_model, explicit_model)
            elif explicit_model is not None:  # Non-string or empty string
                logger.warning(
                    f"Invalid explicit model for {tool_name}: {explicit_model}, falling back to default"
                )

        # Priority 2-4: Configuration system (env vars, config file, defaults)
        # Get assigned nickname for the tool
        assigned_nickname = self._assignments.get(tool_name, "flash")

        # Resolve nickname to actual model name
        model_name = self._nicknames.get(assigned_nickname, assigned_nickname)

        # Validate model name format
        if not model_name or not isinstance(model_name, str):
            logger.warning(
                f"Invalid model name for {tool_name}, falling back to default"
            )
            return self._get_default_model()

        return model_name

    def _get_default_model(self) -> str:
        """Get default fallback model"""
        default_nickname = "flash"
        return self._nicknames.get(default_nickname, "gemini-2.5-flash")

    # Nickname management
    def get_nicknames(self) -> Dict[str, str]:
        """Get all model nicknames"""
        return self._nicknames.copy()

    def get_nickname_for_model(self, model_name: str) -> Optional[str]:
        """Get nickname for a specific model name

        Args:
            model_name: Full model name

        Returns:
            Nickname if found, None otherwise
        """
        for nickname, name in self._nicknames.items():
            if name == model_name:
                return nickname
        return None

    def resolve_nickname(self, nickname_or_model: str) -> str:
        """Resolve nickname to model name or return as-is

        Args:
            nickname_or_model: Either a nickname or full model name

        Returns:
            Resolved model name
        """
        return self._nicknames.get(nickname_or_model, nickname_or_model)

    def add_nickname(self, nickname: str, model_name: str) -> None:
        """Add or update a model nickname

        Args:
            nickname: Nickname to add
            model_name: Full model name
        """
        self._nicknames[nickname] = model_name
        self._models_config["nicknames"] = self._nicknames
        logger.info(f"Added/updated nickname '{nickname}' -> '{model_name}'")

    # Tool assignment management
    def get_assignments(self) -> Dict[str, str]:
        """Get all tool assignments"""
        return self._assignments.copy()

    def get_tool_assignment(self, tool_name: str) -> str:
        """Get assigned nickname for a tool

        Args:
            tool_name: Name of the tool

        Returns:
            Assigned nickname (defaults to 'flash')
        """
        return self._assignments.get(tool_name, "flash")

    def set_tool_assignment(self, tool_name: str, nickname: str) -> None:
        """Set tool assignment to a nickname

        Args:
            tool_name: Name of the tool
            nickname: Nickname to assign
        """
        if nickname not in self._nicknames:
            logger.warning(f"Nickname '{nickname}' not found, assignment may not work")

        self._assignments[tool_name] = nickname
        self._models_config["assignments"] = self._assignments
        logger.info(f"Assigned tool '{tool_name}' to nickname '{nickname}'")

    def register_tool_if_missing(self, tool_name: str, default_nickname: str) -> None:
        """
        Register a new tool with default model assignment if missing.

        Args:
            tool_name: Name of the tool to register
            default_nickname: Default model nickname to use
        """
        # Only add if not already present
        if tool_name not in self._assignments:
            # Validate the default nickname exists
            if default_nickname not in self._nicknames:
                logger.warning(
                    f"Unknown model nickname '{default_nickname}' for tool '{tool_name}', using 'flash'"
                )
                default_nickname = "flash"

            self._assignments[tool_name] = default_nickname
            self._models_config["assignments"] = self._assignments
            logger.info(
                f"Registered new tool '{tool_name}' with default model '{default_nickname}'"
            )
        else:
            logger.debug(
                f"Tool '{tool_name}' already registered with model '{self._assignments[tool_name]}'"
            )

    # Model validation
    def validate_model_name(self, model_name: str) -> bool:
        """Validate that a model name is acceptable

        Args:
            model_name: Model name to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(model_name, str) or not model_name.strip():
            return False

        # Allow direct gemini model names
        if model_name.startswith("gemini-"):
            return True

        # Allow configured nicknames
        if model_name in self._nicknames:
            return True

        return False

    def get_available_models(self) -> Set[str]:
        """Get all available model names (nicknames + direct names)

        Returns:
            Set of available model identifiers
        """
        available = set(self._nicknames.keys())  # All nicknames
        available.update(self._nicknames.values())  # All resolved model names
        return available

    def validate_assignments(self) -> Dict[str, str]:
        """Validate all tool assignments and return issues

        Returns:
            Dictionary mapping tool names to validation issues
        """
        issues = {}

        for tool_name, nickname in self._assignments.items():
            if nickname not in self._nicknames:
                issues[tool_name] = f"Invalid nickname '{nickname}', not found in nicknames"

        if issues:
            logger.warning(f"Found {len(issues)} assignment validation issues")

        return issues

    # Force model override logic
    def apply_force_model_override(self) -> None:
        """Apply FORCE_MODEL environment variable override"""
        force_model = os.getenv("FORCE_MODEL")
        if not force_model:
            return

        logger.info(f"Applying FORCE_MODEL override: {force_model}")

        if force_model in self._nicknames:
            # It's a nickname, override all assignments to use this nickname
            for tool_name in self._assignments.keys():
                self._assignments[tool_name] = force_model
            logger.info(f"Updated all tool assignments to use nickname '{force_model}'")

        elif force_model.startswith("gemini-"):
            # It's a direct model name, create a custom nickname for it
            self._nicknames["custom"] = force_model
            for tool_name in self._assignments.keys():
                self._assignments[tool_name] = "custom"
            logger.info(f"Created custom nickname for model '{force_model}'")

        else:
            logger.warning(f"Invalid FORCE_MODEL value: {force_model}, ignoring")
            return

        # Update the config dictionaries
        self._models_config["nicknames"] = self._nicknames
        self._models_config["assignments"] = self._assignments

    # Configuration summary and debugging
    def get_model_summary(self) -> Dict[str, Any]:
        """Get summary of model configuration

        Returns:
            Dictionary with model configuration summary
        """
        return {
            "nicknames_count": len(self._nicknames),
            "assignments_count": len(self._assignments),
            "available_nicknames": list(self._nicknames.keys()),
            "registered_tools": list(self._assignments.keys()),
            "default_model": self._get_default_model(),
            "force_model_active": bool(os.getenv("FORCE_MODEL")),
        }

    def get_tool_model_mapping(self) -> Dict[str, str]:
        """Get complete tool to resolved model mapping

        Returns:
            Dictionary mapping tool names to resolved model names
        """
        mapping = {}
        for tool_name, nickname in self._assignments.items():
            resolved_model = self._nicknames.get(nickname, nickname)
            mapping[tool_name] = resolved_model
        return mapping

    def debug_model_resolution(self, tool_name: str) -> Dict[str, Any]:
        """Debug model resolution for a specific tool

        Args:
            tool_name: Tool name to debug

        Returns:
            Dictionary with resolution details
        """
        nickname = self._assignments.get(tool_name, "flash")
        resolved_model = self._nicknames.get(nickname, nickname)

        return {
            "tool_name": tool_name,
            "assigned_nickname": nickname,
            "nickname_exists": nickname in self._nicknames,
            "resolved_model": resolved_model,
            "is_valid": self.validate_model_name(resolved_model),
            "force_model_env": os.getenv("FORCE_MODEL"),
        }


# Export main API
__all__ = [
    "ModelConfigManager",
]
