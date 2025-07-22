#!/usr/bin/env python3
"""
Unit tests for hybrid progress utility functionality.
"""

import threading
import time
from io import StringIO
from typing import Any, Dict
from unittest.mock import patch

import pytest

from claude_gemini_mcp.helpers.hybrid_progress import (
    HybridStreamingProgress,
    ProgressConfig,
    ProgressState,
    ProgressType,
    create_bar_progress,
    create_dots_progress,
    create_pulse_progress,
    create_spinner_progress,
)


@pytest.mark.unit
class TestProgressCreation:
    """Test progress indicator creation functions."""

    def test_create_spinner_progress(self):
        """Test spinner progress creation."""
        progress = create_spinner_progress("Test Task")
        assert progress is not None
        assert progress.config.progress_type == ProgressType.SPINNER
        assert "Test Task" in progress.config.prefix

    def test_create_pulse_progress(self):
        """Test pulse progress creation."""
        progress = create_pulse_progress("Test Task")
        assert progress is not None
        assert progress.config.progress_type == ProgressType.PULSE
        assert "Test Task" in progress.config.prefix

    def test_create_bar_progress(self):
        """Test bar progress creation."""
        progress = create_bar_progress("Test Task", width=20)
        assert progress is not None
        assert progress.config.progress_type == ProgressType.BAR
        assert progress.config.width == 20
        assert "Test Task" in progress.config.prefix

    def test_create_dots_progress(self):
        """Test dots progress creation."""
        progress = create_dots_progress("Test Task")
        assert progress is not None
        assert progress.config.progress_type == ProgressType.DOTS
        assert "Test Task" in progress.config.prefix


@pytest.mark.unit
class TestProgressConfiguration:
    """Test progress configuration options."""

    def test_progress_config_creation(self):
        """Test creating custom progress configuration."""
        config = ProgressConfig(
            progress_type=ProgressType.SPINNER,
            prefix="Custom Task ",
            suffix=" working...",
            colors=True,
            interval=0.2,
        )

        assert config.progress_type == ProgressType.SPINNER
        assert config.prefix == "Custom Task "
        assert config.suffix == " working..."
        assert config.colors is True
        assert config.interval == 0.2

    def test_hybrid_progress_with_custom_config(self):
        """Test creating progress with custom configuration."""
        config = ProgressConfig(
            progress_type=ProgressType.DOTS, prefix="🔍 Analysis ", colors=False
        )

        progress = HybridStreamingProgress(config)
        assert progress.config.progress_type == ProgressType.DOTS
        assert progress.config.prefix == "🔍 Analysis "
        assert progress.config.colors is False


@pytest.mark.unit
class TestProgressLifecycle:
    """Test progress indicator lifecycle management."""

    def test_progress_start_and_stop(self):
        """Test basic start and stop functionality."""
        progress = create_spinner_progress("Test Task")

        # Start progress
        progress.start("Starting test")
        assert progress.state == ProgressState.PROGRESS
        assert progress._progress_thread is not None

        # Stop progress
        progress.stop("Test completed")
        assert progress.state == ProgressState.STOPPED

        # Thread should finish
        if progress._progress_thread:
            progress._progress_thread.join(timeout=1.0)
            assert not progress._progress_thread.is_alive()

    def test_progress_complete(self):
        """Test progress completion."""
        progress = create_spinner_progress("Test Task")

        progress.start("Starting test")
        progress.complete("Test completed successfully")

        assert progress.state == ProgressState.COMPLETE

    def test_progress_context_manager(self):
        """Test progress context manager functionality."""
        progress = create_dots_progress("Context Test")

        with progress.progress_context() as ctx:
            assert ctx.state in [ProgressState.PROGRESS, ProgressState.STREAMING]
            ctx.stream_chunk("Test output")

        # Should be completed after context exits
        assert progress.state == ProgressState.COMPLETE


