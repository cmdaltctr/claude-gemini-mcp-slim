#!/usr/bin/env python3
"""
Integration example showing how to use the hybrid streaming progress utility
with the existing Gemini MCP server functionality.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Import our hybrid progress utility
from hybrid_progress import (
    HybridStreamingProgress,
    ProgressConfig,
    ProgressType,
    create_bar_progress,
    create_dots_progress,
    create_pulse_progress,
    create_spinner_progress,
)

# Import existing MCP functionality
from gemini_helper import (
    execute_gemini_api,
    execute_gemini_cli,
    execute_gemini_smart,
    get_api_key,
)


class EnhancedGeminiInterface:
    """
    Enhanced Gemini interface that integrates hybrid streaming progress
    with the existing MCP server functionality.
    """

    def __init__(self):
        self.api_key = get_api_key()

    async def query_with_progress(
        self,
        prompt: str,
        task_type: str = "quick_query",
        progress_type: ProgressType = ProgressType.SPINNER,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a Gemini query with hybrid streaming progress feedback.

        Args:
            prompt: The query/prompt to send to Gemini
            task_type: Type of task (quick_query, analyze_code, analyze_codebase)
            progress_type: Type of progress indicator to show
            context: Optional additional context

        Returns:
            Dictionary with success status and output/error
        """
        # Create appropriate progress indicator
        if progress_type == ProgressType.DOTS:
            progress = create_dots_progress("🤖 Gemini")
        elif progress_type == ProgressType.SPINNER:
            progress = create_spinner_progress("🤖 Gemini")
        elif progress_type == ProgressType.PULSE:
            progress = create_pulse_progress("🤖 Gemini")
        else:
            progress = create_bar_progress("🤖 Gemini", width=25)

        try:
            # Start progress indicator
            progress.start("Querying AI model")

            # Add context if provided
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuery: {prompt}"

            # Use the existing smart execution logic
            result = execute_gemini_smart(full_prompt, task_type, show_progress=False)

            if result["success"]:
                # Stream the response in chunks for better UX
                output_text = result["output"]

                # Split response into manageable chunks
                chunks = self._split_into_chunks(output_text)

                for i, chunk in enumerate(chunks):
                    progress.stream_chunk(chunk, end="")
                    # Add small delay to simulate streaming
                    await asyncio.sleep(0.1)

                # Add final newline
                progress.stream_chunk("\n")

                # Complete successfully
                progress.complete("Query completed successfully")
                return result

            else:
                # Handle error
                progress.stop(f"Query failed: {result['error']}")
                return result

        except Exception as e:
            progress.stop(f"Unexpected error: {str(e)}")
            return {"success": False, "error": str(e)}

    def _split_into_chunks(self, text: str, chunk_size: int = 50) -> list:
        """Split text into chunks for streaming effect"""
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            current_chunk.append(word)
            if len(" ".join(current_chunk)) >= chunk_size:
                chunks.append(" ".join(current_chunk) + " ")
                current_chunk = []

        # Add remaining words
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    async def analyze_code_with_progress(
        self, file_path: str, analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze code with enhanced progress feedback showing file reading,
        analysis, and streaming results.
        """
        # Use pulse indicator for code analysis
        progress = create_pulse_progress("📊 Code Analysis")

        try:
            progress.start("Reading code file")
            await asyncio.sleep(0.5)  # Simulate file reading

            # Validate file exists
            if not Path(file_path).exists():
                progress.stop(f"File not found: {file_path}")
                return {"success": False, "error": f"File not found: {file_path}"}

            # Read file content (simplified version of the original logic)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Update progress message
            progress.config.prefix = "🔍 Analyzing "

            # Create analysis prompt
            prompt = f"""Perform a {analysis_type} analysis of this code:

{content[:8000]}  # Limit for demo

Provide comprehensive analysis including:
1. Code structure and organization
2. Security considerations
3. Performance implications
4. Best practices compliance
5. Recommendations for improvements"""

            # Execute analysis
            result = execute_gemini_smart(prompt, "analyze_code", show_progress=False)

            if result["success"]:
                # Stream analysis results
                chunks = self._split_into_chunks(result["output"], chunk_size=60)

                for chunk in chunks:
                    progress.stream_chunk(chunk, end="")
                    await asyncio.sleep(0.15)  # Slightly slower for analysis

                progress.stream_chunk("\n")
                progress.complete(f"Analysis of {Path(file_path).name} completed")
                return result
            else:
                progress.stop(f"Analysis failed: {result['error']}")
                return result

        except Exception as e:
            progress.stop(f"Analysis error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def codebase_analysis_with_progress(
        self, directory_path: str, scope: str = "all"
    ) -> Dict[str, Any]:
        """
        Perform codebase analysis with progress bar showing the comprehensive scan.
        """
        # Use progress bar for codebase analysis (longer operation)
        progress = create_bar_progress("📈 Codebase Scan", width=35)
        progress.config.show_elapsed = True

        try:
            progress.start("Scanning codebase structure")

            # Validate directory
            dir_path = Path(directory_path)
            if not dir_path.exists() or not dir_path.is_dir():
                progress.stop(f"Directory not found: {directory_path}")
                return {
                    "success": False,
                    "error": f"Directory not found: {directory_path}",
                }

            # Simulate directory scanning with progress updates
            await asyncio.sleep(1.0)  # Initial scan
            progress.config.prefix = "🔎 Analyzing patterns "
            await asyncio.sleep(1.0)  # Pattern analysis
            progress.config.prefix = "🛡️ Security review "
            await asyncio.sleep(0.8)  # Security scan
            progress.config.prefix = "⚡ Performance check "
            await asyncio.sleep(0.7)  # Performance analysis

            # Create codebase analysis prompt
            prompt = f"""Analyze this codebase in directory '{dir_path.name}' (scope: {scope}):

Provide comprehensive analysis including:
1. Overall architecture and design patterns
2. Code quality assessment
3. Security considerations
4. Performance implications
5. Best practices adherence
6. Improvement recommendations

Focus on actionable insights."""

            # Execute analysis
            result = execute_gemini_smart(
                prompt, "analyze_codebase", show_progress=False
            )

            if result["success"]:
                # Stream comprehensive results
                chunks = self._split_into_chunks(result["output"], chunk_size=80)

                for chunk in chunks:
                    progress.stream_chunk(chunk, end="")
                    await asyncio.sleep(0.12)

                progress.stream_chunk("\n")
                progress.complete(f"Codebase analysis completed")
                return result
            else:
                progress.stop(f"Codebase analysis failed: {result['error']}")
                return result

        except Exception as e:
            progress.stop(f"Codebase analysis error: {str(e)}")
            return {"success": False, "error": str(e)}


async def demo_enhanced_interface():
    """Demonstrate the enhanced interface with different progress types"""
    print("🚀 Enhanced Gemini MCP Interface with Hybrid Progress Demo\n")

    interface = EnhancedGeminiInterface()

    # Demo 1: Simple query with spinner
    print("=== Demo 1: Quick Query with Spinner ===")
    await interface.query_with_progress(
        "What are the best practices for Python error handling?",
        task_type="quick_query",
        progress_type=ProgressType.SPINNER,
    )

    await asyncio.sleep(1)

    # Demo 2: Code analysis with pulse (if we have a Python file)
    print("\n=== Demo 2: Code Analysis with Pulse ===")
    # Look for a Python file to analyze
    python_files = list(Path(".").glob("*.py"))
    if python_files:
        await interface.analyze_code_with_progress(
            str(python_files[0]),  # Use first Python file found
            analysis_type="security",
        )
    else:
        print("No Python files found for analysis demo")

    await asyncio.sleep(1)

    # Demo 3: Codebase analysis with progress bar
    print("\n=== Demo 3: Codebase Analysis with Progress Bar ===")
    await interface.codebase_analysis_with_progress(
        ".", scope="structure"  # Current directory
    )

    print("\n✅ All demos completed!")


async def demo_different_contexts():
    """Demo showing different usage contexts"""
    print("\n🎯 Different Context Usage Demos\n")

    interface = EnhancedGeminiInterface()

    # Context 1: Development question with dots
    print("=== Context 1: Development Question (Dots) ===")
    await interface.query_with_progress(
        "How can I optimize this Python function for better performance?",
        progress_type=ProgressType.DOTS,
        context="Working on a performance-critical API endpoint",
    )

    await asyncio.sleep(0.5)

    # Context 2: Architecture review with bar
    print("\n=== Context 2: Architecture Review (Bar) ===")
    await interface.query_with_progress(
        "What are the pros and cons of microservices vs monolithic architecture?",
        progress_type=ProgressType.BAR,
        context="Planning system redesign for scalability",
    )


if __name__ == "__main__":
    try:
        # Run the enhanced interface demo
        asyncio.run(demo_enhanced_interface())

        # Run different contexts demo
        asyncio.run(demo_different_contexts())

    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
