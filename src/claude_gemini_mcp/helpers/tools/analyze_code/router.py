#!/usr/bin/env python3
"""
Smart Router for Polyglot Code Analysis

This module provides intelligent language detection and routing capabilities
for the polyglot code analysis system. It determines the appropriate language
analyzer based on file extensions, content patterns, and heuristics.

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-04
Architecture: Smart Routing with Fallback Strategies
"""

import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .base import (
    AnalysisResult,
    AnalysisType,
    CodeAnalysisError,
    LanguageAnalyzer,
    LanguagePatterns,
    SupportedLanguage,
    UnsupportedLanguageError
)

# Configure logging
logger = logging.getLogger(__name__)


class LanguageRouter:
    """
    Intelligent language detection and routing system

    This router determines the appropriate language analyzer for given code
    using multiple detection strategies with confidence scoring.
    """

    def __init__(self):
        """Initialize the router with available analyzers"""
        self.analyzers: Dict[SupportedLanguage, LanguageAnalyzer] = {}
        self.detection_cache: Dict[str, Tuple[SupportedLanguage, float]] = {}
        self.cache_max_size = 1000
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize analyzers (lazy loading)
        self._initialize_analyzers()

    def _initialize_analyzers(self):
        """Initialize available language analyzers with lazy loading"""
        # Note: Actual analyzer instances will be loaded when first needed
        # to avoid import errors if dependencies are missing
        pass

    def register_analyzer(self, language: SupportedLanguage, analyzer: LanguageAnalyzer):
        """
        Register a language analyzer

        Args:
            language: Language this analyzer handles
            analyzer: Analyzer instance
        """
        self.analyzers[language] = analyzer
        self.logger.info(f"Registered analyzer for {language.value}")

    def get_available_languages(self) -> List[SupportedLanguage]:
        """Get list of languages with available analyzers (including lazy-loadable ones)"""
        # Return all supported languages that have analyzers available
        # This includes both registered and lazy-loadable analyzers
        available_languages = [
            SupportedLanguage.PYTHON,
            SupportedLanguage.TYPESCRIPT,
            SupportedLanguage.JAVASCRIPT
        ]
        return available_languages

    def detect_language(self,
                       code: str,
                       file_path: Optional[str] = None,
                       use_cache: bool = True) -> Tuple[SupportedLanguage, float]:
        """
        Detect programming language using multi-stage approach

        Args:
            code: Source code content
            file_path: Optional file path for additional context
            use_cache: Whether to use detection cache

        Returns:
            Tuple of (detected_language, confidence_score)
        """
        # Check cache first
        cache_key = self._get_cache_key(code, file_path)
        if use_cache and cache_key in self.detection_cache:
            return self.detection_cache[cache_key]

        start_time = time.time()

        # Stage 1: File extension detection (high confidence)
        extension_result = self._detect_by_extension(file_path)

        # Stage 2: Content pattern analysis (medium confidence)
        pattern_results = self._detect_by_patterns(code)

        # Stage 3: Analyzer validation (high confidence boost)
        analyzer_results = self._detect_by_analyzers(code, file_path)

        # Stage 4: Combine results and determine best match
        final_result = self._combine_detection_results(
            extension_result, pattern_results, analyzer_results
        )

        detection_time = time.time() - start_time
        self.logger.debug(f"Language detection took {detection_time:.3f}s")

        # Cache result
        if use_cache:
            self._cache_result(cache_key, final_result)

        return final_result

    def route_analysis(self,
                      code: str,
                      analysis_type: Union[AnalysisType, str],
                      file_path: Optional[str] = None,
                      context: Optional[Dict] = None,
                      force_language: Optional[Union[SupportedLanguage, str]] = None) -> AnalysisResult:
        """
        Route analysis to appropriate language analyzer

        Args:
            code: Source code to analyze
            analysis_type: Type of analysis to perform
            file_path: Optional file path for context
            context: Optional additional context
            force_language: Force specific language (skip detection)

        Returns:
            AnalysisResult from appropriate analyzer

        Raises:
            UnsupportedLanguageError: If no suitable analyzer found
            CodeAnalysisError: For other analysis errors
        """
        start_time = time.time()

        try:
            # Determine language
            if force_language:
                if isinstance(force_language, str):
                    language = SupportedLanguage(force_language)
                else:
                    language = force_language
                confidence = 100.0
            else:
                language, confidence = self.detect_language(code, file_path)

            self.logger.info(f"Routing to {language.value} analyzer (confidence: {confidence:.1f}%)")

            # Get appropriate analyzer
            analyzer = self._get_analyzer(language)

            # Perform analysis
            result = analyzer.analyze(code, analysis_type, file_path, context)

            # Add routing metadata
            result.language = language.value
            if not hasattr(result, 'language_specific'):
                result.language_specific = {}
            result.language_specific['detection_confidence'] = confidence
            result.language_specific['routing_time'] = time.time() - start_time

            return result

        except Exception as e:
            # Create error result
            error_result = AnalysisResult(
                file_path=file_path,
                language="unknown",
                error=str(e),
                analysis_time=time.time() - start_time
            )

            if isinstance(e, UnsupportedLanguageError):
                self.logger.warning(f"No analyzer available for detected language: {e}")
                # Try fallback analysis
                return self._try_fallback_analysis(code, analysis_type, file_path, context, error_result)
            else:
                self.logger.error(f"Analysis routing failed: {e}")
                raise

    def _detect_by_extension(self, file_path: Optional[str]) -> Optional[Tuple[SupportedLanguage, float]]:
        """Detect language by file extension"""
        if not file_path:
            return None

        detected = LanguagePatterns.detect_language_by_extension(file_path)
        if detected:
            return (detected, 90.0)  # High confidence for extension matches
        return None

    def _detect_by_patterns(self, code: str) -> Dict[SupportedLanguage, float]:
        """Detect language using content patterns"""
        pattern_scores = LanguagePatterns.detect_language_by_patterns(code)

        # Convert raw scores to confidence percentages
        if not pattern_scores:
            return {}

        max_score = max(pattern_scores.values())
        if max_score == 0:
            return {}

        # Normalize scores to 0-60 range (medium confidence)
        confidence_scores = {}
        for lang, score in pattern_scores.items():
            confidence = min(60.0, (score / max_score) * 60.0)
            if confidence > 10.0:  # Only include meaningful scores
                confidence_scores[lang] = confidence

        return confidence_scores

    def _detect_by_analyzers(self, code: str, file_path: Optional[str]) -> Dict[SupportedLanguage, float]:
        """Use registered analyzers to validate language detection"""
        analyzer_scores = {}

        for language, analyzer in self.analyzers.items():
            try:
                confidence = analyzer.detect_language_confidence(code, file_path)
                if confidence > 0:
                    analyzer_scores[language] = confidence
            except Exception as e:
                self.logger.debug(f"Analyzer {language.value} failed confidence check: {e}")
                continue

        return analyzer_scores

    def _combine_detection_results(self,
                                 extension_result: Optional[Tuple[SupportedLanguage, float]],
                                 pattern_results: Dict[SupportedLanguage, float],
                                 analyzer_results: Dict[SupportedLanguage, float]) -> Tuple[SupportedLanguage, float]:
        """Combine all detection results to determine best match"""

        combined_scores: Dict[SupportedLanguage, float] = {}

        # Add extension result (high weight)
        if extension_result:
            lang, conf = extension_result
            combined_scores[lang] = combined_scores.get(lang, 0) + conf

        # Add pattern results (medium weight)
        for lang, conf in pattern_results.items():
            combined_scores[lang] = combined_scores.get(lang, 0) + conf

        # Add analyzer results (high weight)
        for lang, conf in analyzer_results.items():
            combined_scores[lang] = combined_scores.get(lang, 0) + conf

        if not combined_scores:
            return (SupportedLanguage.UNKNOWN, 0.0)

        # Find highest scoring language
        best_language = max(combined_scores.items(), key=lambda x: x[1])
        language, score = best_language

        # Normalize confidence to 0-100 range
        max_possible_score = 90.0 + 60.0 + 100.0  # extension + pattern + analyzer
        confidence = min(100.0, (score / max_possible_score) * 100.0)

        return (language, confidence)

    def _get_analyzer(self, language: SupportedLanguage) -> LanguageAnalyzer:
        """
        Get analyzer for specified language with lazy loading

        Args:
            language: Target language

        Returns:
            Language analyzer instance

        Raises:
            UnsupportedLanguageError: If no analyzer available
        """
        if language == SupportedLanguage.UNKNOWN:
            raise UnsupportedLanguageError("Cannot analyze unknown language")

        if language not in self.analyzers:
            # Try lazy loading the analyzer
            self._lazy_load_analyzer(language)

        if language not in self.analyzers:
            raise UnsupportedLanguageError(f"No analyzer available for {language.value}")

        return self.analyzers[language]

    def _lazy_load_analyzer(self, language: SupportedLanguage):
        """Lazy load analyzer for specified language"""
        try:
            if language == SupportedLanguage.PYTHON:
                from .python.analyze_code_py import PythonAnalyzer
                self.register_analyzer(language, PythonAnalyzer())
            elif language == SupportedLanguage.TYPESCRIPT:
                from .typescript.analyze_code_ts import TypeScriptAnalyzer
                self.register_analyzer(language, TypeScriptAnalyzer())
            elif language == SupportedLanguage.JAVASCRIPT:
                from .javascript.analyze_code_js import JavaScriptAnalyzer
                self.register_analyzer(language, JavaScriptAnalyzer())
        except ImportError as e:
            self.logger.warning(f"Failed to load {language.value} analyzer: {e}")
        except Exception as e:
            self.logger.error(f"Error loading {language.value} analyzer: {e}")

    def _try_fallback_analysis(self,
                              code: str,
                              analysis_type: Union[AnalysisType, str],
                              file_path: Optional[str],
                              context: Optional[Dict],
                              error_result: AnalysisResult) -> AnalysisResult:
        """
        Try fallback analysis strategies when no specific analyzer available

        Args:
            code: Source code
            analysis_type: Analysis type requested
            file_path: File path context
            context: Additional context
            error_result: Error result to return if all fallbacks fail

        Returns:
            Basic analysis result or error result
        """
        try:
            # Try basic text analysis as fallback
            from .fallback import FallbackAnalyzer
            fallback = FallbackAnalyzer()
            return fallback.analyze(code, analysis_type, file_path, context)
        except ImportError:
            # No fallback analyzer available
            self.logger.debug("No fallback analyzer available")
        except Exception as e:
            self.logger.warning(f"Fallback analysis failed: {e}")

        return error_result

    def _get_cache_key(self, code: str, file_path: Optional[str]) -> str:
        """Generate cache key for detection results"""
        import hashlib
        content = f"{code[:1000]}{file_path or ''}"  # Use first 1000 chars + file path
        return hashlib.md5(content.encode()).hexdigest()

    def _cache_result(self, key: str, result: Tuple[SupportedLanguage, float]):
        """Cache detection result with size limit"""
        if len(self.detection_cache) >= self.cache_max_size:
            # Remove oldest entries (simple FIFO)
            oldest_keys = list(self.detection_cache.keys())[:self.cache_max_size // 4]
            for old_key in oldest_keys:
                del self.detection_cache[old_key]

        self.detection_cache[key] = result

    def clear_cache(self):
        """Clear the detection cache"""
        self.detection_cache.clear()
        self.logger.debug("Detection cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.detection_cache),
            'cache_max_size': self.cache_max_size
        }


# Singleton router instance for global use
_global_router: Optional[LanguageRouter] = None


def get_router() -> LanguageRouter:
    """Get global router instance (singleton pattern)"""
    global _global_router
    if _global_router is None:
        _global_router = LanguageRouter()
    return _global_router


# Utility functions for direct use
def detect_language(code: str, file_path: Optional[str] = None) -> Tuple[str, float]:
    """
    Detect programming language for given code

    Args:
        code: Source code content
        file_path: Optional file path for context

    Returns:
        Tuple of (language_name, confidence_score)
    """
    router = get_router()
    language, confidence = router.detect_language(code, file_path)
    return (language.value, confidence)


def route_analysis(code: str,
                  analysis_type: Union[AnalysisType, str] = AnalysisType.COMPREHENSIVE,
                  file_path: Optional[str] = None,
                  context: Optional[Dict] = None,
                  force_language: Optional[str] = None) -> AnalysisResult:
    """
    Route code analysis to appropriate language analyzer

    Args:
        code: Source code to analyze
        analysis_type: Type of analysis to perform
        file_path: Optional file path for context
        context: Optional additional context
        force_language: Force specific language (skip detection)

    Returns:
        AnalysisResult from appropriate analyzer
    """
    router = get_router()
    return router.route_analysis(code, analysis_type, file_path, context, force_language)


# Export public API
__all__ = [
    'LanguageRouter',
    'get_router',
    'detect_language',
    'route_analysis'
]
