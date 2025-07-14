#!/usr/bin/env python3
"""
Optimized test runner with multiple execution modes.
Handles parallel execution, timeouts, and proper resource management.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], timeout: Optional[int] = None) -> int:
    """
    Run a command with proper error handling and timeout.

    Args:
        cmd: Command to execute as list of strings
        timeout: Optional timeout in seconds

    Returns:
        Exit code
    """
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            cwd=Path(__file__).parent.parent,
            env=os.environ.copy(),
        )

        duration = time.time() - start_time
        print(
            f"Command completed in {duration:.2f}s with exit code {result.returncode}"
        )
        return result.returncode

    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        return 1
    except Exception as e:
        print(f"Command failed with error: {e}")
        return 1


def install_dependencies() -> int:
    """Install required test dependencies."""
    print("Installing test dependencies...")
    return run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            "requirements-dev.txt",
            "--quiet",
        ]
    )


def run_fast_tests() -> int:
    """Run unit tests in parallel with minimal coverage."""
    print("Running fast unit tests...")
    return run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/",
            "-n",
            "auto",  # Parallel execution
            "--timeout=10",  # 10 second timeout
            "--no-cov",  # Skip coverage for speed
            "-q",  # Quiet output
            "--tb=short",  # Short traceback
            "--maxfail=3",  # Stop after 3 failures
        ]
    )


def run_integration_tests_sequential() -> int:
    """Run integration tests sequentially with timeouts."""
    print("Running integration tests sequentially...")
    return run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/",
            "-n",
            "1",  # Sequential execution
            "--timeout=30",  # 30 second timeout per test
            "--timeout-method=thread",  # Thread-based timeout
            "--no-cov",  # Skip coverage for speed
            "-v",  # Verbose output
            "--tb=short",  # Short traceback
            "--maxfail=1",  # Stop after first failure
        ]
    )


def run_integration_tests_parallel() -> int:
    """Run integration tests in parallel with proper isolation."""
    print("Running integration tests in parallel...")
    return run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/",
            "-n",
            "2",  # Limited parallel execution
            "--timeout=30",  # 30 second timeout per test
            "--timeout-method=thread",  # Thread-based timeout
            "--no-cov",  # Skip coverage for speed
            "-v",  # Verbose output
            "--tb=short",  # Short traceback
            "--maxfail=2",  # Stop after 2 failures
            "--dist=loadscope",  # Better distribution for integration tests
        ]
    )


def run_all_tests_with_coverage() -> int:
    """Run all tests with coverage report."""
    print("Running all tests with coverage...")
    return run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "-n",
            "auto",  # Parallel execution
            "--timeout=30",  # 30 second timeout
            "--cov=.",  # Enable coverage
            "--cov-report=html",  # HTML coverage report
            "--cov-report=term-missing",  # Terminal coverage report
            "--cov-fail-under=70",  # Require 70% coverage
            "-v",  # Verbose output
            "--tb=short",  # Short traceback
            "--maxfail=5",  # Stop after 5 failures
        ]
    )


def run_specific_test(test_pattern: str) -> int:
    """Run specific test pattern."""
    print(f"Running specific test: {test_pattern}")
    return run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            test_pattern,
            "-n",
            "auto",  # Parallel execution
            "--timeout=30",  # 30 second timeout
            "--no-cov",  # Skip coverage for speed
            "-v",  # Verbose output
            "--tb=long",  # Long traceback for debugging
        ]
    )


def run_debug_mode(test_pattern: str) -> int:
    """Run tests in debug mode with detailed output."""
    print(f"Running debug mode for: {test_pattern}")
    return run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            test_pattern,
            "-n",
            "0",  # No parallel execution
            "--timeout=60",  # Longer timeout
            "--no-cov",  # Skip coverage
            "-vv",  # Very verbose output
            "--tb=long",  # Long traceback
            "--capture=no",  # No output capture
            "--log-cli-level=DEBUG",  # Enable debug logging
        ]
    )


def run_smoke_test() -> int:
    """Run a quick smoke test to verify basic functionality."""
    print("Running smoke test...")
    return run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/test_basic_operations.py",
            "--timeout=10",
            "--no-cov",
            "-v",
            "-x",  # Stop on first failure
        ]
    )


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Optimized test runner")
    parser.add_argument(
        "mode",
        choices=[
            "install",
            "fast",
            "integration",
            "integration-parallel",
            "all",
            "smoke",
            "debug",
            "specific",
        ],
        help="Test execution mode",
    )
    parser.add_argument(
        "--test-pattern", help="Specific test pattern to run (for specific/debug modes)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Global timeout in seconds (default: 300)",
    )

    args = parser.parse_args()

    # Set up environment
    os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)

    # Execute based on mode
    if args.mode == "install":
        exit_code = install_dependencies()
    elif args.mode == "fast":
        exit_code = run_fast_tests()
    elif args.mode == "integration":
        exit_code = run_integration_tests_sequential()
    elif args.mode == "integration-parallel":
        exit_code = run_integration_tests_parallel()
    elif args.mode == "all":
        exit_code = run_all_tests_with_coverage()
    elif args.mode == "smoke":
        exit_code = run_smoke_test()
    elif args.mode == "debug":
        if not args.test_pattern:
            print("Error: --test-pattern required for debug mode")
            return 1
        exit_code = run_debug_mode(args.test_pattern)
    elif args.mode == "specific":
        if not args.test_pattern:
            print("Error: --test-pattern required for specific mode")
            return 1
        exit_code = run_specific_test(args.test_pattern)
    else:
        print(f"Unknown mode: {args.mode}")
        return 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
