#!/usr/bin/env python3
"""
Integration tests for hybrid progress utility with MCP server functionality.
Tests real integration scenarios and MCP tool patterns.
"""

import threading
import time
from io import StringIO
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from claude_gemini_mcp.helpers.hybrid_progress import (
    HybridStreamingProgress,
    ProgressState,
    create_bar_progress,
    create_pulse_progress,
    create_spinner_progress,
)


@pytest.mark.integration
class TestMCPToolIntegration:
    """Integration tests for MCP tool patterns with progress indicators."""

    def test_gemini_quick_query_simulation(self):
        """Test simulated MCP gemini_quick_query with progress."""

        def mock_gemini_quick_query(query: str) -> Dict[str, Any]:
            progress = create_spinner_progress("🤖 Gemini")

            try:
                progress.start("Processing query")

                # Simulate API processing delay
                time.sleep(0.1)

                # Simulate streaming response
                response = f"Response to: {query}"
                words = response.split()

                for word in words:
                    progress.stream_chunk(word + " ")
                    time.sleep(0.01)  # Simulate streaming delay

                progress.stream_chunk("\n")
                progress.complete("Query processed")

                return {"success": True, "output": response}

            except Exception as e:
                progress.stop(f"Query failed: {str(e)}")
                return {"success": False, "error": str(e)}

        # Test the integration
        result = mock_gemini_quick_query("test query")

        assert result["success"] is True
        assert "test query" in result["output"]

    def test_gemini_analyze_code_simulation(self):
        """Test simulated code analysis MCP tool with progress."""

        def mock_analyze_code(code: str) -> Dict[str, Any]:
            progress = create_pulse_progress("📊 Code Analysis")

            try:
                progress.start("Analyzing code structure")
                time.sleep(0.05)

                # Simulate analysis phases
                progress.config.prefix = "🔍 Security scan "
                time.sleep(0.05)

                progress.config.prefix = "⚡ Performance check "
                time.sleep(0.05)

                # Simulate analysis results
                analysis = f"Analysis complete for {len(code)} characters of code"
                progress.stream_chunk(analysis + "\n")

                progress.complete("Code analysis completed")

                return {"success": True, "output": analysis}

            except Exception as e:
                progress.stop(f"Analysis failed: {str(e)}")
                return {"success": False, "error": str(e)}

        # Test with sample code
        sample_code = "def hello(): return 'world'"
        result = mock_analyze_code(sample_code)

        assert result["success"] is True
        assert "Analysis complete" in result["output"]

    def test_codebase_analysis_simulation(self):
        """Test simulated codebase analysis with progress bar."""

        def mock_codebase_analysis(directory: str) -> Dict[str, Any]:
            progress = create_bar_progress("📈 Codebase Scan", width=20)

            try:
                progress.start("Initializing scan")
                time.sleep(0.05)

                # Simulate analysis phases
                phases = [
                    "🔍 Structure analysis",
                    "🛡️ Security scanning",
                    "⚡ Performance review",
                    "📋 Best practices check",
                ]

                for phase in phases:
                    progress.config.prefix = f"{phase} "
                    time.sleep(0.03)

                # Generate report
                report = f"Codebase analysis for {directory} completed"
                progress.stream_chunk(report + "\n")

                progress.complete("Analysis completed")

                return {"success": True, "output": report}

            except Exception as e:
                progress.stop(f"Analysis failed: {str(e)}")
                return {"success": False, "error": str(e)}

        # Test the integration
        result = mock_codebase_analysis("./test")

        assert result["success"] is True
        assert "analysis for ./test completed" in result["output"]


