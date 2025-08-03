#!/usr/bin/env python3
"""
Routing Strategies Module - Intelligent routing logic implementations.

This module implements various routing strategies for intelligent model
and provider selection, following claude-code-router patterns for
scenario-based routing, token-aware selection, and cost optimization.

Key Components:
- ScenarioRouter: Route based on predefined scenarios (background, think, etc.)
- TokenAwareRouter: Select models based on context window requirements
- CostOptimizer: Choose cost-optimal models for different task types
- PerformanceRouter: Select fastest available options

Architecture:
- Strategy pattern for pluggable routing logic
- Configuration-driven routing rules
- Context-aware decision making
- Performance and cost optimization
"""

from .scenario_router import ScenarioRouter
from .token_aware_router import TokenAwareRouter
from .cost_optimizer import CostOptimizer

__all__ = [
    "ScenarioRouter",
    "TokenAwareRouter",
    "CostOptimizer",
]
