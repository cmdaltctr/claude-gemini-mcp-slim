#!/usr/bin/env python3
"""
Polyglot Code Analysis Tool Module

This module provides intelligent, multi-language code analysis including:
- Smart language detection and routing
- Python, TypeScript, and JavaScript analysis
- Security vulnerability detection
- Code quality assessment
- Performance analysis
- Extensible architecture for additional languages

The module maintains backward compatibility with existing Python-focused APIs
while adding polyglot capabilities through intelligent routing.
"""

import logging
from typing import Any, Dict, Optional, Union

# Import base types and interfaces
from .base import (
    AnalysisResult,
    AnalysisType,
    AnalysisTypeError,
    CodeAnalysisError,
    CodeIssue,
    CodeMetrics,
    LanguageAnalyzer,
    ParseError,
    Severity,
    SupportedLanguage,
    UnsupportedLanguageError,
)

# Import router functionality
from .router import detect_language, get_router, route_analysis

# Configure logging
logger = logging.getLogger(__name__)

# For backward compatibility, keep these exception names
ASTParseError = ParseError


def analyze_code(
    code: str,
    analysis_type: Union[AnalysisType, str] = AnalysisType.COMPREHENSIVE,
    file_path: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    force_language: Optional[str] = None
) -> AnalysisResult:
    """
    Analyze code with intelligent language detection and routing

    This function provides the main entry point for polyglot code analysis.
    It automatically detects the programming language and routes to the
    appropriate analyzer, maintaining backward compatibility with the
    original Python-focused API.

    Args:
        code: Source code to analyze
        analysis_type: Type of analysis to perform
        file_path: Optional file path for context and language detection
        context: Optional additional context data
        force_language: Force specific language analysis (skip detection)

    Returns:
        AnalysisResult with metrics, issues, and suggestions

    Example:
        >>> result = analyze_code("def hello(): print('world')", AnalysisType.QUALITY)
        >>> print(f"Language: {result.language}")
        >>> print(f"Quality score: {result.quality_score}")
        >>> for issue in result.issues:
        ...     print(f"{issue.severity.value}: {issue.message}")
    """
    try:
        router = get_router()
        return router.route_analysis(
            code=code,
            analysis_type=analysis_type,
            file_path=file_path,
            context=context,
            force_language=force_language
        )
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")

        # Return error result for graceful handling
        return AnalysisResult(
            file_path=file_path,
            language=force_language or "unknown",
            error=str(e)
        )


class CodeAnalyzer:
    """
    Backward compatibility wrapper for the original CodeAnalyzer class

    This class provides the same interface as the original analyzer but
    now uses the polyglot routing system internally.
    """

    def __init__(self, code: str, file_path: Optional[str] = None):
        """Initialize analyzer with code content"""
        self.code = code
        self.file_path = file_path
        self.router = get_router()

        # Detect language on initialization
        self.detected_language, self.confidence = self.router.detect_language(
            code, file_path
        )

        logger.debug(f"Initialized analyzer for {self.detected_language.value} "
                    f"(confidence: {self.confidence:.1f}%)")

    def analyze(self,
               analysis_type: Union[AnalysisType, str],
               context: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Perform code analysis with specified type

        Args:
            analysis_type: Type of analysis to perform
            context: Optional additional context

        Returns:
            AnalysisResult with findings and metrics
        """
        return self.router.route_analysis(
            code=self.code,
            analysis_type=analysis_type,
            file_path=self.file_path,
            context=context,
            force_language=self.detected_language
        )

    def calculate_metrics(self) -> CodeMetrics:
        """Calculate comprehensive code metrics"""
        result = self.analyze(AnalysisType.COMPREHENSIVE)
        return result.metrics

    @property
    def language(self) -> str:
        """Get detected language"""
        return self.detected_language.value

    @property
    def detection_confidence(self) -> float:
        """Get language detection confidence"""
        return self.confidence


# Additional utility functions for polyglot analysis
def get_supported_languages() -> list[str]:
    """Get list of supported programming languages"""
    router = get_router()
    return [lang.value for lang in router.get_available_languages()]


def analyze_multiple_files(files: Dict[str, str],
                          analysis_type: Union[AnalysisType, str] = AnalysisType.COMPREHENSIVE,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, AnalysisResult]:
    """
    Analyze multiple files with polyglot support

    Args:
        files: Dictionary mapping file paths to code content
        analysis_type: Type of analysis to perform
        context: Optional additional context

    Returns:
        Dictionary mapping file paths to analysis results
    """
    results = {}

    for file_path, code in files.items():
        try:
            results[file_path] = analyze_code(
                code=code,
                analysis_type=analysis_type,
                file_path=file_path,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            results[file_path] = AnalysisResult(
                file_path=file_path,
                error=str(e)
            )

    return results


def get_analysis_summary(results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
    """
    Generate summary statistics from multiple analysis results

    Args:
        results: Dictionary of analysis results

    Returns:
        Dictionary with summary statistics
    """
    if not results:
        return {}

    total_files = len(results)
    successful_analyses = sum(1 for r in results.values() if not r.error)

    # Language distribution
    languages = {}
    total_issues = 0
    avg_scores = {'security': 0, 'quality': 0, 'performance': 0}

    for result in results.values():
        if not result.error:
            # Count languages
            lang = result.language
            languages[lang] = languages.get(lang, 0) + 1

            # Count issues
            total_issues += len(result.issues)

            # Accumulate scores
            avg_scores['security'] += result.security_score
            avg_scores['quality'] += result.quality_score
            avg_scores['performance'] += result.performance_score

    # Calculate averages
    if successful_analyses > 0:
        for key in avg_scores:
            avg_scores[key] /= successful_analyses

    return {
        'total_files': total_files,
        'successful_analyses': successful_analyses,
        'failed_analyses': total_files - successful_analyses,
        'languages': languages,
        'total_issues': total_issues,
        'average_scores': avg_scores
    }


# Export public API - maintaining backward compatibility
__all__ = [
    # Core functions (backward compatible)
    "analyze_code",
    "detect_language",

    # Core classes (backward compatible)
    "CodeAnalyzer",

    # Result types (updated to polyglot versions)
    "AnalysisResult",
    "CodeIssue",
    "CodeMetrics",

    # Enums (updated)
    "AnalysisType",
    "Severity",
    "SupportedLanguage",

    # Exceptions (backward compatible names)
    "CodeAnalysisError",
    "ASTParseError",  # Alias for ParseError
    "ParseError",
    "AnalysisTypeError",
    "UnsupportedLanguageError",

    # New polyglot functionality
    "LanguageAnalyzer",
    "get_supported_languages",
    "analyze_multiple_files",
    "get_analysis_summary",
    "get_router",
    "route_analysis",
]
