#!/usr/bin/env python3
"""Unit tests for helpers.code_analyzer module

These tests focus on discovery, aggregation, truncation, and analysis outputs
of the code analyzer functionality.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from claude_gemini_mcp.helpers.code_analyzer import (
    CodeAnalyzerAPI,
    analyze_codebase,
)
from claude_gemini_mcp.helpers.codebase_analyzer import (
    ArchitectureInfo,
    CodebaseAnalysisError,
    CodebaseAnalysisResult,
    CodebaseStats,
    FileDiscoveryError,
    FileFilter,
    ProjectStructure,
    TechStackInfo,
)


class TestFileFilter(unittest.TestCase):
    """Test cases for FileFilter class

    These tests focus on file discovery and filtering functionality.
    """

    def test_should_analyze_file_unsupported_extension(self):
        """Test that unsupported file extensions are rejected"""
        test_file = Path("/test/file.unknown")
        config = {}
        result = FileFilter.should_analyze_file(test_file, config)
        self.assertFalse(result)

    def test_should_skip_directory_default_skips(self):
        """Test that default skip directories are properly skipped"""
        skip_dirs = ["node_modules", ".git", "__pycache__", "venv"]
        for skip_dir in skip_dirs:
            with self.subTest(skip_dir=skip_dir):
                test_dir = Path(f"/test/{skip_dir}")
                result = FileFilter.should_skip_directory(test_dir, {})
                self.assertTrue(result, f"Should skip {skip_dir}")

    def test_should_skip_directory_custom_skips(self):
        """Test that custom skip directories are properly skipped"""
        test_dir = Path("/test/custom_skip")
        config = {"skip_directories": ["custom_skip"]}
        result = FileFilter.should_skip_directory(test_dir, config)
        self.assertTrue(result)


class TestCodeAnalyzerAPI(unittest.TestCase):
    """Test cases for CodeAnalyzerAPI class"""

    def test_validate_inputs_valid(self):
        """Test input validation with valid inputs"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should not raise any exception
            CodeAnalyzerAPI._validate_inputs(temp_dir, 10000, {"skip_directories": []})

    def test_validate_inputs_invalid_path_type(self):
        """Test input validation with invalid path type"""
        with self.assertRaises(ValueError) as context:
            CodeAnalyzerAPI._validate_inputs(123, 10000, {})
        self.assertIn("root_path must be a string", str(context.exception))

    def test_validate_inputs_invalid_size(self):
        """Test input validation with invalid size"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError) as context:
                CodeAnalyzerAPI._validate_inputs(temp_dir, -1000, {})
            self.assertIn(
                "max_total_size must be a positive integer", str(context.exception)
            )

    def test_validate_inputs_nonexistent_path(self):
        """Test input validation with nonexistent path"""
        with self.assertRaises(FileNotFoundError):
            CodeAnalyzerAPI._validate_inputs("/nonexistent/path", 10000, {})

    def test_validate_inputs_file_not_directory(self):
        """Test input validation when path points to file, not directory"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with self.assertRaises(NotADirectoryError):
                CodeAnalyzerAPI._validate_inputs(temp_file.name, 10000, {})

    def test_sanitize_config_defaults(self):
        """Test configuration sanitization with defaults"""
        result = CodeAnalyzerAPI._sanitize_config(None)

        expected_keys = [
            "max_total_size",
            "max_file_size",
            "skip_directories",
            "skip_patterns",
            "include_hidden",
            "encoding",
        ]
        for key in expected_keys:
            self.assertIn(key, result)

    def test_sanitize_config_limits(self):
        """Test configuration sanitization with excessive limits"""
        config = {
            "max_total_size": 20_000_000,  # 20MB - should be capped
            "max_file_size": 2_000_000,  # 2MB - should be capped
        }

        result = CodeAnalyzerAPI._sanitize_config(config)

        self.assertEqual(result["max_total_size"], 10_000_000)  # Capped at 10MB
        self.assertEqual(result["max_file_size"], 1_000_000)  # Capped at 1MB


class TestAnalyzeCodebase(unittest.TestCase):
    """Test cases for analyze_codebase function"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root_path = Path(self.temp_dir)

        # Create a realistic test project structure
        (self.root_path / "main.py").write_text('def main(): print("hello world")')
        (self.root_path / "README.md").write_text(
            "# Test Project\nThis is a test project."
        )
        (self.root_path / "requirements.txt").write_text(
            "requests==2.28.0\nflask==2.0.0"
        )

        # Create src directory with files
        src_dir = self.root_path / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text(
            "from flask import Flask\napp = Flask(__name__)"
        )
        (src_dir / "utils.py").write_text('def helper_function(): return "helper"')

        # Create test directory
        test_dir = self.root_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_main.py").write_text("def test_main(): assert True")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_analyze_codebase_invalid_path(self):
        """Test error handling with invalid path"""
        with self.assertRaises(FileNotFoundError):
            analyze_codebase("/nonexistent/path")

    def test_analyze_codebase_invalid_parameters(self):
        """Test error handling with invalid parameters"""
        with self.assertRaises(ValueError):
            analyze_codebase(str(self.root_path), max_total_size=-1000)

        with self.assertRaises(ValueError):
            analyze_codebase(123)  # Non-string path


if __name__ == "__main__":
    unittest.main()
