"""
Helpers package for utility functions and code analysis.
"""

from .execution_orchestrator import (
    execute_gemini_smart,
    execute_gemini_smart_with_progress,
    split_into_chunks,
)

# Import shared utilities
from .markdown_utils import markdown_to_text
from .security import (
    sanitize_error_message,
    sanitize_for_prompt,
    validate_file_security,
    validate_path_security,
)

# Import from tool modules
from .tools.analyze_code import AnalysisResult, AnalysisType, CodeAnalyzer, analyze_code
from .tools.codebase_analyzer import (
    CodebaseAnalyzer,
    aggregate_contents,
    analyze_codebase,
    build_project_report,
    discover_files,
)

__all__ = [
    "markdown_to_text",
    "analyze_code",
    "CodeAnalyzer",
    "AnalysisType",
    "AnalysisResult",
    "analyze_codebase",
    "CodebaseAnalyzer",
    "discover_files",
    "aggregate_contents",
    "build_project_report",
    "sanitize_for_prompt",
    "validate_path_security",
    "validate_file_security",
    "sanitize_error_message",
    "execute_gemini_smart",
    "execute_gemini_smart_with_progress",
    "split_into_chunks",
]
