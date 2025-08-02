#!/usr/bin/env python3
"""
Comprehensive unit tests for the Gemini CLI Client module.

Tests CLI execution, subprocess handling, timeout management, and security
as specified in task 1.10 requirements.
"""

import os
import subprocess
import sys
import threading
import time
from queue import Queue
from unittest.mock import MagicMock, patch
import pytest

# Add project root to path for imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from claude_gemini_mcp.helpers.gemini_cli_client import (
    build_cli_command,
    execute_gemini_cli_streaming,
    get_cli_timeout,
    stream_subprocess_output,
    validate_cli_availability,
)


class TestCLIAvailability:
    """Test CLI availability validation functionality."""

    @patch('shutil.which')
    def test_validate_cli_availability_available(self, mock_which):
        """Test when Gemini CLI is available in PATH."""
        mock_which.return_value = "/usr/local/bin/gemini"

        result = validate_cli_availability()
        assert result is True
        mock_which.assert_called_once_with("gemini")

    @patch('shutil.which')
    def test_validate_cli_availability_unavailable(self, mock_which):
        """Test when Gemini CLI is not available in PATH."""
        mock_which.return_value = None

        result = validate_cli_availability()
        assert result is False
        mock_which.assert_called_once_with("gemini")


class TestCommandBuilding:
    """Test CLI command construction and validation."""

    def test_build_cli_command_basic(self):
        """Test basic command construction."""
        prompt = "What is Python?"
        model = "gemini-2.5-flash"

        result = build_cli_command(prompt, model)

        expected = ["gemini", "-m", "gemini-2.5-flash", "-p", "What is Python?"]
        assert result == expected

    def test_build_cli_command_no_model(self):
        """Test command construction without model specification."""
        prompt = "What is Python?"

        result = build_cli_command(prompt, None)

        expected = ["gemini", "-p", "What is Python?"]
        assert result == expected

    def test_build_cli_command_prompt_truncation(self):
        """Test that overly long prompts are truncated."""
        long_prompt = "A" * 1500  # Longer than 1000 char limit
        model = "gemini-2.5-flash"

        result = build_cli_command(long_prompt, model)

        assert result[4] == "A" * 1000  # Should be truncated to 1000 chars
        assert len(result[4]) == 1000

    def test_build_cli_command_empty_prompt(self):
        """Test handling of empty prompt."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            build_cli_command("", "gemini-2.5-flash")

    def test_build_cli_command_whitespace_prompt(self):
        """Test handling of whitespace-only prompt."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            build_cli_command("   ", "gemini-2.5-flash")

    def test_build_cli_command_empty_model(self):
        """Test handling of empty model name (should use default)."""
        result = build_cli_command("Test prompt", "")
        expected = ["gemini", "-p", "Test prompt"]
        assert result == expected

    def test_build_cli_command_invalid_model_whitespace(self):
        """Test handling of whitespace-only model name."""
        with pytest.raises(ValueError, match="Invalid model name"):
            build_cli_command("Test prompt", "   ")

    def test_build_cli_command_invalid_model_characters(self):
        """Test handling of model names with invalid characters."""
        invalid_models = [
            "model$name",
            "model@name",
            "model name",
            "model/name",
            "model;name",
        ]

        for model in invalid_models:
            with pytest.raises(ValueError, match="Invalid model name characters"):
                build_cli_command("Test prompt", model)

    def test_build_cli_command_valid_model_characters(self):
        """Test that valid model names are accepted."""
        valid_models = [
            "gemini-pro",
            "gemini-2.5-flash",
            "model.v1",
            "test-model-123",
        ]

        for model in valid_models:
            result = build_cli_command("Test prompt", model)
            assert result[2] == model  # Model should be preserved


