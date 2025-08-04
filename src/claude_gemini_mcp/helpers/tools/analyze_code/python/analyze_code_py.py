#!/usr/bin/env python3
"""
Python Code Analysis Module

This module provides Python-specific code analysis capabilities using AST parsing
and strategic analysis patterns. Migrated from the original analyze_code.py to fit
the polyglot architecture while preserving all existing functionality.

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-04
Architecture: Language-Specific Analyzer implementing LanguageAnalyzer interface
"""

import ast
import logging
import re
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..base import (
    AnalysisResult,
    AnalysisType,
    BaseAnalysisStrategy,
    CodeIssue,
    CodeMetrics,
    LanguageAnalyzer,
    ParseError,
    Severity,
    SupportedLanguage
)

# Configure logging
logger = logging.getLogger(__name__)


class PythonSecurityStrategy(BaseAnalysisStrategy):
    """Python-specific security vulnerability detection strategy"""

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

    def __init__(self):
        super().__init__("python")

    def execute(self, tree: ast.AST, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python security analysis"""
        visitor = PythonSecurityVisitor(self)
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

    def _check_hardcoded_secrets(self, code: str):
        """Check for hardcoded secrets in code"""
        patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password detected"),
            (r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded API key detected"),
            (r'secret\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded secret detected"),
            (r'token\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded token detected"),
        ]

        for line_num, line in enumerate(code.splitlines(), 1):
            for pattern, message in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.add_issue(
                        "security",
                        message,
                        line_num,
                        severity=Severity.HIGH,
                        suggestion="Use environment variables or secure key management",
                        rule_id="hardcoded_secrets"
                    )

    def _check_sql_injection_patterns(self, tree: ast.AST):
        """Check for potential SQL injection vulnerabilities"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if self._is_sql_context(node):
                    for arg in node.args:
                        if isinstance(arg, (ast.BinOp, ast.JoinedStr)):
                            self.add_issue(
                                "security",
                                "Potential SQL injection vulnerability",
                                getattr(node, 'lineno', 0),
                                getattr(node, 'col_offset', 0),
                                Severity.HIGH,
                                "Use parameterized queries instead of string formatting",
                                "sql_injection"
                            )

    def _check_command_injection(self, tree: ast.AST):
        """Check for command injection vulnerabilities"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in [
                    "system", "popen", "call", "run"
                ]:
                    for arg in node.args:
                        if isinstance(arg, (ast.BinOp, ast.JoinedStr)):
                            self.add_issue(
                                "security",
                                "Potential command injection vulnerability",
                                getattr(node, 'lineno', 0),
                                getattr(node, 'col_offset', 0),
                                Severity.HIGH,
                                "Avoid shell injection by using subprocess with list arguments",
                                "command_injection"
                            )

    def _is_sql_context(self, node: ast.Call) -> bool:
        """Check if a function call appears to be SQL-related"""
        if isinstance(node.func, ast.Attribute):
            sql_methods = ["execute", "query", "select", "insert", "update", "delete"]
            return node.func.attr.lower() in sql_methods
        return False

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


class PythonQualityStrategy(BaseAnalysisStrategy):
    """Python-specific code quality assessment strategy"""

    def __init__(self):
        super().__init__("python")

    def execute(self, tree: ast.AST, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python quality analysis"""
        visitor = PythonQualityVisitor(self)
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

    def _check_naming_conventions(self, tree: ast.AST):
        """Check Python naming conventions (PEP 8)"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r"^[a-z_][a-z0-9_]*$", node.name):
                    self.add_issue(
                        "quality",
                        f"Function '{node.name}' doesn't follow snake_case convention",
                        getattr(node, 'lineno', 0),
                        getattr(node, 'col_offset', 0),
                        Severity.LOW,
                        "Use snake_case for function names",
                        "naming_convention"
                    )
            elif isinstance(node, ast.ClassDef):
                if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                    self.add_issue(
                        "quality",
                        f"Class '{node.name}' doesn't follow PascalCase convention",
                        getattr(node, 'lineno', 0),
                        getattr(node, 'col_offset', 0),
                        Severity.LOW,
                        "Use PascalCase for class names",
                        "naming_convention"
                    )

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
                        "quality",
                        f"Missing docstring for {type(node).__name__.lower()} '{node.name}'",
                        getattr(node, 'lineno', 0),
                        getattr(node, 'col_offset', 0),
                        Severity.MEDIUM,
                        "Add docstring to document purpose and parameters",
                        "missing_docstring"
                    )

    def _check_complexity(self, tree: ast.AST):
        """Check for overly complex functions"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    self.add_issue(
                        "quality",
                        f"Function '{node.name}' has high cyclomatic complexity ({complexity})",
                        getattr(node, 'lineno', 0),
                        getattr(node, 'col_offset', 0),
                        Severity.HIGH,
                        "Consider breaking into smaller functions",
                        "high_complexity"
                    )

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


