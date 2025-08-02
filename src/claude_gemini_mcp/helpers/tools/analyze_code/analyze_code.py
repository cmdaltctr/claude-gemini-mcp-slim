#!/usr/bin/env python3
"""
Single File/Snippet Code Analysis Module

This module provides deep, focused analysis of individual code files or snippets using
AST parsing and strategic analysis patterns. Designed for:
- Code review & quality assessment
- Refactoring recommendations
- Bug hunting & security audits
- Algorithm analysis
- Language-specific pattern detection

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-20
Architecture: Strategy Pattern with AST Visitor Implementation
"""

import ast
import hashlib
import logging
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


# Define analysis types
class AnalysisType(Enum):
    """Analysis types supported by the analyzer"""

    COMPREHENSIVE = "comprehensive"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"
    QUALITY = "quality"


# Define severity levels
class Severity(Enum):
    """Issue severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Define code issue class
@dataclass
class CodeIssue:
    """Represents a code issue found during analysis"""

    type: str
    message: str
    line: int
    column: int = 0
    severity: Severity = Severity.MEDIUM
    file_path: Optional[str] = None
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None


# Define code metrics class
@dataclass
class CodeMetrics:
    """Code metrics and complexity measurements"""

    lines_of_code: int = 0
    logical_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    maintainability_index: float = 0.0
    halstead_volume: float = 0.0
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    max_nesting_depth: int = 0


# Define analysis result class
@dataclass
class AnalysisResult:
    """Complete analysis results for a code snippet"""

    file_path: Optional[str] = None
    language: str = "python"
    metrics: CodeMetrics = field(default_factory=CodeMetrics)
    issues: List[CodeIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    security_score: float = 100.0
    quality_score: float = 100.0
    performance_score: float = 100.0
    analysis_time: float = 0.0
    ast_hash: Optional[str] = None
    error: Optional[str] = None


# Define base exception class
class CodeAnalysisError(Exception):
    """Base exception for code analysis errors"""


# Define specific exception classes
class ASTParseError(CodeAnalysisError):
    """Raised when AST parsing fails"""


# Define analysis type error class
class AnalysisTypeError(CodeAnalysisError):
    """Raised when invalid analysis type is requested"""


# Define base analysis strategy class
class BaseAnalysisStrategy:
    """Base class for analysis strategies"""

    # Initialize issues and suggestions
    def __init__(self):
        self.issues: List[CodeIssue] = []
        self.suggestions: List[str] = []

    # Execute the analysis strategy
    def execute(
        self, tree: ast.AST, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the analysis strategy"""
        raise NotImplementedError

    # Add an issue to the results
    def add_issue(
        self,
        issue_type: str,
        message: str,
        node: ast.AST,
        severity: Severity = Severity.MEDIUM,
        suggestion: str = None,
    ):
        """Add an issue to the results"""
        issue = CodeIssue(
            type=issue_type,
            message=message,
            line=getattr(node, "lineno", 0),
            column=getattr(node, "col_offset", 0),
            severity=severity,
            suggestion=suggestion,
        )
        self.issues.append(issue)


