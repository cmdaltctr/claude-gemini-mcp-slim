#!/usr/bin/env python3
"""
JavaScript Code Analysis Module

This module provides JavaScript-specific code analysis capabilities using
Babel parser and JavaScript-specific analysis strategies.

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-04
"""

# Import the main analyzer when dependencies are available
try:
    from .analyze_code_js import JavaScriptAnalyzer
    __all__ = ['JavaScriptAnalyzer']
except ImportError:
    # Handle missing JavaScript dependencies gracefully
    __all__ = []
