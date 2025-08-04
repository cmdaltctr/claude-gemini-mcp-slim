#!/usr/bin/env python3
"""
TypeScript Code Analysis Module

This module provides TypeScript-specific code analysis capabilities using
TypeScript compiler API or compatible parsers.

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-04
"""

# Import the main analyzer when dependencies are available
try:
    from .analyze_code_ts import TypeScriptAnalyzer
    __all__ = ['TypeScriptAnalyzer']
except ImportError:
    # Handle missing TypeScript dependencies gracefully
    __all__ = []