class TestSubprocessOutputStreaming:
    """Test subprocess output streaming functionality."""

    def test_stream_subprocess_output_success(self):
        """Test successful output streaming."""
        # Create mock process
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, None, 0]  # Running, then finished
        mock_process.stdout.readline.side_effect = [
            "First line\n",
            "Second line\n",
            "",  # EOF
        ]
        mock_process.stdout.read.return_value = "Final output"

        # Create queue and stop event
        output_queue = Queue()
        stop_event = threading.Event()

        # Run streaming in thread
        thread = threading.Thread(
            target=stream_subprocess_output,
            args=(mock_process, output_queue, stop_event),
            daemon=True
        )
        thread.start()

        # Collect output
        outputs = []
        done = False
        timeout_count = 0

        while not done and timeout_count < 50:  # Prevent infinite loop
            try:
                msg_type, data = output_queue.get(timeout=0.1)
                outputs.append((msg_type, data))
                if msg_type == "done":
                    done = True
            except:
                timeout_count += 1

        thread.join(timeout=1)

        # Verify outputs
        assert len(outputs) >= 2  # Should have at least stdout messages + done
        assert any(msg_type == "stdout" for msg_type, _ in outputs)
        assert outputs[-1] == ("done", None)

    def test_stream_subprocess_output_error(self):
        """Test error handling in output streaming."""
        # Create mock process that raises exception
        mock_process = MagicMock()
        mock_process.poll.side_effect = Exception("Process error")

        output_queue = Queue()
        stop_event = threading.Event()

        # Run streaming
        thread = threading.Thread(
            target=stream_subprocess_output,
            args=(mock_process, output_queue, stop_event),
            daemon=True
        )
        thread.start()
        thread.join(timeout=1)

        # Should have error message
        msg_type, data = output_queue.get(timeout=1)
        assert msg_type == "error"
        assert "Process error" in data

    def test_stream_subprocess_output_stop_event(self):
        """Test that stop event terminates streaming."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process still running
        mock_process.stdout.readline.return_value = "output\n"

        output_queue = Queue()
        stop_event = threading.Event()

        # Start streaming
        thread = threading.Thread(
            target=stream_subprocess_output,
            args=(mock_process, output_queue, stop_event),
            daemon=True
        )
        thread.start()

        # Let it run briefly then stop
        time.sleep(0.1)
        stop_event.set()
        thread.join(timeout=1)

        # Should terminate and send done message
        messages = []
        while not output_queue.empty():
            messages.append(output_queue.get())

        assert messages[-1] == ("done", None)


class TestCLIExecution:
    """Test main CLI execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_invalid_prompt_empty(self):
        """Test handling of empty prompt."""
        result = await execute_gemini_cli_streaming("", show_progress=False)

        assert result["success"] is False
        assert "Invalid prompt: must be non-empty string" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_invalid_prompt_non_string(self):
        """Test handling of non-string prompt."""
        result = await execute_gemini_cli_streaming(123, show_progress=False)

        assert result["success"] is False
        assert "Invalid prompt: must be non-empty string" in result["error"]

    @patch('claude_gemini_mcp.helpers.gemini_cli_client.cfg')
    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_prompt_too_large(self, mock_cfg):
        """Test handling of oversized prompt."""
        mock_cfg.get_limit.return_value = 1000  # Set small limit for test

        large_prompt = "A" * 1001  # Just over limit
        result = await execute_gemini_cli_streaming(large_prompt, show_progress=False)

        assert result["success"] is False
        assert "Prompt too large" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_invalid_model_name(self):
        """Test handling of invalid model name."""
        result = await execute_gemini_cli_streaming(
            "test prompt",
            model_name="",
            show_progress=False
        )

        assert result["success"] is False
        assert "Invalid model name" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_invalid_model_characters(self):
        """Test handling of model name with invalid characters."""
        result = await execute_gemini_cli_streaming(
            "test prompt",
            model_name="model$name",
            show_progress=False
        )

        assert result["success"] is False
        assert "Invalid model name characters" in result["error"]

    @patch('subprocess.Popen')
    @patch('claude_gemini_mcp.helpers.gemini_cli_client.cfg')
    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_success(self, mock_cfg, mock_popen):
        """Test successful CLI execution."""
        # Setup config mock
        mock_cfg.get_limit.return_value = 1000000
        mock_cfg.get_timeout.return_value = 60

        # Setup process mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.poll.side_effect = [None, None, 0]  # Running, then finished
        mock_process.stdout.readline.side_effect = [
            "Response line 1\nResponse line 2\n",
            "",  # EOF
        ]
        mock_process.stdout.read.return_value = ""
        mock_process.stderr.read.return_value = ""
        mock_popen.return_value = mock_process

        result = await execute_gemini_cli_streaming(
            "Test prompt",
            "gemini-2.5-flash",
            show_progress=False
        )

        assert result["success"] is True
        assert "Response line 1" in result["output"]
        assert "Response line 2" in result["output"]

        # Verify subprocess was called correctly
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0] == ["gemini", "-m", "gemini-2.5-flash", "-p", "Test prompt"]
        assert call_args[1]["shell"] is False  # Security: no shell=True

    @patch('subprocess.Popen')
    @patch('claude_gemini_mcp.helpers.gemini_cli_client.cfg')
    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_failure(self, mock_cfg, mock_popen):
        """Test CLI execution failure."""
        # Setup config mock
        mock_cfg.get_limit.return_value = 1000000
        mock_cfg.get_timeout.return_value = 60

        # Setup process mock for failure
        mock_process = MagicMock()
        mock_process.returncode = 1  # Non-zero exit code
        mock_process.pid = 12345
        mock_process.poll.side_effect = [None, 1]  # Running, then failed
        mock_process.stdout.readline.return_value = ""
        mock_process.stdout.read.return_value = ""
        mock_process.stderr.read.return_value = "CLI error message"
        mock_popen.return_value = mock_process

        result = await execute_gemini_cli_streaming(
            "Test prompt",
            "gemini-2.5-flash",
            show_progress=False
        )

        assert result["success"] is False
        assert "CLI error message" in result["error"]

    @patch('subprocess.Popen')
    @patch('claude_gemini_mcp.helpers.gemini_cli_client.cfg')
    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_timeout(self, mock_cfg, mock_popen):
        """Test CLI execution timeout handling."""
        # Setup config mock with very short timeout
        mock_cfg.get_limit.return_value = 1000000
        mock_cfg.get_timeout.return_value = 0.1  # Very short timeout

        # Setup process mock that never finishes
        mock_process = MagicMock()
        mock_process.returncode = None  # Never finishes
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Always running
        mock_process.stdout.readline.return_value = ""
        mock_process.stdout.read.return_value = ""
        mock_process.stderr.read.return_value = ""
        mock_process.terminate.return_value = None
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        result = await execute_gemini_cli_streaming(
            "Test prompt",
            "gemini-2.5-flash",
            show_progress=False
        )

        assert result["success"] is False
        assert "CLI timeout" in result["error"]
        assert "partial_output" in result  # Should provide partial output

        # Verify process termination was attempted
        mock_process.terminate.assert_called()

    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_file_not_found(self):
        """Test handling when CLI binary is not found."""
        with patch('subprocess.Popen', side_effect=FileNotFoundError()):
            result = await execute_gemini_cli_streaming(
                "Test prompt",
                "gemini-2.5-flash",
                show_progress=False
            )

            assert result["success"] is False
            assert "Gemini CLI not found in PATH" in result["error"]

    @patch('subprocess.Popen')
    @patch('claude_gemini_mcp.helpers.gemini_cli_client.cfg')
    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_environment_handling(self, mock_cfg, mock_popen):
        """Test that environment variables are properly handled."""
        # Setup config mock
        mock_cfg.get_limit.return_value = 1000000
        mock_cfg.get_timeout.return_value = 60

        # Setup process mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.poll.return_value = 0
        mock_process.stdout.readline.return_value = ""
        mock_process.stdout.read.return_value = "Success"
        mock_process.stderr.read.return_value = ""
        mock_popen.return_value = mock_process

        # Set environment variable
        with patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            result = await execute_gemini_cli_streaming(
                "Test prompt",
                "gemini-2.5-flash",
                show_progress=False
            )

        # Verify environment was passed to subprocess
        call_args = mock_popen.call_args
        env = call_args[1]["env"]
        assert "PATH" in env
        assert env["GOOGLE_CLOUD_PROJECT"] == "test-project"

    @patch('subprocess.Popen')
    @patch('claude_gemini_mcp.helpers.gemini_cli_client.cfg')
    @pytest.mark.asyncio
    async def test_execute_gemini_cli_streaming_no_model(self, mock_cfg, mock_popen):
        """Test CLI execution without specifying model."""
        # Setup mocks
        mock_cfg.get_limit.return_value = 1000000
        mock_cfg.get_timeout.return_value = 60

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.poll.return_value = 0
        mock_process.stdout.readline.return_value = ""
        mock_process.stdout.read.return_value = "Success"
        mock_process.stderr.read.return_value = ""
        mock_popen.return_value = mock_process

        result = await execute_gemini_cli_streaming(
            "Test prompt",
            model_name=None,
            show_progress=False
        )

        assert result["success"] is True

        # Verify command was built without model parameter
        call_args = mock_popen.call_args
        command = call_args[0][0]
        assert command == ["gemini", "-p", "Test prompt"]  # No -m flag


