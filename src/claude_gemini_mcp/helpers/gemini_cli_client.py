#!/usr/bin/env python3
"""
Gemini CLI Client Module - Subprocess Management and Streaming Execution

This module handles all Gemini CLI subprocess execution with advanced streaming capabilities,
timeout protection, and comprehensive error handling. It provides a clean, secure interface
for executing Gemini CLI commands with real-time output streaming and robust process management.

Key Features:
- Real-time streaming output with queue-based communication
- Timeout protection with graceful process termination (SIGTERM → SIGKILL escalation)
- Command argument sanitization to prevent shell injection attacks
- Progress indicators and elapsed time tracking
- Thread-safe output handling with proper synchronization
- Comprehensive process lifecycle management (start, monitor, cleanup)
- Environment variable handling (PATH, GOOGLE_CLOUD_PROJECT)
- Input validation and size limits

Architecture:
- Main execution function coordinates subprocess lifecycle
- Dedicated streaming thread handles real-time output capture
- Queue-based communication ensures thread safety
- Stop events enable graceful shutdown coordination
- Timeout management with escalating termination strategies

Usage:
    from claude_gemini_mcp.helpers.gemini_cli_client import (
        execute_gemini_cli_streaming,
        validate_cli_availability,
        build_cli_command
    )

    # Execute CLI with streaming output
    result = await execute_gemini_cli_streaming(
        prompt="What is machine learning?",
        model_name="gemini-2.5-flash",
        timeout=60,
        show_progress=True
    )

    # Check CLI availability
    if validate_cli_availability():
        print("Gemini CLI is available")
"""

import os
import subprocess
import sys
import threading
import time
import shutil
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, List, Optional

from claude_gemini_mcp.config import get_config


# Load configuration
cfg = get_config()


def validate_cli_availability() -> bool:
    """Check if Gemini CLI is available in PATH

    Performs a simple availability check by attempting to locate the 'gemini'
    command in the system PATH. This is useful for determining whether CLI
    fallback execution is possible before attempting subprocess calls.

    Returns:
        bool: True if 'gemini' command is found in PATH, False otherwise

    Usage:
        if validate_cli_availability():
            result = await execute_gemini_cli_streaming(prompt)
        else:
            print("Gemini CLI not available - use API instead")

    Note:
        This function only checks availability, not functionality. The CLI
        binary may exist but still fail during execution due to configuration
        issues or missing dependencies.
    """
    return shutil.which("gemini") is not None


