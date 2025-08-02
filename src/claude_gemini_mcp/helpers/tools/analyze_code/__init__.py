#!/usr/bin/env python3
"""
Single Code Analysis Tool Module

This module provides deep, focused analysis of individual code files or snippets including:
- AST-based Python code analysis
- Security vulnerability detection
- Code quality assessment
- Performance analysis
- Multiple analysis strategies
"""

from .analyze_code import (
    AnalysisResult,
    AnalysisType,
    AnalysisTypeError,
    ASTParseError,
    CodeAnalysisError,
    CodeAnalyzer,
    CodeIssue,
    CodeMetrics,
    Severity,
    analyze_code,
    detect_language,
)

__all__ = [
    # Public API
    "analyze_code",
    "detect_language",
    # Core classes
    "CodeAnalyzer",
    # Result types
    "AnalysisResult",
    "CodeIssue",
    "CodeMetrics",
    # Enums
    "AnalysisType",
    "Severity",
    # Exceptions
    "CodeAnalysisError",
    "ASTParseError",
    "AnalysisTypeError",
]
