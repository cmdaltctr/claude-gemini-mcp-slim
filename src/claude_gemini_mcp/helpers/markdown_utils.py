#!/usr/bin/env python3
"""
Markdown to Text Conversion Utility

This module provides a robust, deterministic markdown-to-text converter that:
- Applies regex replacements in a specific order for consistent results
- Handles nested emphasis, mixed bullets, numbered lists
- Treats tables as plain text lines
- Is idempotent (running multiple times produces same result)
- Performs well on large texts (>10k characters)
- Maintains readability while removing markdown syntax

Architecture: See ADR 003 - Markdown Utilities Implementation
             (../../../PRD/ADR/003-Markdown-Utilities-Implementation.md)
             for design decisions and architectural rationale.
"""

import re


# Convert Markdown text to plain text with deterministic regex processing
def markdown_to_text(markdown: str, preserve_line_breaks: bool = True) -> str:
    """
    Convert Markdown text to plain text with deterministic regex processing.

    This function applies transformations in a specific order to ensure
    consistent, idempotent results. It's optimized for performance and
    handles edge cases like nested emphasis and complex list structures.

    Args:
        markdown (str): The markdown content to convert
        preserve_line_breaks (bool): Whether to preserve line breaks in output

    Returns:
        str: Plain text with markdown syntax removed

    Examples:
        >>> markdown_to_text("# Hello **World**")
        'Hello World'

        >>> markdown_to_text("- Item 1\\n- Item 2")
        'Item 1\\nItem 2'

        >>> markdown_to_text("***bold italic***")
        'bold italic'
    """
    if not isinstance(markdown, str):
        return ""

    if not markdown.strip():
        return ""

    # Work with a copy to ensure idempotency
    text = markdown

    # Phase 1: Code blocks and inline code (highest priority)
    # Remove code blocks first to avoid processing their contents
    text = _remove_code_blocks(text)
    text = _remove_inline_code(text)

    # Phase 2: Links and images (before other processing)
    text = _process_links_and_images(text)

    # Phase 3: Headers (before emphasis to avoid conflicts)
    text = _process_headers(text)

    # Phase 4: Horizontal rules (before emphasis to avoid conflicts)
    text = _process_horizontal_rules(text)

    # Phase 5: Emphasis and formatting (nested processing)
    text = _process_emphasis(text)
    text = _process_strikethrough(text)

    # Phase 6: Lists (complex structures)
    text = _process_lists(text)

    # Phase 7: Tables (treat as plain text)
    text = _process_tables(text)

    # Phase 8: Blockquotes and other block elements
    text = _process_blockquotes(text)

    # Phase 8: Line breaks and whitespace cleanup
    text = _cleanup_whitespace(text, preserve_line_breaks)

    return text.strip()


# Remove fenced code blocks (``` or ~~~) and preserve content as plain text
def _remove_code_blocks(text: str) -> str:
    """Remove fenced code blocks (``` or ~~~) and preserve content as plain text."""
    # Pattern matches opening fence, captures content, matches closing fence
    # Uses non-greedy matching and handles different fence types
    patterns = [
        # Triple backticks with optional language
        r"```[\w]*\n(.*?)\n```",
        # Triple tildes with optional language
        r"~~~[\w]*\n(.*?)\n~~~",
        # Indented code blocks (4+ spaces at line start)
        r"^(?: {4}|\t)(.*)$",
    ]
    # Process patterns in reverse order to avoid partial matches
    for pattern in patterns:
        if pattern.endswith("$"):  # Indented code blocks
            text = re.sub(pattern, r"\1", text, flags=re.MULTILINE)
        else:  # Fenced code blocks
            # Preserve the exact content including indentation
            matches = re.finditer(pattern, text, flags=re.DOTALL)
            for match in reversed(list(matches)):
                text = text[: match.start()] + match.group(1) + text[match.end() :]

    return text


