#!/usr/bin/env python3
"""
Python Code Analysis Module

This module provides Python-specific code analysis capabilities using AST parsing
and language-specific analysis strategies.

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-04
"""

# Import the main analyzer when needed
try:
    from .analyze_code_py import PythonAnalyzer
    __all__ = ['PythonAnalyzer']
except ImportError:
    # Handle missing dependencies gracefully
    __all__ = []