class PythonPerformanceStrategy(BaseAnalysisStrategy):
    """Python-specific performance analysis strategy"""

    def __init__(self):
        super().__init__("python")

    def execute(self, tree: ast.AST, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python performance analysis"""
        visitor = PythonPerformanceVisitor(self)
        visitor.visit(tree)

        # Additional performance checks
        self._check_algorithm_complexity(tree)
        self._check_inefficient_patterns(tree)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "performance_score": self._calculate_performance_score(),
        }

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
                        getattr(node, 'lineno', 0),
                        getattr(node, 'col_offset', 0),
                        Severity.MEDIUM,
                        "Consider optimizing algorithm complexity",
                        "nested_loops"
                    )

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
                            getattr(child, 'lineno', 0),
                            getattr(child, 'col_offset', 0),
                            Severity.LOW,
                            "Consider using join() or list comprehension",
                            "inefficient_string_concat"
                        )

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


# AST Visitors for each strategy
class PythonSecurityVisitor(ast.NodeVisitor):
    """AST visitor for Python security analysis"""

    def __init__(self, strategy: PythonSecurityStrategy):
        self.strategy = strategy

    def visit_Call(self, node):
        """Visit function calls for security issues"""
        if isinstance(node.func, ast.Name):
            if node.func.id in PythonSecurityStrategy.DANGEROUS_FUNCTIONS:
                self.strategy.add_issue(
                    "security",
                    f"Use of dangerous function '{node.func.id}'",
                    getattr(node, 'lineno', 0),
                    getattr(node, 'col_offset', 0),
                    Severity.HIGH,
                    f"Avoid using {node.func.id} with untrusted input",
                    f"dangerous_function_{node.func.id}"
                )

        self.generic_visit(node)

    def visit_Import(self, node):
        """Visit imports for dangerous modules"""
        for alias in node.names:
            if alias.name in PythonSecurityStrategy.DANGEROUS_MODULES:
                self.strategy.add_issue(
                    "security",
                    f"Import of potentially dangerous module '{alias.name}'",
                    getattr(node, 'lineno', 0),
                    getattr(node, 'col_offset', 0),
                    Severity.MEDIUM,
                    f"Ensure secure usage of {alias.name} module",
                    f"dangerous_import_{alias.name}"
                )

        self.generic_visit(node)


class PythonQualityVisitor(ast.NodeVisitor):
    """AST visitor for Python quality analysis"""

    def __init__(self, strategy: PythonQualityStrategy):
        self.strategy = strategy

    def visit_FunctionDef(self, node):
        """Visit function definitions for quality issues"""
        # Check function length
        if len(node.body) > 50:
            self.strategy.add_issue(
                "quality",
                f"Function '{node.name}' is too long ({len(node.body)} statements)",
                getattr(node, 'lineno', 0),
                getattr(node, 'col_offset', 0),
                Severity.MEDIUM,
                "Consider breaking into smaller functions",
                "long_function"
            )

        # Check parameter count
        if len(node.args.args) > 5:
            self.strategy.add_issue(
                "quality",
                f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                getattr(node, 'lineno', 0),
                getattr(node, 'col_offset', 0),
                Severity.MEDIUM,
                "Consider using a configuration object or reducing parameters",
                "too_many_params"
            )

        self.generic_visit(node)


class PythonPerformanceVisitor(ast.NodeVisitor):
    """AST visitor for Python performance analysis"""

    def __init__(self, strategy: PythonPerformanceStrategy):
        self.strategy = strategy

    def visit_ListComp(self, node):
        """Visit list comprehensions for performance issues"""
        # Check for complex operations in list comprehensions
        for generator in node.generators:
            if len(generator.ifs) > 2:
                self.strategy.add_issue(
                    "performance",
                    "Complex list comprehension with multiple conditions",
                    getattr(node, 'lineno', 0),
                    getattr(node, 'col_offset', 0),
                    Severity.LOW,
                    "Consider using filter() or breaking into multiple steps",
                    "complex_list_comp"
                )

        self.generic_visit(node)


class PythonAnalyzer(LanguageAnalyzer):
    """Main Python code analyzer implementing the LanguageAnalyzer interface"""

    def __init__(self):
        super().__init__()
        self.strategies = {
            AnalysisType.SECURITY: PythonSecurityStrategy(),
            AnalysisType.QUALITY: PythonQualityStrategy(),
            AnalysisType.PERFORMANCE: PythonPerformanceStrategy(),
        }

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported Python file extensions"""
        return ['.py', '.pyx', '.pyi']

    def get_language_name(self) -> str:
        """Return the language name this analyzer handles"""
        return "python"

    def can_analyze(self, code: str, file_path: Optional[str] = None) -> bool:
        """Determine if this analyzer can handle the given code"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
        except Exception:
            return False

    def analyze(self,
               code: str,
               analysis_type: Union[AnalysisType, str],
               file_path: Optional[str] = None,
               context: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """Perform Python-specific code analysis"""
        start_time = time.time()

        try:
            # Convert string analysis type to enum
            if isinstance(analysis_type, str):
                analysis_type = AnalysisType(analysis_type)

            # Parse Python code into AST
            tree = self._parse_code(code)

            # Create result object
            result = AnalysisResult(
                file_path=file_path,
                language="python",
                ast_hash=self.calculate_ast_hash(tree)
            )

            # Calculate metrics
            result.metrics = self._calculate_metrics(code, tree)

            # Execute analysis strategies
            if analysis_type == AnalysisType.COMPREHENSIVE:
                # Run all strategies
                all_issues = []
                all_suggestions = []

                for strategy_type, strategy in self.strategies.items():
                    strategy_result = strategy.execute(tree, code, context or {})
                    all_issues.extend(strategy_result.get("issues", []))
                    all_suggestions.extend(strategy_result.get("suggestions", []))

                result.issues = all_issues
                result.suggestions = all_suggestions

                # Calculate scores
                scores = self._calculate_scores(all_issues)
                result.security_score = scores["security_score"]
                result.quality_score = scores["quality_score"]
                result.performance_score = scores["performance_score"]

            else:
                # Run specific strategy
                if analysis_type not in self.strategies:
                    raise ValueError(f"Unsupported analysis type: {analysis_type}")

                strategy = self.strategies[analysis_type]
                strategy_result = strategy.execute(tree, code, context or {})
                result.issues = strategy_result.get("issues", [])
                result.suggestions = strategy_result.get("suggestions", [])

                # Set specific score
                if analysis_type == AnalysisType.SECURITY:
                    result.security_score = strategy_result.get("security_score", 100.0)
                elif analysis_type == AnalysisType.QUALITY:
                    result.quality_score = strategy_result.get("quality_score", 100.0)
                elif analysis_type == AnalysisType.PERFORMANCE:
                    result.performance_score = strategy_result.get("performance_score", 100.0)

            result.analysis_time = time.time() - start_time
            return result

        except Exception as e:
            return AnalysisResult(
                file_path=file_path,
                language="python",
                error=str(e),
                analysis_time=time.time() - start_time
            )

    def _parse_code(self, code: str) -> ast.AST:
        """Parse Python code into AST with error handling"""
        try:
            return ast.parse(code)
        except SyntaxError as e:
            raise ParseError(f"Syntax error at line {e.lineno}: {e.msg}", "python") from e
        except MemoryError:
            raise ParseError("File too large for AST parsing", "python")
        except Exception as e:
            raise ParseError(f"AST parsing failed: {str(e)}", "python") from e

    def _calculate_metrics(self, code: str, tree: ast.AST) -> CodeMetrics:
        """Calculate comprehensive code metrics for Python"""
        metrics = CodeMetrics()
        lines = code.splitlines()

        # Basic line metrics
        metrics.lines_of_code = len(lines)
        metrics.blank_lines = len([line for line in lines if not line.strip()])
        metrics.comment_lines = len([line for line in lines if line.strip().startswith("#")])
        metrics.logical_lines = metrics.lines_of_code - metrics.blank_lines - metrics.comment_lines

        # AST-based metrics
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics.function_count += 1
                # Calculate complexity for this function
                complexity = self._calculate_function_complexity(node)
                metrics.cyclomatic_complexity = max(metrics.cyclomatic_complexity, complexity)
            elif isinstance(node, ast.ClassDef):
                metrics.class_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics.import_count += 1

        # Calculate maintainability index (simplified version)
        if metrics.logical_lines > 0:
            metrics.maintainability_index = max(
                0,
                171
                - 5.2 * (metrics.cyclomatic_complexity / metrics.function_count if metrics.function_count > 0 else 1)
                - 0.23 * metrics.cyclomatic_complexity
                - 16.2 * (metrics.logical_lines / 1000),
            )

        return metrics

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


# Utility functions for backward compatibility
def analyze_code(
    code: str,
    analysis_type: Union[AnalysisType, str] = AnalysisType.COMPREHENSIVE,
    file_path: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> AnalysisResult:
    """
    Analyze Python code using the Python analyzer

    This function provides backward compatibility with the original analyze_code function.

    Args:
        code: Python source code to analyze
        analysis_type: Type of analysis to perform
        file_path: Optional file path for context
        context: Optional additional context

    Returns:
        AnalysisResult with metrics, issues, and suggestions
    """
    analyzer = PythonAnalyzer()
    return analyzer.analyze(code, analysis_type, file_path, context)


# Export public API
__all__ = [
    'PythonAnalyzer',
    'analyze_code',  # For backward compatibility
    'PythonSecurityStrategy',
    'PythonQualityStrategy',
    'PythonPerformanceStrategy'
]