# Remove inline code formatting (`code`) and preserve content
def _remove_inline_code(text: str) -> str:
    """Remove inline code formatting (`code`) and preserve content."""
    # Handle multiple backticks (``code`` or `code`)
    # Process longer sequences first to avoid partial matches
    patterns = [
        r"```([^`]+)```",  # Triple backticks
        r"``([^`]+)``",  # Double backticks
        r"`([^`]+)`",  # Single backticks
    ]
    # Process patterns in reverse order to avoid partial matches
    for pattern in patterns:
        text = re.sub(pattern, r"\1", text)

    return text


# Process links and images, extracting text content
def _process_links_and_images(text: str) -> str:
    """Process links and images, extracting text content."""
    # Images: ![alt](src "title") -> alt text only (process before links)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)

    # Reference-style links: [text][ref]
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)

    # Inline links: [text](url "title")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)

    # Autolinks: <url> -> url
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)

    # Email autolinks: <email@domain.com> -> email@domain.com
    text = re.sub(r"<mailto:([^>]+@[^>]+)>", r"\1", text)
    text = re.sub(r"<([^>]+@[^>]+)>", r"\1", text)

    # Reference definitions: [ref]: url "title" -> remove entirely
    text = re.sub(r"^\s*\[[^\]]+\]:\s+.*$", "", text, flags=re.MULTILINE)

    return text


# Convert headers to plain text, preserving hierarchy with spacing
def _process_headers(text: str) -> str:
    """Convert headers to plain text, preserving hierarchy with spacing."""
    # ATX headers: # Header -> Header
    text = re.sub(r"^#{1,6}\s*(.+?)(?:\s*#+)?$", r"\1", text, flags=re.MULTILINE)

    # Setext headers (underlined with = or -)
    # Header 1: text followed by line of ===
    text = re.sub(r"^(.+)\n=+\s*$", r"\1", text, flags=re.MULTILINE)

    # Header 2: text followed by line of ---
    text = re.sub(r"^(.+)\n-+\s*$", r"\1", text, flags=re.MULTILINE)

    return text


# Process emphasis formatting with proper nested handling
def _process_emphasis(text: str) -> str:
    """
    Process emphasis formatting with proper nested handling.

    Processes in order from most complex to simplest to avoid
    conflicts and ensure proper nesting support.
    """
    # Triple emphasis: ***text*** or ___text___ -> text
    text = re.sub(r"\*{3}(.*?)\*{3}", r"\1", text)
    text = re.sub(r"_{3}(.*?)_{3}", r"\1", text)

    # Double emphasis: **text** or __text__ -> text
    text = re.sub(r"\*{2}(.*?)\*{2}", r"\1", text)
    text = re.sub(r"_{2}(.*?)_{2}", r"\1", text)

    # Single emphasis: *text* or _text_ -> text
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\b_(.*?)_\b", r"\1", text)

    return text


# Remove strikethrough formatting: ~~text~~ -> text
def _process_strikethrough(text: str) -> str:
    """Remove strikethrough formatting: ~~text~~ -> text"""
    return re.sub(r"~~(.*?)~~", r"\1", text)


# Process both ordered and unordered lists
def _process_lists(text: str) -> str:
    """
    Process both ordered and unordered lists.

    Handles mixed list types, nested lists, and preserves content
    while removing list markers.
    """
    lines = text.split("\n")
    processed_lines = []
    # Process lines in reverse order to avoid partial matches
    for line in lines:
        # Task list items: - [ ] or - [x] (check FIRST before unordered lists)
        if re.match(r"^\s*[-*+]\s*\[[x ]\]\s*", line):
            # Remove marker and checkbox
            processed_line = re.sub(r"^\s*[-*+]\s*\[[x ]\]\s*", "", line)
            processed_lines.append(processed_line)

        # Unordered list items: -, *, +
        elif re.match(r"^\s*[-*+]\s+", line):
            # Remove marker and preserve indentation structure
            processed_line = re.sub(r"^\s*[-*+]\s+", "", line)
            processed_lines.append(processed_line)

        # Ordered list items: 1., 2), etc.
        elif re.match(r"^\s*\d+[.)]\s+", line):
            # Remove marker and preserve content
            processed_line = re.sub(r"^\s*\d+[.)]\s+", "", line)
            processed_lines.append(processed_line)

        else:
            processed_lines.append(line)

    return "\n".join(processed_lines)


