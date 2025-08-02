#!/usr/bin/env python3
"""
Unit tests for the execution orchestrator module.

These tests verify the intelligent orchestration functionality including:
- Smart execution with API-first, CLI-fallback strategy
- Result processing pipeline with markdown conversion
- Progress-enhanced execution coordination
- Text chunking utilities for streaming display
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from claude_gemini_mcp.helpers.execution_orchestrator import (
    execute_gemini_smart,
    execute_gemini_smart_with_progress,
    split_into_chunks,
    _process_result_output,
)


class TestSplitIntoChunks:
    """Test text chunking functionality."""

    def test_split_short_text(self):
        """Test chunking of text shorter than chunk size."""
        text = "Hello world"
        result = split_into_chunks(text, chunk_size=20)
        assert result == ["Hello world"]

    def test_split_long_text(self):
        """Test chunking of text longer than chunk size."""
        text = "This is a long text that needs to be split into smaller chunks"
        result = split_into_chunks(text, chunk_size=20)
        assert len(result) > 1
        # Verify all chunks respect word boundaries
        for chunk in result:
            assert len(chunk) <= 20 or " " not in chunk[20:]

    def test_split_empty_text(self):
        """Test chunking of empty text."""
        result = split_into_chunks("", chunk_size=10)
        assert result == []  # Empty text should return empty list

    def test_split_single_long_word(self):
        """Test chunking when single word exceeds chunk size."""
        text = "supercalifragilisticexpialidocious"
        result = split_into_chunks(text, chunk_size=10)
        assert len(result) == 1
        assert result[0] == text  # Single long word should remain intact

    def test_split_custom_chunk_size(self):
        """Test chunking with different chunk sizes."""
        text = "The quick brown fox jumps over the lazy dog"

        # Test with small chunk size
        small_chunks = split_into_chunks(text, chunk_size=10)
        large_chunks = split_into_chunks(text, chunk_size=50)

        assert len(small_chunks) > len(large_chunks)


class TestProcessResultOutput:
    """Test result processing pipeline."""

    def test_process_successful_result_no_conversion(self):
        """Test processing successful result without markdown conversion."""
        result = {"success": True, "output": "Test output"}
        processed = _process_result_output(result, convert_markdown=False, show_progress=False)

        assert processed["success"] is True
        assert processed["output"] == "Test output"

    def test_process_failed_result(self):
        """Test processing failed result."""
        result = {"success": False, "error": "Test error"}
        processed = _process_result_output(result, convert_markdown=True, show_progress=False)

        # Should return unchanged for failed results
        assert processed == result

    def test_process_empty_output(self):
        """Test processing result with empty output."""
        result = {"success": True, "output": ""}
        processed = _process_result_output(result, convert_markdown=True, show_progress=False)

        # Should return unchanged for empty output
        assert processed == result

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.MARKDOWN_UTILS_AVAILABLE', True)
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.markdown_to_text')
    def test_process_with_markdown_conversion_success(self, mock_markdown_to_text):
        """Test successful markdown conversion."""
        mock_markdown_to_text.return_value = "Plain text output"
        result = {"success": True, "output": "**Bold** markdown"}

        processed = _process_result_output(result, convert_markdown=True, show_progress=False)

        mock_markdown_to_text.assert_called_once_with("**Bold** markdown")
        assert processed["output"] == "Plain text output"

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.MARKDOWN_UTILS_AVAILABLE', True)
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.markdown_to_text')
    def test_process_with_markdown_conversion_failure(self, mock_markdown_to_text):
        """Test markdown conversion failure handling."""
        mock_markdown_to_text.side_effect = Exception("Conversion failed")
        original_output = "**Bold** markdown"
        result = {"success": True, "output": original_output}

        processed = _process_result_output(result, convert_markdown=True, show_progress=False)

        # Should keep original output on conversion failure
        assert processed["output"] == original_output

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.MARKDOWN_UTILS_AVAILABLE', False)
    def test_process_without_markdown_utils(self):
        """Test processing when markdown utils are not available."""
        result = {"success": True, "output": "**Bold** markdown"}
        processed = _process_result_output(result, convert_markdown=True, show_progress=False)

        # Should keep original output when markdown utils unavailable
        assert processed["output"] == "**Bold** markdown"


class TestExecuteGeminiSmart:
    """Test smart execution orchestration."""

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.get_api_key')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.execute_gemini_api')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.cfg')
    @pytest.mark.asyncio
    async def test_api_success_path(self, mock_cfg, mock_api_exec, mock_get_api_key):
        """Test successful API execution path."""
        # Setup mocks
        mock_get_api_key.return_value = "test-api-key"
        mock_cfg.get_model.return_value = "gemini-2.5-flash"
        mock_api_exec.return_value = {"success": True, "output": "API response"}

        # Execute
        result = await execute_gemini_smart("Test prompt", show_progress=False)

        # Verify
        mock_get_api_key.assert_called_once()
        mock_api_exec.assert_called_once_with("Test prompt", "gemini-2.5-flash", False)
        assert result["success"] is True
        assert result["output"] == "API response"

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.get_api_key')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.execute_gemini_api')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.execute_gemini_cli_streaming')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.cfg')
    @pytest.mark.asyncio
    async def test_api_failure_cli_fallback(self, mock_cfg, mock_cli_exec, mock_api_exec, mock_get_api_key):
        """Test API failure with CLI fallback."""
        # Setup mocks
        mock_get_api_key.return_value = "test-api-key"
        mock_cfg.get_model.return_value = "gemini-2.5-flash"
        mock_api_exec.return_value = {"success": False, "error": "API failed"}
        mock_cli_exec.return_value = {"success": True, "output": "CLI response"}

        # Execute
        result = await execute_gemini_smart("Test prompt", show_progress=False)

        # Verify both API and CLI were called
        mock_api_exec.assert_called_once()
        mock_cli_exec.assert_called_once_with("Test prompt", "gemini-2.5-flash", False)
        assert result["success"] is True
        assert result["output"] == "CLI response"

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.get_api_key')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.execute_gemini_cli_streaming')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.cfg')
    @pytest.mark.asyncio
    async def test_no_api_key_direct_cli(self, mock_cfg, mock_cli_exec, mock_get_api_key):
        """Test direct CLI execution when no API key available."""
        # Setup mocks
        mock_get_api_key.return_value = None
        mock_cfg.get_model.return_value = "gemini-2.5-flash"
        mock_cli_exec.return_value = {"success": True, "output": "CLI response"}

        # Execute
        result = await execute_gemini_smart("Test prompt", show_progress=False)

        # Verify only CLI was called
        mock_cli_exec.assert_called_once_with("Test prompt", "gemini-2.5-flash", False)
        assert result["success"] is True
        assert result["output"] == "CLI response"

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.cfg')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.get_api_key')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.execute_gemini_cli_streaming')
    @pytest.mark.asyncio
    async def test_model_selection_fallback(self, mock_cli_exec, mock_get_api_key, mock_cfg):
        """Test model selection with config fallback."""
        # Setup mocks - config returns None, should fall back to legacy logic
        mock_cfg.get_model.return_value = None
        mock_get_api_key.return_value = None
        mock_cli_exec.return_value = {"success": True, "output": "CLI response"}

        # Execute with analyze_code task type (should use "pro" model)
        result = await execute_gemini_smart("Test prompt", task_type="analyze_code", show_progress=False)

        # Should use the legacy model assignment
        expected_model = "gemini-2.5-pro"  # Default "pro" model
        mock_cli_exec.assert_called_once_with("Test prompt", expected_model, False)


class TestExecuteGeminiSmartWithProgress:
    """Test progress-enhanced execution."""

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.PROGRESS_AVAILABLE', False)
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.execute_gemini_smart')
    def test_progress_unavailable_fallback(self, mock_smart_exec):
        """Test fallback when progress utilities unavailable."""
        mock_smart_exec.return_value = {"success": True, "output": "Test output"}

        result = execute_gemini_smart_with_progress("Test prompt")

        # Should call standard smart execution with progress enabled
        mock_smart_exec.assert_called_once()
        call_args = mock_smart_exec.call_args
        assert call_args[0][0] == "Test prompt"  # prompt
        assert call_args[0][1] == "quick_query"  # task_type
        assert call_args[1]["show_progress"] is True

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.PROGRESS_AVAILABLE', True)
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.create_spinner_progress')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.execute_gemini_smart')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.split_into_chunks')
    def test_progress_success_with_streaming(self, mock_split, mock_smart_exec, mock_create_progress):
        """Test successful execution with progress indicators and streaming."""
        # Setup mocks
        mock_progress = MagicMock()
        mock_create_progress.return_value = mock_progress
        mock_smart_exec.return_value = {"success": True, "output": "Test response output"}
        mock_split.return_value = ["Test response", " output"]

        # Execute
        result = execute_gemini_smart_with_progress("Test prompt")

        # Verify progress coordination
        mock_progress.start.assert_called_once_with("Processing request")
        mock_progress.complete.assert_called_once_with("Request completed")

        # Verify streaming was called
        assert mock_progress.stream_chunk.call_count >= 2  # For chunks + newline

        assert result["success"] is True

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.PROGRESS_AVAILABLE', True)
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.create_spinner_progress')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.execute_gemini_smart')
    def test_progress_execution_error(self, mock_smart_exec, mock_create_progress):
        """Test error handling in progress execution."""
        # Setup mocks
        mock_progress = MagicMock()
        mock_create_progress.return_value = mock_progress
        mock_smart_exec.return_value = {"success": False, "error": "Test error"}

        # Execute
        result = execute_gemini_smart_with_progress("Test prompt")

        # Verify error handling
        mock_progress.start.assert_called_once_with("Processing request")
        mock_progress.stop.assert_called_once_with("Error: Test error")

        assert result["success"] is False
        assert result["error"] == "Test error"

    @patch('claude_gemini_mcp.helpers.execution_orchestrator.PROGRESS_AVAILABLE', True)
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.create_spinner_progress')
    @patch('claude_gemini_mcp.helpers.execution_orchestrator.execute_gemini_smart')
    def test_progress_unexpected_exception(self, mock_smart_exec, mock_create_progress):
        """Test unexpected exception handling."""
        # Setup mocks
        mock_progress = MagicMock()
        mock_create_progress.return_value = mock_progress
        mock_smart_exec.side_effect = Exception("Unexpected error")

        # Execute
        result = execute_gemini_smart_with_progress("Test prompt")

        # Verify exception handling
        mock_progress.stop.assert_called_once_with("Unexpected error: Unexpected error")
        assert result["success"] is False
        assert "Unexpected error" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__])
