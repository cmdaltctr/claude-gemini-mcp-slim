#!/usr/bin/env python3
"""
Codebase Analyzer Tool Module

This module provides comprehensive codebase analysis capabilities including:
- Full directory/project analysis
- Technology stack detection
- Project structure analysis
- Multi-language support
- Intelligent content aggregation
"""

from .code_analyzer import CodeAnalyzerAPI  # noqa: F401
from .code_analyzer import (
    CodebaseAnalysisError,
    CodebaseAnalysisResult,
    analyze_codebase,
)
from .codebase_analyzer import (
    AnalysisScope,
    ArchitectureInfo,
    CodebaseAnalyzer,
    CodebaseStats,
    FileDiscoveryError,
    FileFilter,
    ProjectStructure,
    TechStackInfo,
    aggregate_contents,
    build_project_report,
    discover_files,
)

__all__ = [
    "analyze_codebase",
    "CodeAnalyzerAPI",
    "CodebaseAnalyzer",
    "discover_files",
    "aggregate_contents",
    "build_project_report",
    "CodebaseAnalysisResult",
    "CodebaseAnalysisError",
    "AnalysisScope",
    "ArchitectureInfo",
    "CodebaseStats",
    "FileDiscoveryError",
    "FileFilter",
    "ProjectStructure",
    "TechStackInfo",
]