@pytest.mark.integration
class TestMCPServerIntegration:
    """Integration tests simulating actual MCP server usage patterns."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_mcp_request_response_cycle(self, mock_stdout):
        """Test complete MCP request/response cycle with progress."""

        def simulate_mcp_request_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            """Simulate MCP server handling a request with progress feedback."""
            method = request.get("method", "unknown")
            params = request.get("params", {})

            if method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name == "gemini_quick_query":
                    progress = create_spinner_progress("🤖 Gemini Query")

                    try:
                        progress.start("Processing request")
                        query = arguments.get("query", "")

                        # Simulate processing
                        time.sleep(0.1)

                        # Stream response
                        response = f"AI response for: {query}"
                        progress.stream_chunk(response + "\n")

                        progress.complete("Request completed")

                        return {
                            "content": [{"type": "text", "text": response}],
                            "isError": False,
                        }

                    except Exception as e:
                        progress.stop(f"Request failed: {str(e)}")
                        return {
                            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                            "isError": True,
                        }

            return {
                "content": [{"type": "text", "text": "Unknown method"}],
                "isError": True,
            }

        # Test MCP request simulation
        request = {
            "method": "tools/call",
            "params": {
                "name": "gemini_quick_query",
                "arguments": {"query": "Hello world"},
            },
        }

        response = simulate_mcp_request_handler(request)

        assert response["isError"] is False
        assert "AI response for: Hello world" in response["content"][0]["text"]

        # Verify streaming output occurred
        output = mock_stdout.getvalue()
        assert "AI response for: Hello world" in output

    def test_concurrent_mcp_requests(self):
        """Test handling multiple concurrent MCP requests with progress."""

        def process_request(request_id: int) -> Dict[str, Any]:
            progress = create_pulse_progress(f"🔄 Request {request_id}")

            try:
                progress.start("Processing")
                time.sleep(0.05)  # Simulate work

                result = f"Result for request {request_id}"
                progress.stream_chunk(result + "\n")
                progress.complete("Request completed")

                return {"id": request_id, "success": True, "result": result}

            except Exception as e:
                progress.stop(f"Request {request_id} failed")
                return {"id": request_id, "success": False, "error": str(e)}

        # Process multiple requests concurrently
        results = []
        threads = []

        def worker(req_id):
            result = process_request(req_id)
            results.append(result)

        # Start multiple request threads
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Verify all requests completed successfully
        assert len(results) == 3
        for result in results:
            assert result["success"] is True
            assert "Result for request" in result["result"]

    def test_mcp_error_handling_integration(self):
        """Test MCP server error handling with progress indicators."""

        def failing_mcp_tool(should_fail: bool = True) -> Dict[str, Any]:
            progress = create_spinner_progress("❌ Failing Tool")

            try:
                progress.start("Starting operation")
                time.sleep(0.05)

                if should_fail:
                    raise ConnectionError("Simulated network failure")

                progress.stream_chunk("Success!\n")
                progress.complete("Operation completed")

                return {"success": True}

            except Exception as e:
                progress.stop(f"Tool failed: {str(e)}")
                return {"success": False, "error": str(e)}

        # Test failure case
        result = failing_mcp_tool(should_fail=True)
        assert result["success"] is False
        assert "network failure" in result["error"]

        # Test success case
        result = failing_mcp_tool(should_fail=False)
        assert result["success"] is True


@pytest.mark.integration
class TestProgressStateTransitions:
    """Test progress state transitions in integration scenarios."""

    def test_progress_state_during_mcp_operation(self):
        """Test progress states during a typical MCP operation."""
        progress = create_spinner_progress("🔄 MCP Operation")

        # Initially idle
        assert progress.state == ProgressState.IDLE

        # Start processing
        progress.start("Starting MCP operation")
        assert progress.state == ProgressState.PROGRESS

        # Brief processing time
        time.sleep(0.05)
        assert progress.state == ProgressState.PROGRESS

        # Switch to streaming
        progress.stream_chunk("Operation result")
        assert progress.state == ProgressState.STREAMING

        # Complete operation
        progress.complete("MCP operation completed")
        assert progress.state == ProgressState.COMPLETE

    def test_progress_cleanup_after_mcp_operations(self):
        """Test that progress indicators clean up properly after MCP operations."""
        initial_thread_count = threading.active_count()

        # Run multiple simulated MCP operations
        for i in range(3):
            progress = create_pulse_progress(f"🔧 MCP Op {i}")

            with progress.progress_context():
                time.sleep(0.02)
                progress.stream_chunk(f"Operation {i} result\n")

        # Allow cleanup time
        time.sleep(0.1)

        final_thread_count = threading.active_count()

        # Should not have thread leaks
        assert final_thread_count <= initial_thread_count + 1


@pytest.mark.integration
class TestHybridProgressMCPIntegration:
    """Test hybrid progress utility integration with actual MCP patterns."""

    def test_context_manager_with_mcp_tools(self):
        """Test context manager usage with MCP tool patterns."""

        results = []

        def mcp_tool_with_context(tool_name: str):
            progress = create_bar_progress(f"🛠️ {tool_name}")

            with progress.progress_context("Starting tool") as ctx:
                time.sleep(0.05)  # Simulate tool startup

                # Simulate tool execution
                ctx.stream_chunk(f"{tool_name} executing...\n")
                time.sleep(0.03)

                ctx.stream_chunk(f"{tool_name} completed!\n")
                results.append(f"{tool_name}_success")

        # Test multiple tools
        tools = ["gemini_query", "code_analysis", "file_search"]

        for tool in tools:
            mcp_tool_with_context(tool)

        # All tools should have completed
        assert len(results) == 3
        for tool in tools:
            assert f"{tool}_success" in results

    def test_streaming_output_integration(self):
        """Test streaming output integration with MCP response patterns."""
        captured_output = []

        def capture_stream_chunk(chunk):
            captured_output.append(chunk)

        # Mock streaming to capture output
        progress = create_spinner_progress("📡 Streaming Test")

        # Replace stream_chunk to capture output
        original_stream_chunk = progress.stream_chunk
        progress.stream_chunk = lambda chunk, end="\n": (
            capture_stream_chunk(chunk),
            original_stream_chunk(chunk, end),
        )[1]

        # Simulate MCP streaming response
        progress.start("Generating response")

        response_chunks = [
            "Hello, this is a streaming response from Gemini.",
            "It demonstrates how the hybrid progress utility",
            "smoothly transitions from progress indicators",
            "to actual content streaming.",
        ]

        for chunk in response_chunks:
            progress.stream_chunk(chunk + " ")
            time.sleep(0.01)

        progress.stream_chunk("\n")
        progress.complete("Streaming completed")

        # Verify all chunks were captured
        assert len(captured_output) == len(response_chunks) + 1  # +1 for newline
        for chunk in response_chunks:
            assert any(chunk in output for output in captured_output)


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v"])