# Process markdown tables by treating them as plain text lines
def _process_tables(text: str) -> str:
    """
    Process markdown tables by treating them as plain text lines.

    Removes table formatting but preserves content in a readable format.
    """
    lines = text.split("\n")
    processed_lines = []
    in_table = False

    for line in lines:
        # Check if line looks like a table row (contains |)
        if "|" in line and line.strip():
            # Remove leading/trailing |, split by |, clean up cells
            cells = [cell.strip() for cell in line.strip("|").split("|")]

            # Check if it's a header separator (|---|---|)
            if all(
                re.match(r"^:?-+:?$", cell.strip()) for cell in cells if cell.strip()
            ):
                # Skip header separator lines
                in_table = True
                continue

            # Join cells with spaces for readability
            if cells and any(cell.strip() for cell in cells):
                processed_lines.append(" ".join(cell for cell in cells if cell.strip()))
                in_table = True

        else:
            if in_table and not line.strip():
                # Empty line after table
                in_table = False
            processed_lines.append(line)

    return "\n".join(processed_lines)


# Remove blockquote markers (>) and preserve content
def _process_blockquotes(text: str) -> str:
    """Remove blockquote markers (>) and preserve content."""
    # Handle nested blockquotes: >> text -> text
    # Process from most nested to least nested
    while True:
        original_text = text
        text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
        if text == original_text:
            break

    return text


# Remove horizontal rules (---, ***, ___)."""
def _process_horizontal_rules(text: str) -> str:
    """Remove horizontal rules (---, ***, ___)."""
    # Handle horizontal rules - they can have optional spaces
    text = re.sub(r"^\s*-{3,}\s*$", "", text, flags=re.MULTILINE)  # Dashes
    text = re.sub(r"^\s*\*{3,}\s*$", "", text, flags=re.MULTILINE)  # Asterisks
    text = re.sub(r"^\s*_{3,}\s*$", "", text, flags=re.MULTILINE)  # Underscores

    return text


# Clean up whitespace while preserving structure
def _cleanup_whitespace(text: str, preserve_line_breaks: bool) -> str:
    """
    Clean up whitespace while preserving structure.

    Args:
        text: Text to clean up
        preserve_line_breaks: Whether to maintain line break structure
    """
    if preserve_line_breaks:
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Clean up trailing whitespace on lines
        text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)

        # Clean up excessive spaces within lines
        text = re.sub(r"[ \t]+", " ", text)

    else:
        # Replace all line breaks with spaces
        text = re.sub(r"\n+", " ", text)

        # Normalize all whitespace to single spaces
        text = re.sub(r"\s+", " ", text)

    return text


# Test if the markdown_to_text function is idempotent
def is_idempotent(markdown: str, max_iterations: int = 3) -> bool:
    """
    Test if the markdown_to_text function is idempotent.

    Args:
        markdown: The markdown text to test
        max_iterations: Maximum number of iterations to test

    Returns:
        bool: True if function is idempotent, False otherwise
    """
    if not markdown.strip():
        return True

    current = markdown
    for i in range(max_iterations):
        next_result = markdown_to_text(current)
        if i > 0 and next_result == current:
            return True
        current = next_result

    return False


# Performance testing helper
def performance_test(text: str, iterations: int = 100) -> dict:
    """
    Test performance of markdown_to_text function.

    Args:
        text: Text to process
        iterations: Number of iterations to run

    Returns:
        dict: Performance statistics
    """
    import time

    # Record times for each iteration
    times = []
    for _ in range(iterations):
        start_time = time.time()
        markdown_to_text(text)
        end_time = time.time()
        times.append(end_time - start_time)

    return {
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
        "total_time": sum(times),
        "text_length": len(text),
        "iterations": iterations,
    }
