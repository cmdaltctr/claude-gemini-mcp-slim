#!/usr/bin/env python3
"""
Base Classes and Interfaces for Polyglot Code Analysis

This module provides the foundation for the polyglot code analysis system,
defining shared interfaces, data structures, and base classes that all
language-specific analyzers must implement.

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-04
Architecture: Plugin-based Polyglot Analysis System
"""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


# Analysis types supported across all languages
class AnalysisType(Enum):
    """Analysis types supported by all language analyzers"""

    COMPREHENSIVE = "comprehensive"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"
    QUALITY = "quality"


# Severity levels for issues found during analysis
class Severity(Enum):
    """Issue severity levels consistent across all languages"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Supported programming languages
class SupportedLanguage(Enum):
    """Supported programming languages for analysis"""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    UNKNOWN = "unknown"


# Code issue representation
@dataclass
class CodeIssue:
    """Represents a code issue found during analysis - consistent across languages"""

    type: str                           # Issue category (security, quality, performance)
    message: str                        # Human-readable issue description
    line: int                          # Line number where issue occurs
    column: int = 0                    # Column position (if available)
    severity: Severity = Severity.MEDIUM  # Issue severity level
    file_path: Optional[str] = None    # File path context
    suggestion: Optional[str] = None   # Remediation suggestion
    rule_id: Optional[str] = None      # Specific rule identifier
    language: Optional[str] = None     # Language context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'type': self.type,
            'message': self.message,
            'line': self.line,
            'column': self.column,
            'severity': self.severity.value,
            'file_path': self.file_path,
            'suggestion': self.suggestion,
            'rule_id': self.rule_id,
            'language': self.language
        }


# Code metrics consistent across languages
@dataclass
class CodeMetrics:
    """Code metrics and complexity measurements - language-agnostic where possible"""

    lines_of_code: int = 0             # Total lines including comments/blanks
    logical_lines: int = 0             # Lines with actual code
    comment_lines: int = 0             # Lines with comments
    blank_lines: int = 0               # Empty lines
    cyclomatic_complexity: int = 0     # Cyclomatic complexity (max)
    cognitive_complexity: int = 0      # Cognitive complexity score
    maintainability_index: float = 0.0 # Maintainability index (0-100)
    halstead_volume: float = 0.0       # Halstead volume metric
    function_count: int = 0            # Number of functions/methods
    class_count: int = 0               # Number of classes/types
    import_count: int = 0              # Number of imports/dependencies
    max_nesting_depth: int = 0         # Maximum nesting depth

    # Language-specific metrics (optional)
    language_specific: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'lines_of_code': self.lines_of_code,
            'logical_lines': self.logical_lines,
            'comment_lines': self.comment_lines,
            'blank_lines': self.blank_lines,
            'cyclomatic_complexity': self.cyclomatic_complexity,
            'cognitive_complexity': self.cognitive_complexity,
            'maintainability_index': self.maintainability_index,
            'halstead_volume': self.halstead_volume,
            'function_count': self.function_count,
            'class_count': self.class_count,
            'import_count': self.import_count,
            'max_nesting_depth': self.max_nesting_depth,
            'language_specific': self.language_specific
        }


# Analysis results consistent across all languages
@dataclass
class AnalysisResult:
    """Complete analysis results for code - standardized across languages"""

    file_path: Optional[str] = None     # Source file path
    language: str = "unknown"           # Detected/specified language
    metrics: CodeMetrics = field(default_factory=CodeMetrics)  # Code metrics
    issues: List[CodeIssue] = field(default_factory=list)      # Found issues
    suggestions: List[str] = field(default_factory=list)       # General suggestions
    security_score: float = 100.0      # Security score (0-100)
    quality_score: float = 100.0       # Quality score (0-100)
    performance_score: float = 100.0   # Performance score (0-100)
    analysis_time: float = 0.0         # Time taken for analysis (seconds)
    ast_hash: Optional[str] = None      # Hash of parsed AST (for caching)
    error: Optional[str] = None         # Error message if analysis failed

    # Language-specific data
    language_specific: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'file_path': self.file_path,
            'language': self.language,
            'metrics': self.metrics.to_dict(),
            'issues': [issue.to_dict() for issue in self.issues],
            'suggestions': self.suggestions,
            'security_score': self.security_score,
            'quality_score': self.quality_score,
            'performance_score': self.performance_score,
            'analysis_time': self.analysis_time,
            'ast_hash': self.ast_hash,
            'error': self.error,
            'language_specific': self.language_specific
        }


# Base exception classes for analysis errors
class CodeAnalysisError(Exception):
    """Base exception for code analysis errors"""

    def __init__(self, message: str, language: Optional[str] = None):
        super().__init__(message)
        self.language = language


class UnsupportedLanguageError(CodeAnalysisError):
    """Raised when a language is not supported by any analyzer"""
    pass


class ParseError(CodeAnalysisError):
    """Raised when code parsing fails"""
    pass


class DependencyMissingError(CodeAnalysisError):
    """Raised when required parser dependencies are missing"""
    pass


class AnalysisTypeError(CodeAnalysisError):
    """Raised when an invalid analysis type is requested"""
    pass


# Base interface for all language analyzers
class LanguageAnalyzer(ABC):
    """Abstract base class for all language-specific analyzers"""

    def __init__(self):
        """Initialize the analyzer"""
        self.name = self.__class__.__name__
        self.supported_extensions = self.get_supported_extensions()
        self.logger = logging.getLogger(f"{__name__}.{self.name}")

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions (e.g., ['.py', '.pyx'])"""
        pass

    @abstractmethod
    def get_language_name(self) -> str:
        """Return the language name this analyzer handles"""
        pass

    @abstractmethod
    def can_analyze(self, code: str, file_path: Optional[str] = None) -> bool:
        """
        Determine if this analyzer can handle the given code

        Args:
            code: Source code content
            file_path: Optional file path for additional context

        Returns:
            True if this analyzer can handle the code, False otherwise
        """
        pass

    @abstractmethod
    def analyze(self,
               code: str,
               analysis_type: Union[AnalysisType, str],
               file_path: Optional[str] = None,
               context: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Perform language-specific code analysis

        Args:
            code: Source code to analyze
            analysis_type: Type of analysis to perform
            file_path: Optional file path for context
            context: Optional additional context data

        Returns:
            AnalysisResult with findings and metrics

        Raises:
            ParseError: If code cannot be parsed
            AnalysisTypeError: If analysis type is not supported
            CodeAnalysisError: For other analysis errors
        """
        pass

    def detect_language_confidence(self, code: str, file_path: Optional[str] = None) -> float:
        """
        Return confidence score (0-100) that this analyzer can handle the code

        This default implementation uses basic heuristics. Language-specific
        analyzers should override this for better accuracy.

        Args:
            code: Source code content
            file_path: Optional file path for additional context

        Returns:
            Confidence score (0-100)
        """
        confidence = 0.0

        # File extension check
        if file_path:
            ext = Path(file_path).suffix.lower()
            if ext in self.supported_extensions:
                confidence += 80.0

        # Basic syntax check
        if self.can_analyze(code, file_path):
            confidence += 20.0

        return min(confidence, 100.0)

    def calculate_ast_hash(self, ast_or_code: Any) -> str:
        """
        Calculate hash of AST or code for caching purposes

        Args:
            ast_or_code: AST object or source code string

        Returns:
            MD5 hash string
        """
        if isinstance(ast_or_code, str):
            content = ast_or_code
        else:
            # Convert AST to string representation
            content = str(ast_or_code)

        return hashlib.md5(content.encode()).hexdigest()

    def _calculate_scores(self, issues: List[CodeIssue]) -> Dict[str, float]:
        """
        Calculate quality scores based on found issues

        Args:
            issues: List of code issues found

        Returns:
            Dictionary with security, quality, and performance scores
        """
        scores = {
            'security_score': 100.0,
            'quality_score': 100.0,
            'performance_score': 100.0
        }

        for issue in issues:
            # Determine which score to impact based on issue type
            score_key = f"{issue.type}_score"
            if score_key not in scores:
                continue

            # Calculate penalty based on severity
            penalty = {
                Severity.CRITICAL: 25,
                Severity.HIGH: 15,
                Severity.MEDIUM: 10,
                Severity.LOW: 5
            }.get(issue.severity, 5)

            scores[score_key] = max(0.0, scores[score_key] - penalty)

        return scores


# Base class for analysis strategies within language analyzers
class BaseAnalysisStrategy(ABC):
    """Base class for analysis strategies (security, quality, performance)"""

    def __init__(self, language: str):
        """Initialize strategy with language context"""
        self.language = language
        self.issues: List[CodeIssue] = []
        self.suggestions: List[str] = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def execute(self, ast_or_code: Any, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the analysis strategy

        Args:
            ast_or_code: Parsed AST or code object
            code: Original source code string
            context: Analysis context

        Returns:
            Dictionary with strategy results
        """
        pass

    def add_issue(self,
                 issue_type: str,
                 message: str,
                 line: int,
                 column: int = 0,
                 severity: Severity = Severity.MEDIUM,
                 suggestion: Optional[str] = None,
                 rule_id: Optional[str] = None,
                 file_path: Optional[str] = None):
        """
        Add an issue to the results

        Args:
            issue_type: Type/category of the issue
            message: Human-readable description
            line: Line number where issue occurs
            column: Column position (optional)
            severity: Issue severity level
            suggestion: Remediation suggestion (optional)
            rule_id: Specific rule identifier (optional)
            file_path: File path context (optional)
        """
        issue = CodeIssue(
            type=issue_type,
            message=message,
            line=line,
            column=column,
            severity=severity,
            suggestion=suggestion,
            rule_id=rule_id,
            language=self.language,
            file_path=file_path
        )
        self.issues.append(issue)

    def add_suggestion(self, suggestion: str):
        """Add a general suggestion to the results"""
        if suggestion not in self.suggestions:
            self.suggestions.append(suggestion)


# Language detection utilities
class LanguagePatterns:
    """Language detection patterns and utilities"""

    # Common patterns for language detection
    PATTERNS = {
        SupportedLanguage.PYTHON: [
            r'^import\s+\w+',
            r'^from\s+\w+\s+import',
            r'def\s+\w+\s*\(',
            r'class\s+\w+\s*[\(:]',
            r'if\s+__name__\s*==\s*["\']__main__["\']',
            r'#.*python',
            r'print\s*\(',
            r'\.py$'  # file extension pattern
        ],
        SupportedLanguage.TYPESCRIPT: [
            r'interface\s+\w+',
            r'type\s+\w+\s*=',
            r'import.*from\s+["\'].*["\']',
            r'export\s+(interface|type|class)',
            r':\s*\w+(\[\]|\<.*\>)?',
            r'\.tsx?$',  # file extension pattern
            r'declare\s+(const|let|var|function|class)',
            r'namespace\s+\w+'
        ],
        SupportedLanguage.JAVASCRIPT: [
            r'function\s+\w+\s*\(',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'import.*from\s+["\'].*["\']',
            r'module\.exports\s*=',
            r'require\s*\(',
            r'\.jsx?$',  # file extension pattern
            r'console\.(log|error|warn)'
        ]
    }

    # File extension mappings
    EXTENSION_MAP = {
        '.py': SupportedLanguage.PYTHON,
        '.pyx': SupportedLanguage.PYTHON,
        '.pyi': SupportedLanguage.PYTHON,
        '.ts': SupportedLanguage.TYPESCRIPT,
        '.tsx': SupportedLanguage.TYPESCRIPT,
        '.js': SupportedLanguage.JAVASCRIPT,
        '.jsx': SupportedLanguage.JAVASCRIPT,
        '.mjs': SupportedLanguage.JAVASCRIPT,
        '.cjs': SupportedLanguage.JAVASCRIPT,
    }

    @classmethod
    def detect_language_by_patterns(cls, code: str) -> Dict[SupportedLanguage, int]:
        """
        Detect language using pattern matching

        Args:
            code: Source code content

        Returns:
            Dictionary mapping languages to confidence scores
        """
        scores = {}

        for language, patterns in cls.PATTERNS.items():
            score = 0
            for pattern in patterns:
                if pattern.endswith('$'):  # Skip file extension patterns for content analysis
                    continue
                matches = len([m for m in __import__('re').finditer(pattern, code, __import__('re').IGNORECASE | __import__('re').MULTILINE)])
                score += matches * 10
            scores[language] = score

        return scores

    @classmethod
    def detect_language_by_extension(cls, file_path: str) -> Optional[SupportedLanguage]:
        """
        Detect language by file extension

        Args:
            file_path: Path to the file

        Returns:
            Detected language or None if not recognized
        """
        if not file_path:
            return None

        ext = Path(file_path).suffix.lower()
        return cls.EXTENSION_MAP.get(ext)


# Export public API
__all__ = [
    # Core classes
    'LanguageAnalyzer',
    'BaseAnalysisStrategy',

    # Data structures
    'AnalysisResult',
    'CodeIssue',
    'CodeMetrics',

    # Enums
    'AnalysisType',
    'Severity',
    'SupportedLanguage',

    # Exceptions
    'CodeAnalysisError',
    'UnsupportedLanguageError',
    'ParseError',
    'DependencyMissingError',
    'AnalysisTypeError',

    # Utilities
    'LanguagePatterns'
]