# Define security analysis strategy class
class SecurityAnalysisStrategy(BaseAnalysisStrategy):
    """Security vulnerability detection strategy"""

    DANGEROUS_FUNCTIONS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "input" if sys.version_info[0] == 2 else None,
    }

    DANGEROUS_MODULES = {
        "subprocess",
        "os",
        "sys",
        "pickle",
        "shelve",
        "marshal",
        "tempfile",
        "urllib",
        "socket",
    }

    # Execute security analysis
    def execute(
        self, tree: ast.AST, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute security analysis"""
        visitor = SecurityVisitor(self)
        visitor.visit(tree)

        # Additional security checks
        self._check_hardcoded_secrets(code)
        self._check_sql_injection_patterns(tree)
        self._check_command_injection(tree)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "security_score": self._calculate_security_score(),
        }

    # Check for hardcoded secrets in code
    def _check_hardcoded_secrets(self, code: str):
        """Check for hardcoded secrets in code"""
        patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password detected"),
            (r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded API key detected"),
            (r'secret\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded secret detected"),
            (r'token\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded token detected"),
        ]
        # Check for hardcoded secrets
        for pattern, message in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issue = CodeIssue(
                    type="security",
                    message=message,
                    line=0,  # Would need more sophisticated line detection
                    severity=Severity.HIGH,
                    suggestion="Use environment variables or secure key management",
                )
                self.issues.append(issue)

    # Check for SQL injection patterns in code
    def _check_sql_injection_patterns(self, tree: ast.AST):
        """Check for potential SQL injection vulnerabilities"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for string formatting in SQL-like contexts
                if self._is_sql_context(node):
                    for arg in node.args:
                        if isinstance(arg, (ast.BinOp, ast.JoinedStr)):
                            self.add_issue(
                                "security",
                                "Potential SQL injection vulnerability",
                                node,
                                Severity.HIGH,
                                "Use parameterized queries instead of string formatting",
                            )

    # Check for command injection patterns in code
    def _check_command_injection(self, tree: ast.AST):
        """Check for command injection vulnerabilities"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in [
                    "system",
                    "popen",
                    "call",
                    "run",
                ]:
                    for arg in node.args:
                        if isinstance(arg, (ast.BinOp, ast.JoinedStr)):
                            self.add_issue(
                                "security",
                                "Potential command injection vulnerability",
                                node,
                                Severity.HIGH,
                                "Avoid shell injection by using subprocess with list arguments",
                            )

    # Check if a function call appears to be SQL-related
    def _is_sql_context(self, node: ast.Call) -> bool:
        """Check if a function call appears to be SQL-related"""
        if isinstance(node.func, ast.Attribute):
            sql_methods = ["execute", "query", "select", "insert", "update", "delete"]
            return node.func.attr.lower() in sql_methods
        return False

    # Calculate security score based on issues found
    def _calculate_security_score(self) -> float:
        """Calculate security score based on issues found"""
        if not self.issues:
            return 100.0

        score = 100.0
        for issue in self.issues:
            if issue.severity == Severity.CRITICAL:
                score -= 25
            elif issue.severity == Severity.HIGH:
                score -= 15
            elif issue.severity == Severity.MEDIUM:
                score -= 10
            else:
                score -= 5

        return max(0.0, score)


# Define quality analysis strategy class
class QualityAnalysisStrategy(BaseAnalysisStrategy):
    """Code quality assessment strategy"""

    def execute(
        self, tree: ast.AST, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute quality analysis"""
        visitor = QualityVisitor(self)
        visitor.visit(tree)

        # Additional quality checks
        self._check_naming_conventions(tree)
        self._check_documentation(tree)
        self._check_complexity(tree)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "quality_score": self._calculate_quality_score(),
        }

    # Check Python naming conventions (PEP 8)
    def _check_naming_conventions(self, tree: ast.AST):
        """Check Python naming conventions (PEP 8)"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r"^[a-z_][a-z0-9_]*$", node.name):
                    self.add_issue(
                        "style",
                        f"Function '{node.name}' doesn't follow snake_case convention",
                        node,
                        Severity.LOW,
                        "Use snake_case for function names",
                    )
            elif isinstance(node, ast.ClassDef):
                if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                    self.add_issue(
                        "style",
                        f"Class '{node.name}' doesn't follow PascalCase convention",
                        node,
                        Severity.LOW,
                        "Use PascalCase for class names",
                    )

    # Check for missing documentation
    def _check_documentation(self, tree: ast.AST):
        """Check for missing documentation"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                has_docstring = (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                )

                if not has_docstring:
                    self.add_issue(
                        "documentation",
                        f"Missing docstring for {type(node).__name__.lower()} '{node.name}'",
                        node,
                        Severity.MEDIUM,
                        "Add docstring to document purpose and parameters",
                    )

    # Check for overly complex functions
    def _check_complexity(self, tree: ast.AST):
        """Check for overly complex functions"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    self.add_issue(
                        "complexity",
                        f"Function '{node.name}' has high cyclomatic complexity ({complexity})",
                        node,
                        Severity.HIGH,
                        "Consider breaking into smaller functions",
                    )

    # Calculate cyclomatic complexity for a function
    def _calculate_cyclomatic_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity

        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    # Calculate quality score based on issues found
    def _calculate_quality_score(self) -> float:
        """Calculate quality score based on issues found"""
        if not self.issues:
            return 100.0

        score = 100.0
        for issue in self.issues:
            if issue.severity == Severity.CRITICAL:
                score -= 20
            elif issue.severity == Severity.HIGH:
                score -= 12
            elif issue.severity == Severity.MEDIUM:
                score -= 8
            else:
                score -= 3

        return max(0.0, score)


# Define performance analysis strategy class
class PerformanceAnalysisStrategy(BaseAnalysisStrategy):
    """Performance analysis strategy"""

    def execute(
        self, tree: ast.AST, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute performance analysis"""
        visitor = PerformanceVisitor(self)
        visitor.visit(tree)

        # Additional performance checks
        self._check_algorithm_complexity(tree)
        self._check_inefficient_patterns(tree)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "performance_score": self._calculate_performance_score(),
        }

    # Check for inefficient algorithm patterns
    def _check_algorithm_complexity(self, tree: ast.AST):
        """Check for inefficient algorithm patterns"""
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check for nested loops
                nested_loops = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.For, ast.While)) and child != node:
                        nested_loops += 1

                if nested_loops >= 2:
                    self.add_issue(
                        "performance",
                        f"Nested loops detected (depth: {nested_loops + 1})",
                        node,
                        Severity.MEDIUM,
                        "Consider optimizing algorithm complexity",
                    )

    # Check for common inefficient patterns
    def _check_inefficient_patterns(self, tree: ast.AST):
        """Check for common inefficient patterns"""
        for node in ast.walk(tree):
            # Check for repeated string concatenation in loops
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.AugAssign)
                        and isinstance(child.op, ast.Add)
                        and isinstance(child.target, ast.Name)
                    ):
                        self.add_issue(
                            "performance",
                            "String concatenation in loop can be inefficient",
                            child,
                            Severity.LOW,
                            "Consider using join() or list comprehension",
                        )

    # Calculate performance score based on issues found
    def _calculate_performance_score(self) -> float:
        """Calculate performance score based on issues found"""
        if not self.issues:
            return 100.0

        score = 100.0
        for issue in self.issues:
            if issue.severity == Severity.CRITICAL:
                score -= 20
            elif issue.severity == Severity.HIGH:
                score -= 15
            elif issue.severity == Severity.MEDIUM:
                score -= 10
            else:
                score -= 5

        return max(0.0, score)