class TestConfigurationAndTimeout:
    """Test configuration and timeout functionality."""

    @patch('claude_gemini_mcp.helpers.gemini_cli_client.cfg')
    def test_get_cli_timeout(self, mock_cfg):
        """Test CLI timeout retrieval from configuration."""
        mock_cfg.get_timeout.return_value = 120

        timeout = get_cli_timeout()

        assert timeout == 120
        mock_cfg.get_timeout.assert_called_once_with("cli_timeout", 60)

    @patch('claude_gemini_mcp.helpers.gemini_cli_client.cfg')
    def test_get_cli_timeout_default(self, mock_cfg):
        """Test CLI timeout default value."""
        mock_cfg.get_timeout.return_value = 60  # Default value

        timeout = get_cli_timeout()

        assert timeout == 60


class TestSecurityFeatures:
    """Test security-related functionality."""

    def test_command_injection_prevention(self):
        """Test that command injection is prevented."""
        # These should not be able to inject commands
        dangerous_inputs = [
            "prompt; rm -rf /",
            "prompt && malicious_command",
            "prompt | cat /etc/passwd",
            "prompt `whoami`",
            "prompt $(whoami)",
        ]

        for dangerous_input in dangerous_inputs:
            result = build_cli_command(dangerous_input, "gemini-pro")

            # Should be safely contained in arguments
            assert len(result) == 5  # ["gemini", "-m", "model", "-p", "prompt"]
            assert result[4] == dangerous_input  # Exact string preserved, not interpreted

    def test_model_name_sanitization(self):
        """Test that model names are properly sanitized."""
        # These should be rejected
        dangerous_models = [
            "../../../malicious",
            "model; echo dangerous",
            "model && rm file",
            "model | cat",
        ]

        for dangerous_model in dangerous_models:
            with pytest.raises(ValueError, match="Invalid model name characters"):
                build_cli_command("Test prompt", dangerous_model)

    @patch('subprocess.Popen')
    @patch('claude_gemini_mcp.helpers.gemini_cli_client.cfg')
    @pytest.mark.asyncio
    async def test_shell_false_enforcement(self, mock_cfg, mock_popen):
        """Test that shell=False is enforced for security."""
        # Setup mocks
        mock_cfg.get_limit.return_value = 1000000
        mock_cfg.get_timeout.return_value = 60

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.poll.return_value = 0
        mock_process.stdout.readline.return_value = ""
        mock_process.stdout.read.return_value = "Success"
        mock_process.stderr.read.return_value = ""
        mock_popen.return_value = mock_process

        await execute_gemini_cli_streaming(
            "Test prompt",
            "gemini-2.5-flash",
            show_progress=False
        )

        # Verify shell=False was used
        call_args = mock_popen.call_args
        assert call_args[1]["shell"] is False


if __name__ == "__main__":
    pytest.main([__file__])