def build_cli_command(prompt: str, model_name: Optional[str]) -> List[str]:
    """Build sanitized CLI command arguments

    Constructs a safe command argument list for subprocess execution without
    shell interpretation. Includes input validation and prompt length limiting
    to prevent command line argument overflow.

    Args:
        prompt: Input prompt for the AI model (will be truncated if too long)
        model_name: Optional model name to use (validated for safe characters)

    Returns:
        List[str]: Safe command arguments ready for subprocess.Popen()

    Raises:
        ValueError: If prompt is empty or model_name contains invalid characters

    Security Note:
        This function never uses shell=True and carefully validates all inputs
        to prevent command injection attacks. Only alphanumeric characters,
        dots, and hyphens are allowed in model names.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    # Build command args safely (no shell=True)
    cmd_args = ["gemini"]

    if model_name:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("Invalid model name")
        # Basic sanitization: only allow alphanumeric, dots, hyphens
        if not all(c.isalnum() or c in ".-" for c in model_name):
            raise ValueError("Invalid model name characters")
        cmd_args.extend(["-m", model_name])

    # Limit prompt length for CLI argument safety
    cmd_args.extend(["-p", prompt[:1000]])

    return cmd_args


def stream_subprocess_output(
    process: subprocess.Popen, output_queue: Queue, stop_event: threading.Event
) -> None:
    """Thread function to stream subprocess output with timeout protection

    This function runs in a separate daemon thread and continuously reads
    subprocess output, placing it in a queue for the main thread to process.
    It handles graceful shutdown through stop events and ensures all output
    is captured before termination.

    Args:
        process: The subprocess.Popen object to read from
        output_queue: Thread-safe queue for passing output to main thread
        stop_event: Threading event to signal when streaming should stop

    Queue Message Format:
        ("stdout", data): Standard output data received
        ("error", error_msg): Error occurred during streaming
        ("done", None): Streaming completed normally

    Thread Safety:
        This function is designed to run safely in a daemon thread with
        proper synchronization through the queue and stop event. It will
        automatically terminate when the main thread exits.

    Note:
        The function includes a small delay (0.01s) in the reading loop to
        prevent excessive CPU usage while maintaining responsiveness.
    """
    try:
        while not stop_event.is_set() and process.poll() is None:
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    output_queue.put(("stdout", line))
                elif process.poll() is not None:
                    break
            time.sleep(0.01)  # Small delay to prevent tight loop

        # Get any remaining output
        if process.stdout:
            remaining = process.stdout.read()
            if remaining:
                output_queue.put(("stdout", remaining))
    except Exception as e:
        output_queue.put(("error", str(e)))
    finally:
        output_queue.put(("done", None))


async def execute_gemini_cli_streaming(
    prompt: str, model_name: Optional[str] = None, show_progress: bool = True
) -> Dict[str, Any]:
    """Execute Gemini CLI with timeout-protected real-time streaming output

    This is the main CLI execution function that provides comprehensive subprocess
    management with real-time output streaming, timeout protection, and detailed
    progress reporting. It handles the complete lifecycle from process startup
    through output capture to cleanup.

    Args:
        prompt: Input prompt for the AI model (validated and size-limited)
        model_name: Optional specific model to use (defaults to CLI's default)
        show_progress: Whether to display progress indicators and status messages

    Returns:
        Dict[str, Any]: Execution result with the following structure:
            {
                "success": bool,           # True if execution completed successfully
                "output": str,            # Full output text (if successful)
                "error": str,             # Error message (if failed)
                "partial_output": str     # Partial output (if timed out)
            }

    Features:
        - Input validation with size limits and type checking
        - Command argument sanitization to prevent injection
        - Real-time streaming output with progress indicators
        - Timeout protection with graceful termination (SIGTERM → SIGKILL)
        - Thread-safe output handling through queues
        - Comprehensive error handling and reporting
        - Environment variable preservation (PATH, GOOGLE_CLOUD_PROJECT)
        - Detailed progress tracking with time remaining

    Error Handling:
        - FileNotFoundError: Gemini CLI not found in PATH
        - subprocess.TimeoutExpired: Process exceeded timeout limit
        - Validation errors: Invalid input parameters
        - General subprocess errors: Process execution failures

    Timeout Behavior:
        The function implements a two-stage termination process:
        1. SIGTERM: Graceful termination request (5s timeout)
        2. SIGKILL: Forced termination if graceful fails

    Usage:
        # Basic usage
        result = await execute_gemini_cli_streaming(
            prompt="What is Python?",
            show_progress=True
        )

        # With specific model
        result = await execute_gemini_cli_streaming(
            prompt="Analyze this code",
            model_name="gemini-2.5-pro",
            show_progress=False
        )

        # Check results
        if result["success"]:
            print(f"Output: {result['output']}")
        else:
            print(f"Error: {result['error']}")
    """
    try:
        # Input validation
        if not isinstance(prompt, str) or len(prompt.strip()) == 0:
            return {
                "success": False,
                "error": "Invalid prompt: must be non-empty string",
            }

        # Check prompt size limit from config
        max_prompt_size = cfg.get_limit("max_prompt_size", 1000000)
        if len(prompt) > max_prompt_size:
            return {
                "success": False,
                "error": f"Prompt too large (max {max_prompt_size} bytes)",
            }

        # Validate model name if provided
        if model_name is not None:
            if not isinstance(model_name, str) or not model_name.strip():
                return {"success": False, "error": "Invalid model name"}
            # Basic sanitization: only allow alphanumeric, dots, hyphens
            if not all(c.isalnum() or c in ".-" for c in model_name):
                return {"success": False, "error": "Invalid model name characters"}

        # Build command args safely using helper function
        try:
            cmd_args = build_cli_command(prompt, model_name)
        except ValueError as e:
            return {"success": False, "error": f"Command validation error: {str(e)}"}

        # Get timeout from config
        cli_timeout = cfg.get_timeout("cli_timeout", 60)  # 60 seconds default
        timeout = cli_timeout

        if show_progress:
            print("🔍 Starting timeout-protected Gemini CLI...", file=sys.stderr)
            print(f"📝 Prompt length: {len(prompt)} characters", file=sys.stderr)
            print(f"⏱️ Timeout: {timeout} seconds", file=sys.stderr)
            print("⏳ Streaming output:", file=sys.stderr)
            print("-" * 50, file=sys.stderr)

        # Set up environment
        env = {"PATH": os.environ.get("PATH", "")}
        if "GOOGLE_CLOUD_PROJECT" in os.environ:
            env["GOOGLE_CLOUD_PROJECT"] = os.environ["GOOGLE_CLOUD_PROJECT"]

        # Start process with streaming support
        process = subprocess.Popen(
            cmd_args,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            env=env,
        )

        # Set up threaded streaming with timeout protection
        output_queue = Queue()
        stop_event = threading.Event()

        # Start output streaming thread
        stream_thread = threading.Thread(
            target=stream_subprocess_output,
            args=(process, output_queue, stop_event),
            daemon=True,
        )
        stream_thread.start()

        output_lines = []
        start_time = time.time()
        last_progress_time = start_time
        timeout_reached = False

        # Process output with timeout protection
        while True:
            elapsed = time.time() - start_time

            # Check for timeout
            if elapsed > timeout:
                if show_progress:
                    print(
                        f"\n⚠️ Timeout reached after {timeout}s, terminating...",
                        file=sys.stderr,
                    )
                timeout_reached = True
                stop_event.set()
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    try:
                        process.kill()
                        process.wait(timeout=5)
                    except Exception:
                        pass
                break

            # Try to get output from queue (non-blocking)
            try:
                msg_type, data = output_queue.get(timeout=0.1)

                if msg_type == "stdout" and data:
                    output_lines.append(data)
                    if show_progress:
                        print(data.rstrip(), flush=True)
                    last_progress_time = time.time()

                elif msg_type == "error":
                    if show_progress:
                        print(f"\n⚠️ Stream error: {data}", file=sys.stderr)
                    break

                elif msg_type == "done":
                    if show_progress:
                        print("\n✅ Streaming completed", file=sys.stderr)
                    break

            except Empty:
                # No output received, continue waiting
                pass

            # Show progress periodically
            if show_progress and time.time() - last_progress_time > 15:
                elapsed_seconds = int(elapsed)
                remaining_seconds = max(0, timeout - elapsed_seconds)
                print(
                    f"\n⏱️ Progress: {elapsed_seconds}s elapsed, {remaining_seconds}s remaining",
                    file=sys.stderr,
                )
                last_progress_time = time.time()

            # Check if process finished naturally
            if process.poll() is not None:
                break

            time.sleep(0.1)  # Small delay to prevent tight loop

        # Clean up
        stop_event.set()
        stream_thread.join(timeout=1)

        # Get any remaining stderr
        stderr_output = ""
        try:
            if process.stderr:
                stderr_output = process.stderr.read()
        except Exception:
            pass

        full_output = "".join(output_lines)

        if show_progress:
            print("-" * 50, file=sys.stderr)
            if timeout_reached:
                print(f"⏰ Operation timed out after {timeout}s", file=sys.stderr)
            else:
                print("✅ Analysis complete!", file=sys.stderr)

        # Return results
        if timeout_reached:
            return {
                "success": False,
                "error": f"CLI timeout after {timeout} seconds",
                "partial_output": full_output,
            }
        elif process.returncode == 0:
            return {"success": True, "output": full_output}
        else:
            return {"success": False, "error": stderr_output or "CLI execution failed"}

    except subprocess.TimeoutExpired:
        timeout = cfg.get_timeout("cli_timeout", 60)
        return {"success": False, "error": f"CLI timeout after {timeout} seconds"}
    except FileNotFoundError:
        return {"success": False, "error": "Gemini CLI not found in PATH"}
    except Exception as e:
        return {"success": False, "error": f"CLI execution error: {str(e)}"}


def get_cli_timeout() -> int:
    """Get the configured CLI timeout value

    Returns:
        int: Timeout in seconds from configuration, with 60s default
    """
    return cfg.get_timeout("cli_timeout", 60)
