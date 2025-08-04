#!/usr/bin/env python3
"""
TypeScript Code Analysis Module

This module provides TypeScript-specific code analysis capabilities.
It attempts to use TypeScript compiler API or falls back to pattern-based analysis
when TypeScript dependencies are not available.

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-04
Architecture: Language-Specific Analyzer implementing LanguageAnalyzer interface
"""

import json
import logging
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..base import (
    AnalysisResult,
    AnalysisType,
    BaseAnalysisStrategy,
    CodeIssue,
    CodeMetrics,
    DependencyMissingError,
    LanguageAnalyzer,
    ParseError,
    Severity,
    SupportedLanguage
)

# Configure logging
logger = logging.getLogger(__name__)


class TypeScriptSecurityStrategy(BaseAnalysisStrategy):
    """TypeScript-specific security vulnerability detection strategy"""

    DANGEROUS_PATTERNS = [
        (r'eval\s*\(', "Use of eval() function", Severity.HIGH),
        (r'innerHTML\s*=', "Direct innerHTML assignment", Severity.MEDIUM),
        (r'document\.write\s*\(', "Use of document.write()", Severity.MEDIUM),
        (r'window\[.*\]', "Dynamic window property access", Severity.LOW),
        (r'dangerouslySetInnerHTML', "React dangerouslySetInnerHTML usage", Severity.MEDIUM),
        (r'any\s+', "Use of 'any' type weakens type safety", Severity.LOW),
        (r'@ts-ignore', "TypeScript error suppression", Severity.LOW),
        (r'process\.env\[.*\]', "Dynamic environment variable access", Severity.LOW),
    ]

    def __init__(self):
        super().__init__("typescript")

    def execute(self, parsed_data: Any, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute TypeScript security analysis"""
        # Pattern-based analysis for now
        self._check_security_patterns(code)
        self._check_type_safety_issues(code)
        self._check_external_dependencies(code)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "security_score": self._calculate_security_score(),
        }

    def _check_security_patterns(self, code: str):
        """Check for common TypeScript security patterns"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            for pattern, message, severity in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    self.add_issue(
                        "security",
                        message,
                        line_num,
                        severity=severity,
                        suggestion=self._get_suggestion_for_pattern(pattern),
                        rule_id=f"ts_security_{pattern[:10]}"
                    )

    def _check_type_safety_issues(self, code: str):
        """Check for type safety violations"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for excessive any usage
            any_count = len(re.findall(r'\bany\b', line))
            if any_count > 2:
                self.add_issue(
                    "security",
                    f"Excessive use of 'any' type ({any_count} occurrences) weakens type safety",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Use specific types or union types instead of 'any'",
                    rule_id="ts_excessive_any"
                )

            # Check for type assertions that might be unsafe
            if re.search(r'as\s+any\b', line):
                self.add_issue(
                    "security",
                    "Unsafe type assertion to 'any'",
                    line_num,
                    severity=Severity.HIGH,
                    suggestion="Use proper type guards or specific type assertions",
                    rule_id="ts_unsafe_assertion"
                )

    def _check_external_dependencies(self, code: str):
        """Check for potentially unsafe external dependencies"""
        # Look for dynamic imports or requires
        dynamic_imports = re.finditer(r'import\s*\(.*\)', code, re.MULTILINE)
        for match in dynamic_imports:
            line_num = code[:match.start()].count('\n') + 1
            self.add_issue(
                "security",
                "Dynamic import detected - ensure imported modules are trusted",
                line_num,
                severity=Severity.MEDIUM,
                suggestion="Validate dynamic imports and use static imports when possible",
                rule_id="ts_dynamic_import"
            )

    def _get_suggestion_for_pattern(self, pattern: str) -> str:
        """Get security suggestion for specific pattern"""
        suggestions = {
            r'eval\s*\(': "Avoid eval() - use JSON.parse() or specific parsers",
            r'innerHTML\s*=': "Use textContent or createElement for safety",
            r'document\.write\s*\(': "Use DOM manipulation methods instead",
            r'any\s+': "Use specific types or union types for better type safety",
            r'@ts-ignore': "Address the TypeScript error instead of ignoring it",
        }

        for pat, suggestion in suggestions.items():
            if pat in pattern:
                return suggestion

        return "Review for potential security implications"

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


class TypeScriptQualityStrategy(BaseAnalysisStrategy):
    """TypeScript-specific code quality assessment strategy"""

    def __init__(self):
        super().__init__("typescript")

    def execute(self, parsed_data: Any, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute TypeScript quality analysis"""
        self._check_naming_conventions(code)
        self._check_interface_design(code)
        self._check_function_complexity(code)
        self._check_import_organization(code)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "quality_score": self._calculate_quality_score(),
        }

    def _check_naming_conventions(self, code: str):
        """Check TypeScript naming conventions"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check interface naming (should start with uppercase)
            interface_matches = re.finditer(r'interface\s+([a-z][a-zA-Z0-9]*)', line)
            for match in interface_matches:
                interface_name = match.group(1)
                self.add_issue(
                    "quality",
                    f"Interface '{interface_name}' should start with uppercase letter",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Use PascalCase for interface names",
                    rule_id="ts_interface_naming"
                )

            # Check function naming (should be camelCase)
            func_matches = re.finditer(r'function\s+([A-Z][a-zA-Z0-9]*)', line)
            for match in func_matches:
                func_name = match.group(1)
                self.add_issue(
                    "quality",
                    f"Function '{func_name}' should use camelCase",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Use camelCase for function names",
                    rule_id="ts_function_naming"
                )

    def _check_interface_design(self, code: str):
        """Check interface design quality"""
        # Find interfaces and analyze their structure
        interface_pattern = r'interface\s+(\w+)\s*\{([^}]+)\}'
        interfaces = re.finditer(interface_pattern, code, re.DOTALL)

        for match in interfaces:
            interface_name = match.group(1)
            interface_body = match.group(2)
            line_num = code[:match.start()].count('\n') + 1

            # Count properties
            properties = re.findall(r'^\s*(\w+)\s*[?:]', interface_body, re.MULTILINE)

            if len(properties) > 10:
                self.add_issue(
                    "quality",
                    f"Interface '{interface_name}' has too many properties ({len(properties)})",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Consider breaking large interfaces into smaller, focused ones",
                    rule_id="ts_large_interface"
                )

            # Check for optional properties pattern
            optional_count = len(re.findall(r'\w+\?:', interface_body))
            if optional_count > len(properties) * 0.7:  # More than 70% optional
                self.add_issue(
                    "quality",
                    f"Interface '{interface_name}' has mostly optional properties",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Consider if this interface is too permissive",
                    rule_id="ts_mostly_optional"
                )

    def _check_function_complexity(self, code: str):
        """Check function complexity"""
        # Simple complexity check based on nested structures
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Count nested structures (simple heuristic)
            nesting_indicators = ['if', 'for', 'while', 'switch', 'try']
            nesting_count = sum(1 for indicator in nesting_indicators if indicator in line.lower())

            if nesting_count > 3:
                self.add_issue(
                    "quality",
                    f"High complexity detected (multiple control structures)",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Consider breaking complex functions into smaller ones",
                    rule_id="ts_high_complexity"
                )

    def _check_import_organization(self, code: str):
        """Check import statement organization"""
        lines = code.splitlines()
        import_lines = []

        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('import'):
                import_lines.append((line_num, line.strip()))

        if len(import_lines) > 1:
            # Check if imports are grouped (external vs internal)
            external_imports = []
            internal_imports = []

            for line_num, import_line in import_lines:
                if re.search(r"from\s+['\"]\.\.?/", import_line):
                    internal_imports.append(line_num)
                else:
                    external_imports.append(line_num)

            # If we have both types, check if they're grouped
            if external_imports and internal_imports:
                if max(external_imports) > min(internal_imports):
                    # External imports should come before internal ones
                    self.add_issue(
                        "quality",
                        "Import statements are not properly organized",
                        min(import_lines)[0],
                        severity=Severity.LOW,
                        suggestion="Group external imports before internal imports",
                        rule_id="ts_import_organization"
                    )

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


class TypeScriptPerformanceStrategy(BaseAnalysisStrategy):
    """TypeScript-specific performance analysis strategy"""

    def __init__(self):
        super().__init__("typescript")

    def execute(self, parsed_data: Any, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute TypeScript performance analysis"""
        self._check_compilation_performance(code)
        self._check_runtime_patterns(code)
        self._check_memory_patterns(code)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "performance_score": self._calculate_performance_score(),
        }

    def _check_compilation_performance(self, code: str):
        """Check for patterns that may slow TypeScript compilation"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for complex type computations
            if re.search(r'keyof\s+typeof', line):
                self.add_issue(
                    "performance",
                    "Complex type computation detected",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Consider simplifying type computations for better compilation performance",
                    rule_id="ts_complex_types"
                )

            # Check for excessive conditional types
            conditional_types = len(re.findall(r'\?\s*:', line))
            if conditional_types > 3:
                self.add_issue(
                    "performance",
                    f"Multiple conditional types in single line ({conditional_types})",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Break complex conditional types into simpler ones",
                    rule_id="ts_conditional_types"
                )

    def _check_runtime_patterns(self, code: str):
        """Check for runtime performance issues"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for inefficient array operations
            if re.search(r'\.filter\(.*\)\.map\(', line):
                self.add_issue(
                    "performance",
                    "Chained filter().map() can be optimized",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Consider using reduce() or a single loop for better performance",
                    rule_id="ts_inefficient_chaining"
                )

            # Check for potential memory leaks
            if re.search(r'setInterval|setTimeout', line) and 'clear' not in line.lower():
                self.add_issue(
                    "performance",
                    "Timer without cleanup detected",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Ensure timers are cleared to prevent memory leaks",
                    rule_id="ts_timer_leak"
                )

    def _check_memory_patterns(self, code: str):
        """Check for potential memory usage issues"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for large object creation in loops
            if re.search(r'for\s*\(.*\{', line) and 'new ' in line:
                self.add_issue(
                    "performance",
                    "Object creation inside loop detected",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Move object creation outside loop when possible",
                    rule_id="ts_object_in_loop"
                )

            # Check for potential closure memory issues
            if re.search(r'function.*return\s+function', line):
                self.add_issue(
                    "performance",
                    "Nested function creation - check for closure memory usage",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Be mindful of variables captured in closures",
                    rule_id="ts_closure_memory"
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


class TypeScriptAnalyzer(LanguageAnalyzer):
    """Main TypeScript code analyzer implementing the LanguageAnalyzer interface"""

    def __init__(self):
        super().__init__()
        self.strategies = {
            AnalysisType.SECURITY: TypeScriptSecurityStrategy(),
            AnalysisType.QUALITY: TypeScriptQualityStrategy(),
            AnalysisType.PERFORMANCE: TypeScriptPerformanceStrategy(),
        }
        self._has_typescript = self._check_typescript_availability()

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported TypeScript file extensions"""
        return ['.ts', '.tsx']

    def get_language_name(self) -> str:
        """Return the language name this analyzer handles"""
        return "typescript"

    def can_analyze(self, code: str, file_path: Optional[str] = None) -> bool:
        """Determine if this analyzer can handle the given code"""
        # Check for TypeScript-specific syntax
        ts_patterns = [
            r'interface\s+\w+',
            r'type\s+\w+\s*=',
            r':\s*\w+(\[\]|\<.*\>)?',
            r'export\s+(interface|type)',
            r'declare\s+(const|let|var|function|class)',
            r'namespace\s+\w+'
        ]

        # If file extension is TypeScript, give it high confidence
        if file_path and Path(file_path).suffix.lower() in ['.ts', '.tsx']:
            return True

        # Check for TypeScript patterns
        for pattern in ts_patterns:
            if re.search(pattern, code):
                return True

        return False

    def analyze(self,
               code: str,
               analysis_type: Union[AnalysisType, str],
               file_path: Optional[str] = None,
               context: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """Perform TypeScript-specific code analysis"""
        start_time = time.time()

        try:
            # Convert string analysis type to enum
            if isinstance(analysis_type, str):
                analysis_type = AnalysisType(analysis_type)

            # Parse TypeScript code (fallback to pattern-based analysis)
            parsed_data = self._parse_code(code, file_path)

            # Create result object
            result = AnalysisResult(
                file_path=file_path,
                language="typescript",
                ast_hash=self.calculate_ast_hash(code)  # Use code since we don't have proper AST
            )

            # Calculate metrics
            result.metrics = self._calculate_metrics(code, parsed_data)

            # Execute analysis strategies
            if analysis_type == AnalysisType.COMPREHENSIVE:
                # Run all strategies
                all_issues = []
                all_suggestions = []

                for strategy_type, strategy in self.strategies.items():
                    strategy_result = strategy.execute(parsed_data, code, context or {})
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
                strategy_result = strategy.execute(parsed_data, code, context or {})
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

            # Add TypeScript-specific metadata
            result.language_specific = {
                'typescript_available': self._has_typescript,
                'analysis_method': 'typescript_compiler' if self._has_typescript else 'pattern_based'
            }

            return result

        except Exception as e:
            return AnalysisResult(
                file_path=file_path,
                language="typescript",
                error=str(e),
                analysis_time=time.time() - start_time
            )

    def _check_typescript_availability(self) -> bool:
        """Check if TypeScript compiler is available"""
        try:
            result = subprocess.run(['tsc', '--version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _parse_code(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Parse TypeScript code (fallback to basic analysis if TS not available)"""
        if self._has_typescript:
            return self._parse_with_typescript(code, file_path)
        else:
            return self._parse_with_patterns(code)

    def _parse_with_typescript(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Parse using TypeScript compiler (if available)"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            # Run TypeScript compiler for syntax checking
            result = subprocess.run(
                ['tsc', '--noEmit', '--strict', tmp_path],
                capture_output=True, text=True, timeout=10
            )

            # Clean up
            Path(tmp_path).unlink(missing_ok=True)

            return {
                'syntax_errors': result.stderr if result.returncode != 0 else None,
                'compilation_success': result.returncode == 0,
                'compiler_output': result.stderr
            }

        except Exception as e:
            logger.warning(f"TypeScript parsing failed: {e}")
            return self._parse_with_patterns(code)

    def _parse_with_patterns(self, code: str) -> Dict[str, Any]:
        """Parse using pattern-based analysis (fallback)"""
        return {
            'syntax_errors': None,
            'compilation_success': True,  # Assume success for pattern-based
            'analysis_method': 'pattern_based'
        }

    def _calculate_metrics(self, code: str, parsed_data: Dict[str, Any]) -> CodeMetrics:
        """Calculate comprehensive code metrics for TypeScript"""
        metrics = CodeMetrics()
        lines = code.splitlines()

        # Basic line metrics
        metrics.lines_of_code = len(lines)
        metrics.blank_lines = len([line for line in lines if not line.strip()])
        metrics.comment_lines = len([line for line in lines if line.strip().startswith('//')])
        metrics.logical_lines = metrics.lines_of_code - metrics.blank_lines - metrics.comment_lines

        # TypeScript-specific counts
        content = code

        # Count functions (including arrow functions)
        function_patterns = [
            r'function\s+\w+',
            r'\w+\s*=\s*\([^)]*\)\s*=>',
            r'=\s*async\s*\([^)]*\)\s*=>'
        ]
        for pattern in function_patterns:
            metrics.function_count += len(re.findall(pattern, content))

        # Count interfaces and types
        metrics.class_count = len(re.findall(r'interface\s+\w+', content))
        metrics.class_count += len(re.findall(r'type\s+\w+\s*=', content))
        metrics.class_count += len(re.findall(r'class\s+\w+', content))

        # Count imports
        metrics.import_count = len(re.findall(r'^import\s+', content, re.MULTILINE))

        # Simple complexity estimation
        complexity_indicators = ['if', 'for', 'while', 'switch', 'catch', '?', '&&', '||']
        complexity_score = 0
        for indicator in complexity_indicators:
            complexity_score += len(re.findall(re.escape(indicator), content, re.IGNORECASE))

        metrics.cyclomatic_complexity = min(complexity_score, 100)  # Cap at 100

        # TypeScript-specific metrics
        metrics.language_specific = {
            'interfaces_count': len(re.findall(r'interface\s+\w+', content)),
            'type_aliases_count': len(re.findall(r'type\s+\w+\s*=', content)),
            'generic_usage_count': len(re.findall(r'<[A-Z][^>]*>', content)),
            'any_usage_count': len(re.findall(r'\bany\b', content)),
            'strict_null_checks': '!' in content,  # Simple heuristic
        }

        return metrics

    def detect_language_confidence(self, code: str, file_path: Optional[str] = None) -> float:
        """Return confidence score for TypeScript detection"""
        confidence = 0.0

        # File extension check
        if file_path:
            ext = Path(file_path).suffix.lower()
            if ext in ['.ts', '.tsx']:
                confidence += 90.0

        # TypeScript-specific patterns
        ts_patterns = [
            (r'interface\s+\w+', 20),
            (r'type\s+\w+\s*=', 15),
            (r':\s*string\b', 10),
            (r':\s*number\b', 10),
            (r':\s*boolean\b', 10),
            (r'export\s+(interface|type)', 15),
            (r'declare\s+', 15),
            (r'namespace\s+\w+', 20),
            (r'<[A-Z][^>]*>', 10),  # Generics
        ]

        for pattern, score in ts_patterns:
            if re.search(pattern, code):
                confidence += score

        # Check if it can actually be parsed (basic syntax check)
        if self.can_analyze(code, file_path):
            confidence += 20.0

        return min(confidence, 100.0)


# Export public API
__all__ = [
    'TypeScriptAnalyzer',
    'TypeScriptSecurityStrategy',
    'TypeScriptQualityStrategy',
    'TypeScriptPerformanceStrategy'
]
