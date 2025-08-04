#!/usr/bin/env python3
"""
JavaScript Code Analysis Module

This module provides JavaScript-specific code analysis capabilities.
It uses pattern-based analysis and can optionally integrate with Node.js
tools when available for enhanced parsing.

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


class JavaScriptSecurityStrategy(BaseAnalysisStrategy):
    """JavaScript-specific security vulnerability detection strategy"""

    DANGEROUS_PATTERNS = [
        (r'eval\s*\(', "Use of eval() function", Severity.HIGH),
        (r'Function\s*\(', "Use of Function constructor", Severity.HIGH),
        (r'innerHTML\s*=', "Direct innerHTML assignment (XSS risk)", Severity.HIGH),
        (r'outerHTML\s*=', "Direct outerHTML assignment", Severity.HIGH),
        (r'document\.write\s*\(', "Use of document.write()", Severity.MEDIUM),
        (r'dangerouslySetInnerHTML', "React dangerouslySetInnerHTML usage", Severity.MEDIUM),
        (r'v-html\s*=', "Vue v-html directive (XSS risk)", Severity.MEDIUM),
        (r'window\[.*\]', "Dynamic window property access", Severity.LOW),
        (r'localStorage\[.*\]', "Dynamic localStorage access", Severity.LOW),
        (r'sessionStorage\[.*\]', "Dynamic sessionStorage access", Severity.LOW),
        (r'setTimeout\s*\(\s*["\']', "setTimeout with string argument", Severity.MEDIUM),
        (r'setInterval\s*\(\s*["\']', "setInterval with string argument", Severity.MEDIUM),
        (r'postMessage\s*\(', "Cross-origin messaging - verify origin", Severity.MEDIUM),
        (r'JSON\.parse\s*\(.*\)', "JSON.parse without error handling", Severity.LOW),
    ]

    PROTOTYPE_POLLUTION_PATTERNS = [
        (r'__proto__', "Direct __proto__ manipulation", Severity.HIGH),
        (r'constructor\.prototype', "Prototype chain manipulation", Severity.MEDIUM),
        (r'Object\.setPrototypeOf', "Prototype modification", Severity.MEDIUM),
    ]

    def __init__(self):
        super().__init__("javascript")

    def execute(self, parsed_data: Any, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute JavaScript security analysis"""
        self._check_security_patterns(code)
        self._check_prototype_pollution(code)
        self._check_dom_manipulation(code)
        self._check_async_security(code)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "security_score": self._calculate_security_score(),
        }

    def _check_security_patterns(self, code: str):
        """Check for common JavaScript security patterns"""
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
                        rule_id=f"js_security_{pattern.split('\\')[0][:10]}"
                    )

    def _check_prototype_pollution(self, code: str):
        """Check for prototype pollution vulnerabilities"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            for pattern, message, severity in self.PROTOTYPE_POLLUTION_PATTERNS:
                if re.search(pattern, line):
                    self.add_issue(
                        "security",
                        message,
                        line_num,
                        severity=severity,
                        suggestion="Avoid modifying prototype chains; use Object.create() or classes",
                        rule_id="js_prototype_pollution"
                    )

    def _check_dom_manipulation(self, code: str):
        """Check for unsafe DOM manipulation patterns"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for potential XSS in DOM manipulation
            dom_patterns = [
                (r'\.setAttribute\s*\(\s*["\']on\w+["\']', "Event handler injection risk"),
                (r'\.insertAdjacentHTML\s*\(', "insertAdjacentHTML without sanitization"),
                (r'\.src\s*=\s*(?![\"\'][https?://])', "Dynamic src assignment"),
            ]

            for pattern, message in dom_patterns:
                if re.search(pattern, line):
                    self.add_issue(
                        "security",
                        message,
                        line_num,
                        severity=Severity.MEDIUM,
                        suggestion="Sanitize user input and validate sources",
                        rule_id="js_dom_manipulation"
                    )

    def _check_async_security(self, code: str):
        """Check for async/await security issues"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for unhandled promise rejections
            if 'await ' in line and 'try' not in line and 'catch' not in line:
                # Look ahead/behind for try-catch blocks (simple heuristic)
                context_lines = lines[max(0, line_num-3):min(len(lines), line_num+3)]
                has_error_handling = any('try' in l or 'catch' in l for l in context_lines)

                if not has_error_handling:
                    self.add_issue(
                        "security",
                        "Unhandled async operation - potential for unhandled rejections",
                        line_num,
                        severity=Severity.LOW,
                        suggestion="Wrap async operations in try-catch blocks",
                        rule_id="js_unhandled_async"
                    )

    def _get_suggestion_for_pattern(self, pattern: str) -> str:
        """Get security suggestion for specific pattern"""
        suggestions = {
            r'eval\s*\(': "Avoid eval() - use JSON.parse() or specific parsers",
            r'Function\s*\(': "Avoid Function constructor - use regular function declarations",
            r'innerHTML\s*=': "Use textContent or createElement for safety",
            r'document\.write\s*\(': "Use DOM manipulation methods instead",
            r'setTimeout\s*\(\s*["\']': "Pass function reference instead of string",
            r'JSON\.parse\s*\(': "Wrap JSON.parse in try-catch for safe parsing",
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


class JavaScriptQualityStrategy(BaseAnalysisStrategy):
    """JavaScript-specific code quality assessment strategy"""

    def __init__(self):
        super().__init__("javascript")

    def execute(self, parsed_data: Any, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute JavaScript quality analysis"""
        self._check_modern_js_usage(code)
        self._check_function_design(code)
        self._check_error_handling(code)
        self._check_async_patterns(code)
        self._check_variable_declarations(code)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "quality_score": self._calculate_quality_score(),
        }

    def _check_modern_js_usage(self, code: str):
        """Check for modern JavaScript best practices"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for var usage (should use let/const)
            if re.search(r'\bvar\s+\w+', line):
                self.add_issue(
                    "quality",
                    "Use 'let' or 'const' instead of 'var' for block scoping",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Replace 'var' with 'let' for mutable variables or 'const' for constants",
                    rule_id="js_var_usage"
                )

            # Check for function() vs arrow functions in appropriate contexts
            if re.search(r'\.map\s*\(\s*function\s*\(', line):
                self.add_issue(
                    "quality",
                    "Consider using arrow function for cleaner syntax",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Use arrow functions for short callback functions",
                    rule_id="js_arrow_function"
                )

            # Check for == vs === usage
            if re.search(r'[^=!]==[^=]', line) or re.search(r'!=[^=]', line):
                self.add_issue(
                    "quality",
                    "Use strict equality (=== or !==) instead of loose equality",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Use === and !== for type-safe comparisons",
                    rule_id="js_strict_equality"
                )

    def _check_function_design(self, code: str):
        """Check function design quality"""
        # Find function definitions and analyze them
        function_patterns = [
            r'function\s+(\w+)\s*\([^)]*\)\s*\{',
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{',
            r'(\w+)\s*:\s*function\s*\([^)]*\)\s*\{'
        ]

        for pattern in function_patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                func_name = match.group(1)
                line_num = code[:match.start()].count('\n') + 1

                # Simple complexity check - count braces and control structures
                func_end = self._find_function_end(code, match.start())
                func_body = code[match.start():func_end]

                complexity_score = (
                    func_body.count('{') +
                    func_body.count('if') +
                    func_body.count('for') +
                    func_body.count('while') +
                    func_body.count('switch')
                )

                if complexity_score > 15:
                    self.add_issue(
                        "quality",
                        f"Function '{func_name}' appears complex (complexity score: {complexity_score})",
                        line_num,
                        severity=Severity.MEDIUM,
                        suggestion="Consider breaking complex functions into smaller ones",
                        rule_id="js_function_complexity"
                    )

    def _check_error_handling(self, code: str):
        """Check for proper error handling patterns"""
        lines = code.splitlines()

        # Check for try-catch usage
        try_blocks = 0
        catch_blocks = 0

        for line_num, line in enumerate(lines, 1):
            if 'try' in line and '{' in line:
                try_blocks += 1
            if 'catch' in line:
                catch_blocks += 1

            # Check for Promise without catch
            if re.search(r'\.then\s*\(', line) and '.catch' not in line:
                # Look ahead to see if catch is on next lines
                next_lines = lines[line_num:line_num+3] if line_num < len(lines) else []
                has_catch = any('.catch' in l for l in next_lines)

                if not has_catch:
                    self.add_issue(
                        "quality",
                        "Promise chain without error handling",
                        line_num,
                        severity=Severity.MEDIUM,
                        suggestion="Add .catch() to handle promise rejections",
                        rule_id="js_promise_error_handling"
                    )

        # Overall error handling assessment
        if try_blocks > 0 and catch_blocks == 0:
            self.add_issue(
                "quality",
                "Try blocks without corresponding catch blocks",
                1,
                severity=Severity.HIGH,
                suggestion="Ensure all try blocks have appropriate error handling",
                rule_id="js_incomplete_error_handling"
            )

    def _check_async_patterns(self, code: str):
        """Check for proper async/await patterns"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for mixing async patterns
            if 'await' in line and '.then(' in line:
                self.add_issue(
                    "quality",
                    "Mixing async/await with Promise chains",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Use consistent async pattern (prefer async/await)",
                    rule_id="js_mixed_async_patterns"
                )

            # Check for async function without await
            if line.strip().startswith('async') and 'function' in line:
                # Simple check - look for await in nearby lines (not perfect but useful)
                func_lines = lines[line_num-1:min(line_num+20, len(lines))]
                has_await = any('await' in l for l in func_lines)

                if not has_await:
                    self.add_issue(
                        "quality",
                        "Async function without await usage",
                        line_num,
                        severity=Severity.LOW,
                        suggestion="Consider if function needs to be async",
                        rule_id="js_unnecessary_async"
                    )

    def _check_variable_declarations(self, code: str):
        """Check variable declaration patterns"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for unused variables (simple heuristic)
            const_matches = re.finditer(r'const\s+(\w+)\s*=', line)
            for match in const_matches:
                var_name = match.group(1)
                # Simple check - if variable appears only once, might be unused
                var_usage_count = code.count(var_name)
                if var_usage_count == 1:  # Only the declaration
                    self.add_issue(
                        "quality",
                        f"Variable '{var_name}' appears to be unused",
                        line_num,
                        severity=Severity.LOW,
                        suggestion="Remove unused variables or add usage",
                        rule_id="js_unused_variable"
                    )

    def _find_function_end(self, code: str, start_pos: int) -> int:
        """Find the end of a function (simple brace matching)"""
        brace_count = 0
        pos = start_pos

        while pos < len(code):
            if code[pos] == '{':
                brace_count += 1
            elif code[pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return pos + 1
            pos += 1

        return len(code)  # Fallback

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


class JavaScriptPerformanceStrategy(BaseAnalysisStrategy):
    """JavaScript-specific performance analysis strategy"""

    def __init__(self):
        super().__init__("javascript")

    def execute(self, parsed_data: Any, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute JavaScript performance analysis"""
        self._check_dom_performance(code)
        self._check_loop_performance(code)
        self._check_memory_patterns(code)
        self._check_async_performance(code)

        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "performance_score": self._calculate_performance_score(),
        }

    def _check_dom_performance(self, code: str):
        """Check for DOM performance issues"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for excessive DOM queries
            dom_queries = [
                'getElementById', 'getElementsByClassName', 'getElementsByTagName',
                'querySelector', 'querySelectorAll'
            ]

            query_count = sum(1 for query in dom_queries if query in line)
            if query_count > 2:
                self.add_issue(
                    "performance",
                    f"Multiple DOM queries in single line ({query_count})",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Cache DOM elements to avoid repeated queries",
                    rule_id="js_dom_queries"
                )

            # Check for style manipulation in loops
            if ('for(' in line or 'while(' in line) and '.style.' in line:
                self.add_issue(
                    "performance",
                    "Style manipulation inside loop",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Use CSS classes or batch style changes",
                    rule_id="js_style_in_loop"
                )

    def _check_loop_performance(self, code: str):
        """Check for loop performance issues"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for array methods in nested loops
            if ('for(' in line or '.forEach(' in line):
                # Look for array methods in the same or next few lines
                context_lines = lines[line_num-1:min(line_num+5, len(lines))]
                context = ' '.join(context_lines)

                expensive_operations = ['.filter(.', '.map(.', '.find(.', '.reduce(.']
                expensive_count = sum(1 for op in expensive_operations if op in context)

                if expensive_count > 0:
                    self.add_issue(
                        "performance",
                        "Array operations inside loops can be expensive",
                        line_num,
                        severity=Severity.MEDIUM,
                        suggestion="Consider optimizing nested array operations",
                        rule_id="js_nested_array_ops"
                    )

            # Check for inefficient chaining
            chain_pattern = r'\.filter\(.*\)\.map\(.*\)\.filter\('
            if re.search(chain_pattern, line):
                self.add_issue(
                    "performance",
                    "Inefficient array method chaining",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Combine operations or use reduce() for better performance",
                    rule_id="js_inefficient_chaining"
                )

    def _check_memory_patterns(self, code: str):
        """Check for potential memory issues"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for potential memory leaks
            if ('setInterval(' in line or 'setTimeout(' in line) and 'clear' not in line.lower():
                self.add_issue(
                    "performance",
                    "Timer without cleanup - potential memory leak",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Clear timers to prevent memory leaks",
                    rule_id="js_timer_leak"
                )

            # Check for event listeners without cleanup
            if 'addEventListener(' in line and 'removeEventListener' not in code:
                self.add_issue(
                    "performance",
                    "Event listener without removal - potential memory leak",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Remove event listeners when no longer needed",
                    rule_id="js_event_listener_leak"
                )

            # Check for closure-heavy patterns
            if 'return function(' in line:
                self.add_issue(
                    "performance",
                    "Function closure - check for memory usage",
                    line_num,
                    severity=Severity.LOW,
                    suggestion="Be mindful of variables captured in closures",
                    rule_id="js_closure_memory"
                )

    def _check_async_performance(self, code: str):
        """Check for async performance issues"""
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for synchronous operations that could be async
            sync_operations = ['readFileSync', 'writeFileSync', 'execSync']
            for op in sync_operations:
                if op in line:
                    self.add_issue(
                        "performance",
                        f"Synchronous operation '{op}' blocks event loop",
                        line_num,
                        severity=Severity.HIGH,
                        suggestion=f"Use async version: {op.replace('Sync', '')}",
                        rule_id="js_blocking_sync"
                    )

            # Check for Promise.all opportunities
            if 'await ' in line and 'for(' in line:
                self.add_issue(
                    "performance",
                    "Sequential async operations in loop",
                    line_num,
                    severity=Severity.MEDIUM,
                    suggestion="Consider using Promise.all() for parallel execution",
                    rule_id="js_sequential_async"
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


class JavaScriptAnalyzer(LanguageAnalyzer):
    """Main JavaScript code analyzer implementing the LanguageAnalyzer interface"""

    def __init__(self):
        super().__init__()
        self.strategies = {
            AnalysisType.SECURITY: JavaScriptSecurityStrategy(),
            AnalysisType.QUALITY: JavaScriptQualityStrategy(),
            AnalysisType.PERFORMANCE: JavaScriptPerformanceStrategy(),
        }
        self._has_node = self._check_node_availability()

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported JavaScript file extensions"""
        return ['.js', '.jsx', '.mjs', '.cjs']

    def get_language_name(self) -> str:
        """Return the language name this analyzer handles"""
        return "javascript"

    def can_analyze(self, code: str, file_path: Optional[str] = None) -> bool:
        """Determine if this analyzer can handle the given code"""
        # Check for JavaScript-specific syntax
        js_patterns = [
            r'function\s+\w+\s*\(',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'import.*from\s+["\'].*["\']',
            r'module\.exports\s*=',
            r'require\s*\(',
            r'console\.(log|error|warn)',
            r'=>\s*\{',  # Arrow functions
        ]

        # If file extension is JavaScript, give it high confidence
        if file_path and Path(file_path).suffix.lower() in ['.js', '.jsx', '.mjs', '.cjs']:
            return True

        # Check for JavaScript patterns
        for pattern in js_patterns:
            if re.search(pattern, code):
                return True

        return False

    def analyze(self,
               code: str,
               analysis_type: Union[AnalysisType, str],
               file_path: Optional[str] = None,
               context: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """Perform JavaScript-specific code analysis"""
        start_time = time.time()

        try:
            # Convert string analysis type to enum
            if isinstance(analysis_type, str):
                analysis_type = AnalysisType(analysis_type)

            # Parse JavaScript code (pattern-based analysis for now)
            parsed_data = self._parse_code(code, file_path)

            # Create result object
            result = AnalysisResult(
                file_path=file_path,
                language="javascript",
                ast_hash=self.calculate_ast_hash(code)
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

            # Add JavaScript-specific metadata
            result.language_specific = {
                'node_available': self._has_node,
                'analysis_method': 'pattern_based',  # Could be enhanced with Babel parser
                'es_version_detected': self._detect_es_version(code),
                'frameworks_detected': self._detect_frameworks(code)
            }

            return result

        except Exception as e:
            return AnalysisResult(
                file_path=file_path,
                language="javascript",
                error=str(e),
                analysis_time=time.time() - start_time
            )

    def _check_node_availability(self) -> bool:
        """Check if Node.js is available"""
        try:
            result = subprocess.run(['node', '--version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _parse_code(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Parse JavaScript code (pattern-based analysis)"""
        return {
            'syntax_valid': True,  # Assume valid for pattern-based analysis
            'analysis_method': 'pattern_based',
            'parsing_time': 0.0
        }

    def _calculate_metrics(self, code: str, parsed_data: Dict[str, Any]) -> CodeMetrics:
        """Calculate comprehensive code metrics for JavaScript"""
        metrics = CodeMetrics()
        lines = code.splitlines()

        # Basic line metrics
        metrics.lines_of_code = len(lines)
        metrics.blank_lines = len([line for line in lines if not line.strip()])
        metrics.comment_lines = len([line for line in lines if line.strip().startswith('//')])
        metrics.logical_lines = metrics.lines_of_code - metrics.blank_lines - metrics.comment_lines

        # JavaScript-specific counts
        content = code

        # Count functions (including arrow functions)
        function_patterns = [
            r'function\s+\w+',
            r'const\s+\w+\s*=\s*\([^)]*\)\s*=>',
            r'let\s+\w+\s*=\s*\([^)]*\)\s*=>',
            r'\w+\s*:\s*function\s*\(',
            r'\w+\s*:\s*\([^)]*\)\s*=>'
        ]
        for pattern in function_patterns:
            metrics.function_count += len(re.findall(pattern, content))

        # Count classes
        metrics.class_count = len(re.findall(r'class\s+\w+', content))

        # Count imports/requires
        metrics.import_count = len(re.findall(r'import\s+', content, re.MULTILINE))
        metrics.import_count += len(re.findall(r'require\s*\(', content))

        # Simple complexity estimation
        complexity_indicators = ['if', 'for', 'while', 'switch', 'catch', '?', '&&', '||']
        complexity_score = 0
        for indicator in complexity_indicators:
            complexity_score += len(re.findall(re.escape(indicator), content, re.IGNORECASE))

        metrics.cyclomatic_complexity = min(complexity_score, 100)  # Cap at 100

        # JavaScript-specific metrics
        metrics.language_specific = {
            'arrow_functions_count': len(re.findall(r'=>', content)),
            'async_functions_count': len(re.findall(r'async\s+function', content)) + len(re.findall(r'=\s*async\s*\(', content)),
            'promise_usage_count': len(re.findall(r'new Promise', content)) + len(re.findall(r'\.then\(', content)),
            'callback_patterns_count': len(re.findall(r'function\s*\([^)]*\)\s*\{', content)),
            'es6_features_count': self._count_es6_features(content),
            'dom_usage_count': len(re.findall(r'document\.|window\.', content)),
        }

        return metrics

    def _count_es6_features(self, code: str) -> int:
        """Count ES6+ features in the code"""
        es6_patterns = [
            r'const\s+\w+',
            r'let\s+\w+',
            r'=>',  # Arrow functions
            r'`[^`]*`',  # Template literals
            r'\.\.\.[\w\[]',  # Spread operator
            r'class\s+\w+',
            r'import\s+.*from',
            r'export\s+(default\s+)?',
            r'for\s*\([^)]*of[^)]*\)',  # for...of loops
        ]

        count = 0
        for pattern in es6_patterns:
            count += len(re.findall(pattern, code))

        return count

    def _detect_es_version(self, code: str) -> str:
        """Detect ES version based on features used"""
        if 'async' in code or 'await' in code:
            return 'ES2017+'
        elif 'class' in code or '=>' in code:
            return 'ES6+'
        elif 'var' in code and 'function' in code:
            return 'ES5'
        else:
            return 'Unknown'

    def _detect_frameworks(self, code: str) -> List[str]:
        """Detect JavaScript frameworks/libraries in use"""
        frameworks = []

        framework_patterns = {
            'React': [r'import.*React', r'jsx', r'useState', r'useEffect'],
            'Vue': [r'new Vue', r'v-if', r'v-for', r'@click'],
            'Angular': [r'@Component', r'@Injectable', r'ngOnInit'],
            'jQuery': [r'\$\(', r'jQuery'],
            'Express': [r'express\(\)', r'app\.get\(', r'req\.', r'res\.'],
            'Lodash': [r'_\.', r'import.*lodash'],
            'Moment': [r'moment\(', r'import.*moment'],
        }

        for framework, patterns in framework_patterns.items():
            if any(re.search(pattern, code) for pattern in patterns):
                frameworks.append(framework)

        return frameworks

    def detect_language_confidence(self, code: str, file_path: Optional[str] = None) -> float:
        """Return confidence score for JavaScript detection"""
        confidence = 0.0

        # File extension check
        if file_path:
            ext = Path(file_path).suffix.lower()
            if ext in ['.js', '.jsx', '.mjs', '.cjs']:
                confidence += 90.0

        # JavaScript-specific patterns
        js_patterns = [
            (r'function\s+\w+\s*\(', 15),
            (r'const\s+\w+\s*=', 10),
            (r'let\s+\w+\s*=', 10),
            (r'var\s+\w+\s*=', 5),  # Lower score for var (older JS)
            (r'console\.(log|error|warn)', 15),
            (r'=>\s*\{', 10),  # Arrow functions
            (r'require\s*\(', 15),
            (r'module\.exports', 15),
            (r'import.*from', 10),
            (r'export\s+(default\s+)?', 10),
        ]

        for pattern, score in js_patterns:
            if re.search(pattern, code):
                confidence += score

        # Check if it can actually be analyzed
        if self.can_analyze(code, file_path):
            confidence += 20.0

        return min(confidence, 100.0)


# Export public API
__all__ = [
    'JavaScriptAnalyzer',
    'JavaScriptSecurityStrategy',
    'JavaScriptQualityStrategy',
    'JavaScriptPerformanceStrategy'
]
