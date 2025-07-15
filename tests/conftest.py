#!/usr/bin/env python3
"""
Pytest configuration file with shared fixtures and test utilities.
Provides proper test isolation and resource management.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import TextContent


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the entire test session.
    This prevents event loop issues in async tests.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_environment() -> Generator[None, None, None]:
    """
    Reset environment variables and state between tests.
    This ensures test isolation.
    """
    # Store original environment
    original_env = dict(os.environ)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """
    Create a temporary workspace for file operations.
    Automatically cleaned up after test.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        yield Path(temp_dir)

        os.chdir(original_cwd)


@pytest.fixture
def mock_process() -> MagicMock:
    """
    Create a mock subprocess for CLI testing.
    Provides proper cleanup and realistic behavior.
    """
    process = MagicMock()
    process.returncode = 0
    process.pid = 12345
    process.stdout.readline = AsyncMock(return_value=b"")
    process.communicate = AsyncMock(return_value=(b"test output", b""))
    process.wait = AsyncMock(return_value=0)
    process.terminate = MagicMock()
    process.kill = MagicMock()

    return process


@pytest.fixture
def mock_gemini_api() -> Dict[str, Any]:
    """
    Create a mock Gemini API for testing.
    Provides realistic API responses.
    """
    mock_genai = MagicMock()
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mock API response"

    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mock_genai.GenerativeModel.return_value = mock_model

    return {"genai": mock_genai, "model": mock_model, "response": mock_response}


@pytest.fixture
def mock_api_key() -> str:
    """
    Provide a mock API key for testing.
    """
    return "mock_api_key_AIzaSyBHJ5X2K9L8M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z"


@pytest.fixture
def fake_api_key() -> str:
    """
    Provide a deterministic dummy API key for testing.
    This key is non-secret and safe for use in tests.
    """
    return "test-api-key-1234567890"


@pytest.fixture
def sample_code() -> str:
    """
    Provide sample code for testing code analysis.
    """
    return '''
def hello_world():
    """Print a greeting message."""
    print("Hello, World!")
    return True

def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b

if __name__ == "__main__":
    hello_world()
    result = calculate_sum(2, 3)
    print(f"Sum: {result}")
'''


@pytest.fixture
def large_code_sample() -> str:
    """
    Provide a large code sample for testing limits.
    """
    lines = []
    for i in range(100):
        lines.append(f"def function_{i}():")
        lines.append(f'    """Function number {i}."""')
        lines.append(f'    return "Result from function {i}"')
        lines.append("")

    return "\n".join(lines)


@pytest.fixture
def mock_text_content() -> Callable[[str], TextContent]:
    """
    Create mock TextContent for MCP responses.
    """

    def _create_content(text: str) -> TextContent:
        return TextContent(type="text", text=text)

    return _create_content


@pytest.fixture
def integration_test_timeout() -> int:
    """
    Provide a shorter timeout for integration tests.
    """
    return 10  # seconds


@pytest.fixture(autouse=True)
def patch_imports() -> Generator[None, None, None]:
    """
    Patch problematic imports that might cause issues in tests.
    """
    with patch.dict("sys.modules", {"google.generativeai": MagicMock()}):
        yield


@pytest.fixture
def mock_cli_execution() -> Callable[..., Dict[str, Any]]:
    """
    Create a factory for mock CLI execution results.
    """

    def _create_result(
        success: bool = True,
        output: str = "Mock CLI output",
        error: str = "",
        returncode: int = 0,
    ) -> Dict[str, Any]:
        return {
            "success": success,
            "output": output,
            "error": error,
            "returncode": returncode,
        }

    return _create_result


@pytest.fixture
def slow_operation_mock() -> Callable[[float], Any]:
    """
    Create a mock that simulates slow operations for timeout testing.
    """

    async def _slow_operation(delay: float = 0.1) -> str:
        await asyncio.sleep(delay)
        return "Slow operation completed"

    return _slow_operation


@pytest.fixture
def resource_cleanup() -> Generator[Callable[[Any], None], None, None]:
    """
    Track resources that need cleanup after tests.
    """
    resources = []

    def register_resource(resource: Any) -> None:
        resources.append(resource)

    yield register_resource

    # Cleanup registered resources
    for resource in resources:
        try:
            if hasattr(resource, "close"):
                resource.close()
            elif hasattr(resource, "terminate"):
                resource.terminate()
            elif hasattr(resource, "cleanup"):
                resource.cleanup()
        except Exception:
            # Ignore cleanup errors in tests
            pass


@pytest.fixture
def parallel_safe_mock() -> Callable[..., MagicMock]:
    """
    Create process-safe mocks for parallel test execution.
    """

    def _create_mock(**kwargs: Any) -> MagicMock:
        mock = MagicMock(**kwargs)
        # Make the mock process-safe
        # Make the mock process-safe by setting a custom __reduce__ method
        # This helps with parallel test execution
        mock.__dict__["__reduce__"] = lambda: (MagicMock, ())
        return mock

    return _create_mock


# Pytest hooks for better test execution
def pytest_configure(config: Any) -> None:
    """
    Configure pytest for optimal parallel execution.
    """
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "timeout: marks tests that should timeout")


def pytest_collection_modifyitems(config: Any, items: List[Any]) -> None:
    """
    Modify test collection to add appropriate markers.
    """
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark slow tests
        if "slow" in item.name.lower() or "large" in item.name.lower():
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item: Any) -> None:
    """
    Setup each test with proper isolation.
    """
    # Clear any existing patches
    if hasattr(item, "_patches"):
        for patch_obj in item._patches:
            patch_obj.stop()
        item._patches = []
    else:
        item._patches = []


def pytest_runtest_teardown(item: Any) -> None:
    """
    Teardown each test with proper cleanup.
    """
    # Stop any remaining patches
    if hasattr(item, "_patches"):
        for patch_obj in item._patches:
            try:
                patch_obj.stop()
            except Exception:
                pass
        item._patches = []


# Test markers for different test types
pytestmark = [
    pytest.mark.asyncio,  # Enable asyncio for all tests
]