# Define security analysis strategy class
class SecurityVisitor(ast.NodeVisitor):
    """AST visitor for security analysis"""

    # Initialize security visitor
    def __init__(self, strategy: SecurityAnalysisStrategy):
        self.strategy = strategy

    # Visit function calls for security issues
    def visit_Call(self, node):
        """Visit function calls for security issues"""
        if isinstance(node.func, ast.Name):
            if node.func.id in SecurityAnalysisStrategy.DANGEROUS_FUNCTIONS:
                self.strategy.add_issue(
                    "security",
                    f"Use of dangerous function '{node.func.id}'",
                    node,
                    Severity.HIGH,
                    f"Avoid using {node.func.id} with untrusted input",
                )

        self.generic_visit(node)

    # Visit imports for dangerous modules
    def visit_Import(self, node):
        """Visit imports for dangerous modules"""
        for alias in node.names:
            if alias.name in SecurityAnalysisStrategy.DANGEROUS_MODULES:
                self.strategy.add_issue(
                    "security",
                    f"Import of potentially dangerous module '{alias.name}'",
                    node,
                    Severity.MEDIUM,
                    f"Ensure secure usage of {alias.name} module",
                )

        self.generic_visit(node)


# Define quality analysis strategy class
class QualityVisitor(ast.NodeVisitor):
    """AST visitor for quality analysis"""

    # Initialize quality visitor
    def __init__(self, strategy: QualityAnalysisStrategy):
        self.strategy = strategy

    # Visit function definitions for quality issues
    def visit_FunctionDef(self, node):
        """Visit function definitions for quality issues"""
        # Check function length
        if len(node.body) > 50:
            self.strategy.add_issue(
                "quality",
                f"Function '{node.name}' is too long ({len(node.body)} statements)",
                node,
                Severity.MEDIUM,
                "Consider breaking into smaller functions",
            )

        # Check parameter count
        if len(node.args.args) > 5:
            self.strategy.add_issue(
                "quality",
                f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                node,
                Severity.MEDIUM,
                "Consider using a configuration object or reducing parameters",
            )

        self.generic_visit(node)


