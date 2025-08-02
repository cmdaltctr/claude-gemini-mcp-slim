#!/usr/bin/env python3
"""
Execution Orchestrator Module - Intelligent AI execution coordination.

This module serves as the central orchestration engine for AI execution workflows,
implementing an intelligent API-first, CLI-fallback strategy. It coordinates between
different execution backends, manages result processing, and provides progress
indicators for enhanced user experience.

Core Orchestration Strategy:
1. Model Selection: Uses centralized config for model assignment and nickname resolution
2. Execution Strategy: Attempts API first, gracefully falls back to CLI on failure
3. Result Processing: Optional markdown-to-text conversion with error handling
4. Progress Management: Coordinates progress indicators across different clients
5. Error Propagation: Proper error handling with sanitized user feedback

Key Components:
- Smart Execution Engine: execute_gemini_smart()
- Result Processing Pipeline: _process_result_output()
- Progress-Enhanced Execution: execute_gemini_smart_with_progress()
- Streaming Text Utilities: split_into_chunks()

This module implements the Agentic Collaboration Protocol (ACP) principle of
intelligent orchestration rather than simple pass-through communication.
"""

import asyncio
import sys
import time
from typing import Dict, List

from claude_gemini_mcp.config import get_config
from claude_gemini_mcp.helpers.api_key_manager import get_api_key
from claude_gemini_mcp.helpers.gemini_api_client import execute_gemini_api
from claude_gemini_mcp.helpers.gemini_cli_client import execute_gemini_cli_streaming

# Import availability flags and optional dependencies
try:
    from claude_gemini_mcp.helpers.markdown_utils import markdown_to_text

    MARKDOWN_UTILS_AVAILABLE = True
except ImportError:
    MARKDOWN_UTILS_AVAILABLE = False

try:
    from claude_gemini_mcp.helpers.hybrid_progress import (
        create_spinner_progress,
    )

    PROGRESS_AVAILABLE = True
except ImportError:
    PROGRESS_AVAILABLE = False

# Configuration
cfg = get_config()

# Legacy model configuration for backward compatibility
# This will be replaced by direct calls to cfg.get_model(tool_name)
MODEL_ASSIGNMENTS = {
    "quick_query": "flash",  # Simple Q&A
    "analyze_code": "pro",  # Deep analysis
    "analyze_codebase": "pro",  # Large context
}

# Model nickname mapping for backward compatibility
GEMINI_MODELS = {
    "flash": cfg.get_raw_config()
    .get("models", {})
    .get("nicknames", {})
    .get("flash", "gemini-2.5-flash"),
    "pro": cfg.get_raw_config()
    .get("models", {})
    .get("nicknames", {})
    .get("pro", "gemini-2.5-pro"),
}


def _process_result_output(
    result: Dict, convert_markdown: bool, show_progress: bool
) -> Dict:
    """Process result output through markdown parser if enabled and available.

    This function implements the result processing pipeline, handling optional
    markdown-to-text conversion with proper error handling and user feedback.

    Args:
        result: Result dictionary with 'success' and 'output' keys
        convert_markdown: Whether to convert markdown to plain text
        show_progress: Whether to show progress indicators

    Returns:
        dict: Processed result dictionary with potentially converted output

    Note:
        If markdown conversion fails, the original output is preserved to
        ensure robustness. Progress indicators provide transparency about
        processing steps and any issues encountered.
    """
    if not result["success"] or not result.get("output"):
        return result

    # Skip conversion if disabled or markdown utils not available
    if not convert_markdown or not MARKDOWN_UTILS_AVAILABLE:
        if not convert_markdown and show_progress:
            print("🔧 Markdown conversion bypassed for debugging", file=sys.stderr)
        elif not MARKDOWN_UTILS_AVAILABLE and show_progress:
            print(
                "⚠️ Markdown utils not available, skipping conversion", file=sys.stderr
            )
        return result

    try:
        original_output = result["output"]
        if show_progress:
            print("📝 Converting markdown to plain text...", file=sys.stderr)

        # Convert markdown to plain text
        converted_output = markdown_to_text(original_output)

        # Update result with converted output
        result["output"] = converted_output

        if show_progress:
            original_len = len(original_output)
            converted_len = len(converted_output)
            print(
                f"✅ Markdown conversion complete: {original_len} → {converted_len} chars",
                file=sys.stderr,
            )

    except Exception as e:
        if show_progress:
            print(
                f"⚠️ Markdown conversion failed: {str(e)}, using original output",
                file=sys.stderr,
            )
        # Keep original output if conversion fails

    return result


