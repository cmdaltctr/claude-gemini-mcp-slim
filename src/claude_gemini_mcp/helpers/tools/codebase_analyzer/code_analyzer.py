#!/usr/bin/env python3
"""
Clean Public API for Code Analysis

This module provides a simplified, clean interface for codebase analysis
with a focus on ease of use and Gemini prompt injection compatibility.

Key Design Principles:
- Simple function signature with clear parameters
- Returns structured results suitable for AI analysis
- Optimized for direct Gemini prompt injection
- Enterprise-grade security and validation
- Comprehensive error handling

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-20
Architecture: Clean API Facade Pattern
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Import the comprehensive codebase analyzer
from .codebase_analyzer import (
    AnalysisScope,
    CodebaseAnalysisError,
    CodebaseAnalysisResult,
    CodebaseAnalyzer,
    ContentAggregationError,
    FileDiscoveryError,
    ProjectStructureError,
)

# Configure logging
logger = logging.getLogger(__name__)


# Clean API facade for codebase analysis operations
class CodeAnalyzerAPI:
    """
    Clean API facade for codebase analysis operations

    This class provides a simplified interface over the comprehensive
    codebase analysis functionality while maintaining all the power
    and flexibility of the underlying system.
    """

    # Validate input parameters
    @staticmethod
    def _validate_inputs(
        root_path: str, max_total_size: int, config: Optional[dict]
    ) -> None:
        """Validate input parameters"""
        if not isinstance(root_path, str):
            raise ValueError("root_path must be a string")

        if not isinstance(max_total_size, int) or max_total_size <= 0:
            raise ValueError("max_total_size must be a positive integer")

        if config is not None and not isinstance(config, dict):
            raise ValueError("config must be a dictionary or None")

        # Validate path exists
        path_obj = Path(root_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")

        if not path_obj.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {root_path}")

    # Sanitize and set defaults for configuration
    @staticmethod
    def _sanitize_config(config: Optional[dict]) -> Dict[str, Any]:
        """Sanitize and set defaults for configuration"""
        if config is None:
            config = {}

        # Set safe defaults
        sanitized_config = {
            "max_total_size": config.get("max_total_size", 200_000),
            "max_file_size": config.get("max_file_size", 50_000),
            "skip_directories": config.get("skip_directories", []),
            "skip_patterns": config.get("skip_patterns", []),
            "include_hidden": config.get("include_hidden", []),
            "encoding": config.get("encoding", "utf-8"),
        }

        # Validate numerical limits
        if sanitized_config["max_total_size"] > 10_000_000:  # 10MB limit
            logger.warning("max_total_size exceeds recommended limit, capping at 10MB")
            sanitized_config["max_total_size"] = 10_000_000

        if sanitized_config["max_file_size"] > 1_000_000:  # 1MB per file limit
            logger.warning("max_file_size exceeds recommended limit, capping at 1MB")
            sanitized_config["max_file_size"] = 1_000_000

        return sanitized_config

    # Perform comprehensive codebase analysis with clean, simple interface


def analyze_codebase(
    root_path: str, max_total_size: int = 200_000, config: Optional[dict] = None
) -> CodebaseAnalysisResult:
    """
    Perform comprehensive codebase analysis with clean, simple interface

    This function provides a streamlined API for analyzing entire codebases,
    returning structured results optimized for direct Gemini prompt injection
    or further post-processing.

    Args:
        root_path: Absolute or relative path to the codebase root directory
        max_total_size: Maximum total size in bytes for aggregated content (default: 200,000)
        config: Optional configuration dictionary with analysis parameters

    Returns:
        CodebaseAnalysisResult: Comprehensive analysis results containing:
            - project_report: Structured project overview and metrics
            - prompt_payload: Ready-to-use content for AI prompt injection
            - stats: Analysis performance and processing statistics
            - structure: Detailed project structure information
            - tech_stack: Technology stack and dependency analysis
            - architecture: Architecture patterns and design insights
            - file_analyses: Individual file analysis results (if available)
            - error: Error message if analysis failed

    Raises:
        ValueError: If parameters are invalid
        FileNotFoundError: If root_path doesn't exist
        NotADirectoryError: If root_path is not a directory
        CodebaseAnalysisError: If analysis fails

    Example:
        Basic usage:
        >>> result = analyze_codebase("/path/to/project")
        >>> print(f"Found {result.structure.total_files} files")
        >>> print(f"Primary language: {result.project_report['summary']['primary_language']}")

        With configuration:
        >>> config = {
        ...     'skip_directories': ['node_modules', '.git'],
        ...     'max_file_size': 100_000,
        ...     'include_hidden': ['.github']
        ... }
        >>> result = analyze_codebase("/path/to/project", max_total_size=500_000, config=config)

        For Gemini prompt injection:
        >>> result = analyze_codebase("/path/to/project")
        >>> gemini_prompt = f"Analyze this codebase:\\n{result.prompt_payload}"

        Error handling:
        >>> try:
        ...     result = analyze_codebase("/invalid/path")
        ... except FileNotFoundError as e:
        ...     print(f"Path error: {e}")
        ... except CodebaseAnalysisError as e:
        ...     print(f"Analysis failed: {e}")

    Configuration Options:
        - max_total_size: Override the max_total_size parameter
        - max_file_size: Maximum size per individual file (default: 50,000)
        - skip_directories: List of directory names to skip
        - skip_patterns: List of regex patterns for files to skip
        - include_hidden: List of hidden directories to include
        - encoding: File encoding to use (default: 'utf-8')

    Performance Notes:
        - Analysis time scales with project size and file count
        - Large projects may require higher max_total_size limits
        - Consider using skip_patterns for better performance on large codebases
        - The prompt_payload is optimized for AI context windows

    Security Notes:
        - Input validation prevents path traversal attacks
        - File size limits prevent memory exhaustion
        - Content sanitization prevents injection attacks
        - Binary files are automatically excluded
    """
    try:
        # Validate inputs
        CodeAnalyzerAPI._validate_inputs(root_path, max_total_size, config)

        # Sanitize configuration
        sanitized_config = CodeAnalyzerAPI._sanitize_config(config)

        # Override max_total_size in config if provided as parameter
        sanitized_config["max_total_size"] = max_total_size

        logger.info(f"Starting codebase analysis for: {root_path}")
        logger.info(f"Max total size: {max_total_size:,} bytes")

        # Create analyzer instance
        analyzer = CodebaseAnalyzer(root_path, sanitized_config)

        # Perform comprehensive analysis
        result = analyzer.analyze_codebase(max_total_size, AnalysisScope.ALL)

        # Log analysis results
        if result.error:
            logger.error(f"Analysis failed: {result.error}")
        else:
            logger.info(
                f"Analysis completed successfully in {result.stats.total_time:.2f}s"
            )
            logger.info(f"Analyzed {result.stats.files_analyzed} files")
            logger.info(f"Generated {len(result.prompt_payload):,} character payload")

        return result

    # Handle exceptions
    except (ValueError, FileNotFoundError, NotADirectoryError) as e:
        logger.error(f"Input validation failed: {e}")
        raise

    except (FileDiscoveryError, ContentAggregationError, ProjectStructureError) as e:
        logger.error(f"Analysis stage failed: {e}")
        raise CodebaseAnalysisError(f"Codebase analysis failed: {str(e)}") from e

    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise CodebaseAnalysisError(f"Unexpected error: {str(e)}") from e


# Export the clean public API
__all__ = ["analyze_codebase", "CodebaseAnalysisResult", "CodebaseAnalysisError"]