# Define performance analysis strategy class
class PerformanceVisitor(ast.NodeVisitor):
    """AST visitor for performance analysis"""

    def __init__(self, strategy: PerformanceAnalysisStrategy):
        self.strategy = strategy

    # Visit list comprehensions for performance issues
    def visit_ListComp(self, node):
        """Visit list comprehensions for performance issues"""
        # Check for complex operations in list comprehensions
        for generator in node.generators:
            if len(generator.ifs) > 2:
                self.strategy.add_issue(
                    "performance",
                    "Complex list comprehension with multiple conditions",
                    node,
                    Severity.LOW,
                    "Consider using filter() or breaking into multiple steps",
                )

        self.generic_visit(node)


# Define main code analyzer Class
class CodeAnalyzer:
    """Main code analyzer class using strategy pattern"""

    # Initialize analyzer with code content
    def __init__(self, code: str, file_path: Optional[str] = None):
        """Initialize analyzer with code content"""
        self.code = code
        self.file_path = file_path
        self.tree: Optional[ast.AST] = None
        self.strategies = {
            AnalysisType.SECURITY: SecurityAnalysisStrategy(),
            AnalysisType.QUALITY: QualityAnalysisStrategy(),
            AnalysisType.PERFORMANCE: PerformanceAnalysisStrategy(),
        }

    # Parse code into AST with error handling
    def _parse_code(self) -> ast.AST:
        """Parse code into AST with error handling"""
        try:
            return ast.parse(self.code)
        except SyntaxError as e:
            raise ASTParseError(f"Syntax error at line {e.lineno}: {e.msg}") from e
        except MemoryError:
            raise ASTParseError("File too large for AST parsing")
        except Exception as e:
            raise ASTParseError(f"AST parsing failed: {str(e)}") from e

    @lru_cache(maxsize=128)
    def _get_ast_hash(self) -> str:
        """Get hash of AST structure for caching"""
        if self.tree is None:
            self.tree = self._parse_code()
        return hashlib.md5(ast.dump(self.tree).encode()).hexdigest()

    # Calculate comprehensive code metrics
    def calculate_metrics(self) -> CodeMetrics:
        """Calculate comprehensive code metrics"""
        if self.tree is None:
            self.tree = self._parse_code()

        metrics = CodeMetrics()
        lines = self.code.splitlines()

        # Basic line metrics
        metrics.lines_of_code = len(lines)
        metrics.blank_lines = len([line for line in lines if not line.strip()])
        metrics.comment_lines = len(
            [line for line in lines if line.strip().startswith("#")]
        )
        metrics.logical_lines = (
            metrics.lines_of_code - metrics.blank_lines - metrics.comment_lines
        )

        # AST-based metrics
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics.function_count += 1
                # Calculate complexity for this function
                complexity = self._calculate_function_complexity(node)
                metrics.cyclomatic_complexity = max(
                    metrics.cyclomatic_complexity, complexity
                )
            elif isinstance(node, ast.ClassDef):
                metrics.class_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics.import_count += 1

        # Calculate maintainability index (simplified version)
        if metrics.logical_lines > 0:
            metrics.maintainability_index = max(
                0,
                171
                - 5.2
                * (
                    metrics.cyclomatic_complexity / metrics.function_count
                    if metrics.function_count > 0
                    else 1
                )
                - 0.23 * metrics.cyclomatic_complexity
                - 16.2 * (metrics.logical_lines / 1000),
            )

        return metrics

    # Calculate cyclomatic complexity for a function
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity

        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    # Perform code analysis with specified type
    def analyze(
        self,
        analysis_type: Union[AnalysisType, str],
        context: Optional[Dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Perform code analysis with specified type"""
        import time

        start_time = time.time()

        try:
            if isinstance(analysis_type, str):
                analysis_type = AnalysisType(analysis_type)

            if self.tree is None:
                self.tree = self._parse_code()

            result = AnalysisResult(
                file_path=self.file_path, ast_hash=self._get_ast_hash()
            )

            # Calculate metrics
            result.metrics = self.calculate_metrics()

            # Execute analysis strategies
            if analysis_type == AnalysisType.COMPREHENSIVE:
                # Run all strategies
                all_issues = []
                all_suggestions = []

                for strategy_type, strategy in self.strategies.items():
                    strategy_result = strategy.execute(
                        self.tree, self.code, context or {}
                    )
                    all_issues.extend(strategy_result.get("issues", []))
                    all_suggestions.extend(strategy_result.get("suggestions", []))

                result.issues = all_issues
                result.suggestions = all_suggestions
                result.security_score = self._calculate_overall_score(
                    all_issues, "security"
                )
                result.quality_score = self._calculate_overall_score(
                    all_issues, "quality"
                )
                result.performance_score = self._calculate_overall_score(
                    all_issues, "performance"
                )

            else:
                # Run specific strategy
                if analysis_type not in self.strategies:
                    raise AnalysisTypeError(
                        f"Unsupported analysis type: {analysis_type}"
                    )

                strategy = self.strategies[analysis_type]
                strategy_result = strategy.execute(self.tree, self.code, context or {})
                result.issues = strategy_result.get("issues", [])
                result.suggestions = strategy_result.get("suggestions", [])

                if analysis_type == AnalysisType.SECURITY:
                    result.security_score = strategy_result.get("security_score", 100.0)
                elif analysis_type == AnalysisType.QUALITY:
                    result.quality_score = strategy_result.get("quality_score", 100.0)
                elif analysis_type == AnalysisType.PERFORMANCE:
                    result.performance_score = strategy_result.get(
                        "performance_score", 100.0
                    )

            result.analysis_time = time.time() - start_time
            return result

        except Exception as e:
            return AnalysisResult(
                file_path=self.file_path,
                error=str(e),
                analysis_time=time.time() - start_time,
            )

    # Calculate score for a specific category of issues
    def _calculate_overall_score(self, issues: List[CodeIssue], category: str) -> float:
        """Calculate score for a specific category of issues"""
        category_issues = [issue for issue in issues if issue.type == category]
        if not category_issues:
            return 100.0

        score = 100.0
        for issue in category_issues:
            if issue.severity == Severity.CRITICAL:
                score -= 25
            elif issue.severity == Severity.HIGH:
                score -= 15
            elif issue.severity == Severity.MEDIUM:
                score -= 10
            else:
                score -= 5

        return max(0.0, score)


# Analyze code content with specified analysis type
def analyze_code(
    code: str,
    analysis_type: Union[AnalysisType, str] = AnalysisType.COMPREHENSIVE,
    file_path: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> AnalysisResult:
    """
    Analyze code content with specified analysis type

    Args:
        code: Source code to analyze
        analysis_type: Type of analysis to perform
        file_path: Optional file path for context
        context: Optional additional context

    Returns:
        AnalysisResult with metrics, issues, and suggestions

    Example:
        >>> result = analyze_code("def hello(): print('world')", AnalysisType.QUALITY)
        >>> print(f"Quality score: {result.quality_score}")
        >>> for issue in result.issues:
        ...     print(f"{issue.severity.value}: {issue.message}")
    """
    analyzer = CodeAnalyzer(code, file_path)
    return analyzer.analyze(analysis_type, context)


# Detect programming language from code content or file extension
def detect_language(code: str, file_path: Optional[str] = None) -> str:
    """
    Detect programming language from code content or file extension

    Args:
        code: Source code content
        file_path: Optional file path with extension

    Returns:
        Detected language name
    """
    if file_path:
        extension = Path(file_path).suffix.lower()
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
        }
        if extension in extension_map:
            return extension_map[extension]

    # Try to detect from code patterns
    if "def " in code or "import " in code or "from " in code:
        return "python"
    elif "function " in code or "var " in code or "let " in code:
        return "javascript"
    elif "public class" in code or "import java" in code:
        return "java"

    return "unknown"


# Export public API
__all__ = [
    "CodeAnalyzer",
    "analyze_code",
    "detect_language",
    "AnalysisType",
    "AnalysisResult",
    "CodeIssue",
    "CodeMetrics",
    "Severity",
    "CodeAnalysisError",
    "ASTParseError",
    "AnalysisTypeError",
]