async def execute_gemini_smart(
    prompt: str,
    task_type: str = "quick_query",
    show_progress: bool = True,
    convert_markdown: bool = True,
) -> Dict:
    """Smart execution: try API first, fall back to CLI if needed.

    This is the central orchestration function implementing intelligent execution
    strategy. It attempts API execution first for optimal performance, then
    gracefully falls back to CLI execution if the API is unavailable or fails.

    Orchestration Strategy:
    1. Model Resolution: Uses centralized config with backward compatibility
    2. API Availability Check: Verifies API key presence before attempting API call
    3. Primary Execution: Attempts API execution with full error handling
    4. Fallback Strategy: Falls back to CLI execution on API failure
    5. Result Processing: Applies markdown conversion pipeline to final output

    Args:
        prompt: Input prompt for the AI model
        task_type: Type of task for model selection (quick_query, analyze_code, etc.)
        show_progress: Whether to show progress indicators during execution
        convert_markdown: Whether to convert markdown output to plain text (default: True)

    Returns:
        dict: Execution result with 'success' boolean and 'output'/'error' content

    Note:
        This function embodies the Agentic Collaboration Protocol principle by
        intelligently orchestrating the execution workflow rather than simply
        passing requests through to backends.
    """
    # Model selection with centralized configuration
    model_name = cfg.get_model(task_type, None)
    if not model_name:
        # Fallback to legacy logic for backward compatibility
        model_type = MODEL_ASSIGNMENTS.get(task_type, "flash")
        model_name = GEMINI_MODELS[model_type]

    # Resolve nickname if it matches legacy pattern
    if model_name in GEMINI_MODELS:
        model_name = GEMINI_MODELS[model_name]

    if show_progress:
        print(f"📝 Task: {task_type}", file=sys.stderr)
        print(f"🤖 Selected model: {model_name}", file=sys.stderr)

    # Primary execution strategy: API first
    api_key = get_api_key()
    if api_key:
        if show_progress:
            print("🚀 API key found, attempting API call...", file=sys.stderr)

        result = await execute_gemini_api(prompt, model_name, show_progress)
        if result["success"]:
            # Process successful API result through the pipeline
            result = _process_result_output(result, convert_markdown, show_progress)
            return result

        if show_progress:
            print("🔄 API failed, falling back to CLI...", file=sys.stderr)
    else:
        if show_progress:
            print(
                "📝 No API key found in any location, using CLI directly",
                file=sys.stderr,
            )

    # Fallback execution strategy: CLI
    result = await execute_gemini_cli_streaming(prompt, model_name, show_progress)

    # Process CLI result through the pipeline
    result = _process_result_output(result, convert_markdown, show_progress)
    return result


def split_into_chunks(text: str, chunk_size: int = 50) -> List[str]:
    """Split text into chunks for streaming display.

    This utility function enables smooth streaming display of AI responses by
    breaking text into appropriately-sized chunks. It respects word boundaries
    to maintain readability while ensuring chunks don't exceed the specified size.

    Args:
        text: Input text to be chunked
        chunk_size: Maximum characters per chunk (default: 50)

    Returns:
        list[str]: List of text chunks, each respecting word boundaries

    Note:
        This function is used by the progress-enhanced execution to provide
        a smooth streaming experience for users viewing AI responses.
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        # Start new chunk if adding this word would exceed limit
        if current_length + len(word) + 1 > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1

    # Add final chunk if any words remain
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def execute_gemini_smart_with_progress(
    prompt: str, task_type: str = "quick_query"
) -> Dict:
    """Execute Gemini with beautiful streaming progress indicators.

    This function provides an enhanced user experience by combining smart
    execution with sophisticated progress indicators and streaming output display.
    It leverages the hybrid progress system to show spinners, streaming text,
    and completion status.

    Progress Flow:
    1. Initialize spinner progress indicator
    2. Execute smart orchestration (API-first, CLI-fallback)
    3. Stream successful results in chunks for smooth display
    4. Show completion status or error information

    Args:
        prompt: Input prompt for the AI model
        task_type: Type of task for model selection

    Returns:
        dict: Execution result with 'success' boolean and 'output'/'error' content

    Note:
        If progress utilities are not available, falls back to standard smart
        execution with basic progress indicators.
    """
    # Fallback to standard execution if progress utilities unavailable
    if not PROGRESS_AVAILABLE:
        return asyncio.run(execute_gemini_smart(prompt, task_type, show_progress=True))

    # Initialize progress indicator
    progress = create_spinner_progress("🤖 Gemini")

    try:
        progress.start("Processing request")

        # Execute smart orchestration without built-in progress (we handle it here)
        result = asyncio.run(
            execute_gemini_smart(prompt, task_type, show_progress=False)
        )

        if result["success"]:
            # Stream response in chunks for smooth display experience
            chunks = split_into_chunks(result["output"], chunk_size=60)
            for chunk in chunks:
                progress.stream_chunk(chunk + " ", end="")
                time.sleep(0.05)  # Small delay for nice streaming effect

            progress.stream_chunk("\n")
            progress.complete("Request completed")
        else:
            progress.stop(f"Error: {result['error']}")

        return result

    except Exception as e:
        progress.stop(f"Unexpected error: {str(e)}")
        return {"success": False, "error": str(e)}


# Public API exports
__all__ = [
    "execute_gemini_smart",
    "execute_gemini_smart_with_progress",
    "split_into_chunks",
]