@pytest.mark.unit
class TestProgressStreaming:
    """Test progress streaming functionality."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_stream_chunk(self, mock_stdout):
        """Test streaming chunks to output."""
        progress = create_spinner_progress("Stream Test")

        progress.start("Testing streaming")

        # Stream some content (use end="" to avoid adding extra newlines)
        progress.stream_chunk("Hello ", end="")
        progress.stream_chunk("World!", end="")
        progress.stream_chunk("\n", end="")

        progress.complete("Streaming complete")

        # Verify output was written
        output = mock_stdout.getvalue()
        assert "Hello World!" in output

    def test_streaming_switches_from_progress_mode(self):
        """Test that streaming switches away from progress indicators."""
        progress = create_pulse_progress("Switch Test")

        progress.start("Starting with progress")
        time.sleep(0.1)  # Let progress show briefly

        # Start streaming - should switch modes
        progress.stream_chunk("Streaming content now")

        # Verify we're in streaming mode
        assert progress.state == ProgressState.STREAMING

        progress.complete("Done")


@pytest.mark.unit
class TestProgressErrorHandling:
    """Test error handling in progress indicators."""

    def test_progress_handles_exceptions(self):
        """Test progress handles exceptions gracefully."""
        progress = create_spinner_progress("Error Test")

        progress.start("This will encounter an error")

        # Simulate an exception during operation
        try:
            raise ValueError("Test error")
        except ValueError as e:
            progress.stop(f"Error occurred: {str(e)}")

        assert progress.state == ProgressState.STOPPED

    def test_stop_before_start(self):
        """Test calling stop before start."""
        progress = create_dots_progress("Stop Before Start Test")

        # Should handle gracefully
        progress.stop("Stopping before start")
        assert progress.state == ProgressState.STOPPED

    def test_stream_before_start(self):
        """Test streaming before starting progress."""
        progress = create_spinner_progress("Stream Before Start Test")

        # Should handle gracefully
        progress.stream_chunk("Streaming before start")
        progress.complete("Done")


@pytest.mark.unit
class TestProgressTypes:
    """Test different progress indicator types."""

    def test_dots_progress_behavior(self):
        """Test dots progress specific behavior."""
        progress = create_dots_progress("Dots Test")
        # Customize max_dots after creation
        progress.config.max_dots = 3

        progress.start("Testing dots")
        time.sleep(0.2)  # Let it cycle a bit
        progress.complete("Dots complete")

        assert progress.config.max_dots == 3

    def test_spinner_progress_behavior(self):
        """Test spinner progress specific behavior."""
        progress = create_spinner_progress("Spinner Test")

        # Test with custom spinner characters
        progress.config.spinner_chars = ["|", "/", "-", "\\"]

        progress.start("Testing spinner")
        time.sleep(0.2)  # Let it spin a bit
        progress.complete("Spinner complete")

        assert len(progress.config.spinner_chars) == 4

    def test_bar_progress_behavior(self):
        """Test progress bar specific behavior."""
        progress = create_bar_progress("Bar Test", width=20)

        progress.start("Testing bar")
        time.sleep(0.1)
        progress.complete("Bar complete")

        assert progress.config.width == 20
        assert (
            progress.config.show_elapsed is True
        )  # Bar progress has show_elapsed=True by default

    def test_pulse_progress_behavior(self):
        """Test pulse progress specific behavior."""
        progress = create_pulse_progress("Pulse Test")

        progress.start("Testing pulse")
        time.sleep(0.1)
        progress.complete("Pulse complete")

        assert progress.config.progress_type == ProgressType.PULSE


@pytest.mark.unit
class TestProgressThreadSafety:
    """Test thread safety of progress indicators."""

    def test_concurrent_stream_chunks(self):
        """Test concurrent streaming from multiple threads."""
        progress = create_spinner_progress("Concurrent Test")
        progress.start("Testing concurrent access")

        results = []

        def stream_worker(thread_id: int):
            for i in range(3):
                progress.stream_chunk(f"Thread-{thread_id}-Chunk-{i} ")
                time.sleep(0.01)
            results.append(thread_id)

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=stream_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        progress.complete("Concurrent test complete")

        # All threads should have completed
        assert len(results) == 3

    def test_start_stop_thread_safety(self):
        """Test thread safety of start/stop operations."""
        progress = create_pulse_progress("Thread Safety Test")

        def start_stop_worker():
            progress.start("Worker starting")
            time.sleep(0.05)
            progress.stop("Worker stopping")

        # Multiple threads trying to start/stop
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=start_stop_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should end in a clean state
        assert progress.state == ProgressState.STOPPED


@pytest.mark.unit
class TestProgressIntegrationPatterns:
    """Test common integration patterns with progress indicators."""

    def test_mcp_tool_simulation_pattern(self):
        """Test the MCP tool simulation pattern."""

        def simulate_mcp_operation(query: str) -> Dict[str, Any]:
            progress = create_spinner_progress("🤖 MCP Tool")

            try:
                progress.start("Processing request")

                # Simulate processing
                time.sleep(0.1)

                # Simulate response streaming
                response = f"Mock response to: {query}"
                words = response.split()

                for i, word in enumerate(words):
                    progress.stream_chunk(word + " ")
                    if i % 3 == 0:  # Simulate streaming delay
                        time.sleep(0.01)

                progress.stream_chunk("\n")
                progress.complete("Request processed")

                return {"success": True, "output": response}

            except Exception as e:
                progress.stop(f"Error: {str(e)}")
                return {"success": False, "error": str(e)}

        # Test the pattern
        result = simulate_mcp_operation("test query")

        assert result["success"] is True
        assert "test query" in result["output"]

    def test_async_operation_pattern(self):
        """Test async operation pattern with progress."""

        async def async_operation_with_progress():
            progress = create_bar_progress("Async Operation")

            try:
                progress.start("Starting async work")

                # Simulate async work
                await asyncio.sleep(0.05)

                progress.stream_chunk("Async work completed\n")
                progress.complete("Async operation done")

                return {"success": True}

            except Exception as e:
                progress.stop(f"Async error: {str(e)}")
                return {"success": False, "error": str(e)}

        # Run the async test
        import asyncio

        result = asyncio.run(async_operation_with_progress())

        assert result["success"] is True

    def test_error_recovery_pattern(self):
        """Test error recovery pattern with progress."""

        def operation_with_retry():
            progress = create_dots_progress("Retry Operation")

            for attempt in range(3):
                try:
                    progress.start(f"Attempt {attempt + 1}")

                    # Simulate failure on first two attempts
                    if attempt < 2:
                        raise ConnectionError("Network error")

                    # Success on third attempt
                    progress.stream_chunk("Operation succeeded!\n")
                    progress.complete("Success after retry")

                    return {"success": True, "attempts": attempt + 1}

                except ConnectionError:
                    if attempt < 2:
                        progress.stop(f"Attempt {attempt + 1} failed, retrying...")
                        time.sleep(0.01)
                    else:
                        progress.stop("All attempts failed")
                        return {"success": False, "error": "Max retries exceeded"}

        result = operation_with_retry()
        assert result["success"] is True
        assert result["attempts"] == 3


# Performance and cleanup tests
@pytest.mark.unit
class TestProgressPerformance:
    """Test performance characteristics of progress indicators."""

    def test_minimal_overhead_when_disabled(self):
        """Test that progress has minimal overhead when disabled."""

        def operation_without_progress():
            start_time = time.time()
            time.sleep(0.05)
            return time.time() - start_time

        def operation_with_progress():
            start_time = time.time()
            progress = create_spinner_progress("Performance Test")
            progress.start("Testing")
            time.sleep(0.05)
            progress.complete("Done")
            return time.time() - start_time

        # Measure both
        time_without = operation_without_progress()
        time_with = operation_with_progress()

        # Progress should add minimal overhead (less than 50% increase)
        overhead_ratio = time_with / time_without
        assert (
            overhead_ratio < 1.5
        ), f"Progress overhead too high: {overhead_ratio:.2f}x"

    def test_memory_cleanup(self):
        """Test that progress indicators clean up properly."""
        initial_thread_count = threading.active_count()

        # Create and use multiple progress indicators
        for i in range(5):
            progress = create_pulse_progress(f"Cleanup Test {i}")
            progress.start(f"Operation {i}")
            time.sleep(0.01)
            progress.complete(f"Operation {i} done")

        # Give threads time to clean up
        time.sleep(0.1)

        final_thread_count = threading.active_count()

        # Thread count should return to initial level
        assert (
            final_thread_count <= initial_thread_count + 1
        ), f"Thread leak detected: {initial_thread_count} -> {final_thread_count}"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
