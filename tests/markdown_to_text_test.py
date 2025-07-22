#!/usr/bin/env python3
"""
Pytest Test Suite for Markdown to Text Conversion

This test suite covers all critical functionality for the markdown_to_text function:
- Headers (ATX and Setext styles)
- Bullets and ordered lists (including mixed and nested)
- Emphasis (bold, italic, nested combinations)
- Links (inline, reference, autolinks)
- Code blocks (fenced and indented)
- Mixed content scenarios
- Edge cases and performance requirements

Tests are designed to be comprehensive, maintainable, and integrate with CI/CD pre-commit hooks.

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-20
"""

import time
from typing import Any, Dict, List

import pytest

from claude_gemini_mcp.helpers.markdown_utils import is_idempotent, markdown_to_text, performance_test


class TestMarkdownToText:
    """
    Comprehensive pytest test suite for markdown_to_text functionality.

    This test class is organized by functionality area and includes:
    - Individual component tests
    - Integration tests for mixed content
    - Edge cases and boundary conditions
    - Performance benchmarks
    """

    # HEADERS TESTING
    @pytest.mark.unit
    def test_atx_headers(self):
        """Test ATX-style headers (# Header)."""
        test_cases = [
            ("# Level 1 Header", "Level 1 Header"),
            ("## Level 2 Header", "Level 2 Header"),
            ("### Level 3 Header", "Level 3 Header"),
            ("#### Level 4 Header", "Level 4 Header"),
            ("##### Level 5 Header", "Level 5 Header"),
            ("###### Level 6 Header", "Level 6 Header"),
            ("# Header with closing hashes #", "Header with closing hashes"),
            ("##   Spaced Header   ##", "Spaced Header"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"ATX header test failed: {markdown_input} -> {result} != {expected}"

    @pytest.mark.unit
    def test_setext_headers(self):
        """Test Setext-style headers (underlined with = or -)."""
        test_cases = [
            ("Header 1\n========", "Header 1"),
            ("Header 2\n--------", "Header 2"),
            ("Another H1\n===", "Another H1"),
            ("Another H2\n---", "Another H2"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result.strip() == expected
            ), f"Setext header test failed: {markdown_input} -> {result} != {expected}"

    @pytest.mark.unit
    def test_headers_with_emphasis(self):
        """Test headers containing emphasis markup."""
        test_cases = [
            ("# **Bold Header**", "Bold Header"),
            ("## *Italic Header*", "Italic Header"),
            ("### ***Bold Italic Header***", "Bold Italic Header"),
            ("#### Header with `code` element", "Header with code element"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"Header with emphasis test failed: {markdown_input}"

    # BULLETS AND LISTS TESTING

    @pytest.mark.unit
    def test_unordered_lists(self):
        """Test unordered list processing with various bullet styles."""
        bullet_styles = [
            "- First item\n- Second item\n- Third item",
            "* First item\n* Second item\n* Third item",
            "+ First item\n+ Second item\n+ Third item",
        ]

        expected = "First item\nSecond item\nThird item"

        for bullet_list in bullet_styles:
            result = markdown_to_text(bullet_list)
            assert (
                result.strip() == expected
            ), f"Unordered list test failed: {bullet_list}"

    @pytest.mark.unit
    def test_ordered_lists(self):
        """Test ordered list processing with various numbering styles."""
        test_cases = [
            (
                "1. First item\n2. Second item\n3. Third item",
                "First item\nSecond item\nThird item",
            ),
            (
                "1) First item\n2) Second item\n3) Third item",
                "First item\nSecond item\nThird item",
            ),
            ("10. Tenth item\n11. Eleventh item", "Tenth item\nEleventh item"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result.strip() == expected
            ), f"Ordered list test failed: {markdown_input}"

    @pytest.mark.unit
    def test_mixed_list_types(self):
        """Test processing of mixed bullet and numbered lists."""
        mixed_list = """- Bullet item 1
* Bullet item 2
+ Bullet item 3
1. Numbered item 1
2. Numbered item 2
3) Alternative numbered item
- [ ] Unchecked task
- [x] Checked task"""

        expected_lines = [
            "Bullet item 1",
            "Bullet item 2",
            "Bullet item 3",
            "Numbered item 1",
            "Numbered item 2",
            "Alternative numbered item",
            "Unchecked task",
            "Checked task",
        ]

        result = markdown_to_text(mixed_list)
        result_lines = [line.strip() for line in result.split("\n") if line.strip()]

        assert result_lines == expected_lines, f"Mixed list test failed: {result_lines}"

    @pytest.mark.unit
    def test_nested_lists(self):
        """Test nested list structures with proper indentation handling."""
        nested_list = """- Top level item 1
  - Nested item 1.1
    - Deep nested item 1.1.1
  - Nested item 1.2
- Top level item 2
1. Numbered top level
   1. Nested numbered 1
   2. Nested numbered 2"""

        result = markdown_to_text(nested_list)

        # Should contain all items without bullet markers
        assert "Top level item 1" in result
        assert "Nested item 1.1" in result
        assert "Deep nested item 1.1.1" in result
        assert "Numbered top level" in result

        # Should not contain markdown markers
        assert "-" not in result or not result.strip().startswith("-")
        assert "1." not in result or not any(
            line.strip().startswith("1.") for line in result.split("\n")
        )

    # EMPHASIS TESTING
    @pytest.mark.unit
    def test_basic_emphasis(self):
        """Test basic emphasis formatting (bold, italic)."""
        test_cases = [
            ("**bold text**", "bold text"),
            ("__bold text__", "bold text"),
            ("*italic text*", "italic text"),
            ("_italic text_", "italic text"),
            ("~~strikethrough~~", "strikethrough"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"Basic emphasis test failed: {markdown_input} -> {result}"

    @pytest.mark.unit
    def test_nested_emphasis(self):
        """Test nested emphasis combinations - critical edge case."""
        test_cases = [
            ("***bold italic***", "bold italic"),
            ("___bold italic___", "bold italic"),
            ("**bold with *nested italic***", "bold with nested italic"),
            ("*italic with **nested bold***", "italic with nested bold"),
            ("***really **complex** nesting***", "really complex nesting"),
            ("**bold _with_ underline emphasis**", "bold with underline emphasis"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"Nested emphasis test failed: {markdown_input} -> {result}"

    @pytest.mark.unit
    def test_emphasis_edge_cases(self):
        """Test emphasis edge cases and boundary conditions."""
        test_cases = [
            # Emphasis at word boundaries
            ("word *emphasized* word", "word emphasized word"),
            ("start**bold**end", "startboldend"),
            # Multiple emphasis in one line
            ("**bold** and *italic* and ~~strike~~", "bold and italic and strike"),
            # Emphasis with punctuation
            ("**bold!** and *italic?*", "bold! and italic?"),
            # Mixed emphasis styles
            ("*italic* and **bold** and ***both***", "italic and bold and both"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"Emphasis edge case failed: {markdown_input} -> {result}"

    # LINKS TESTING
    @pytest.mark.unit
    def test_inline_links(self):
        """Test inline link processing [text](url)."""
        test_cases = [
            ("[link text](http://example.com)", "link text"),
            ("[Google](https://google.com)", "Google"),
            ('[link with title](http://example.com "Title")', "link with title"),
            ("[](http://example.com)", ""),  # Empty link text
            ("[multi word link](http://example.com)", "multi word link"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"Inline link test failed: {markdown_input} -> {result}"

    @pytest.mark.unit
    def test_reference_links(self):
        """Test reference-style links [text][ref]."""
        reference_markdown = """Check out [Google][1] and [GitHub][gh].

[1]: https://google.com
[gh]: https://github.com "GitHub Homepage\""""

        result = markdown_to_text(reference_markdown)

        assert "Check out Google and GitHub." in result
        # Reference definitions should be removed
        assert "[1]:" not in result
        assert "[gh]:" not in result
        assert "https://google.com" not in result

    @pytest.mark.unit
    def test_autolinks(self):
        """Test automatic link detection <url>."""
        test_cases = [
            ("<http://example.com>", "http://example.com"),
            ("<https://github.com>", "https://github.com"),
            ("<mailto:test@example.com>", "test@example.com"),
            ("<user@domain.org>", "user@domain.org"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"Autolink test failed: {markdown_input} -> {result}"

    @pytest.mark.unit
    def test_images(self):
        """Test image processing ![alt](src)."""
        test_cases = [
            ("![alt text](image.jpg)", "alt text"),
            ("![](image.png)", ""),  # Empty alt text
            ('![Image with title](img.jpg "Title")', "Image with title"),
            ("![Multi word alt](picture.gif)", "Multi word alt"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"Image test failed: {markdown_input} -> {result}"

    # CODE BLOCKS TESTING
    @pytest.mark.unit
    def test_fenced_code_blocks(self):
        """Test fenced code block processing."""
        test_cases = [
            ("```\ncode line 1\ncode line 2\n```", "code line 1\ncode line 2"),
            (
                "```python\ndef hello():\n    print('world')\n```",
                "def hello():\nprint('world')",
            ),
            ("~~~\ncode with tildes\n~~~", "code with tildes"),
            ("```javascript\nconst x = 1;\n```", "const x = 1;"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result.strip() == expected
            ), f"Fenced code block test failed: {markdown_input}"

    @pytest.mark.unit
    def test_inline_code(self):
        """Test inline code processing `code`."""
        test_cases = [
            ("Use the `print()` function", "Use the print() function"),
            ("Code `var x = 1` in sentence", "Code var x = 1 in sentence"),
            ("``code with backticks``", "code with backticks"),
            ("```triple backticks```", "triple backticks"),
            (
                "Multiple `code1` and `code2` elements",
                "Multiple code1 and code2 elements",
            ),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"Inline code test failed: {markdown_input} -> {result}"

    @pytest.mark.unit
    def test_indented_code_blocks(self):
        """Test indented code blocks (4 spaces)."""
        indented_code = """Regular paragraph.

    def function():
        return "indented code"

    Another code line

Regular paragraph continues."""

        result = markdown_to_text(indented_code)

        # Code content should be preserved
        assert "def function():" in result
        assert 'return "indented code"' in result
        assert "Another code line" in result

        # Regular paragraphs should be preserved
        assert "Regular paragraph." in result
        assert "Regular paragraph continues." in result

    # MIXED CONTENT TESTING
    @pytest.mark.integration
    def test_comprehensive_mixed_content(self):
        """Test complex document with all markdown elements mixed together."""
        complex_document = """# Main Document Title

This document contains **bold text**, *italic text*, and ***bold italic text***.

## Features List

- **Bold bullet** with [link](http://example.com)
- *Italic bullet* with `inline code`
- Regular bullet with ~~strikethrough~~

### Numbered Features

1. First feature with **emphasis**
2. Second feature with [external link](https://github.com)
3. Third feature with `code element`

> This is a blockquote with **bold text** and *italic text*.
> It spans multiple lines and includes a [link](http://example.com).

Here's some code:

```python
def process_markdown(text):
    return markdown_to_text(text)
```

| Feature | Status | Priority |
|---------|--------|----------|
| **Bold** | ✓ Complete | *High* |
| Links | ✓ Complete | Medium |
| `Code` | ✓ Complete | High |

Final paragraph with ![image](test.jpg) and <http://autolink.com>.

---

© 2025 Test Document"""

        result = markdown_to_text(complex_document)

        # Verify all content types are processed correctly
        assert "Main Document Title" in result
        assert "Bold bullet with link" in result
        assert "def process_markdown(text):" in result
        assert "Feature Status Priority" in result  # Table headers
        assert "Bold ✓ Complete High" in result  # Table content
        assert "http://autolink.com" in result
        assert "© 2025 Test Document" in result

        # Verify markdown syntax is removed
        assert "**" not in result
        assert "##" not in result
        assert "```" not in result
        assert "|" not in result or result.count("|") < 3  # Minimal table separators
        assert "[" not in result or "](" not in result  # Links removed

    @pytest.mark.integration
    def test_nested_mixed_content(self):
        """Test deeply nested mixed content scenarios."""
        nested_content = """# Document with Nested Elements

- **Bold item** with [link to *italic* content](http://example.com)
- List item with `code containing **bold** text`
- > Blockquote **inside** list item with ***emphasis***

1. **Numbered** item with ![image alt *text*](img.jpg)
2. Item with code block:
   ```
   // Code with **markdown** (should not process)
   function test() { return "value"; }
   ```

> **Bold blockquote** with:
> - Nested list in blockquote
> - Another nested item with *emphasis*
> - `Code in blockquote`"""

        result = markdown_to_text(nested_content)

        # Content should be preserved
        assert "Document with Nested Elements" in result
        assert "Bold item with link to italic content" in result
        assert "Code with markdown" in result  # Code content preserved literally
        assert "Bold blockquote with:" in result
        assert "Nested list in blockquote" in result

        # Markdown syntax should be removed
        assert "**" not in result
        assert "*italic*" not in result
        assert "[" not in result or "](" not in result

    # EDGE CASES AND BOUNDARY CONDITIONS
    @pytest.mark.unit
    def test_empty_and_whitespace(self):
        """Test empty inputs and whitespace-only content."""
        test_cases = [
            ("", ""),
            ("   ", ""),
            ("\n\n\n", ""),
            ("   \n   \n   ", ""),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result == expected
            ), f"Empty/whitespace test failed: '{markdown_input}' -> '{result}'"

    @pytest.mark.unit
    def test_invalid_input_types(self):
        """Test handling of invalid input types."""
        invalid_inputs = [None, 123, [], {}, object()]

        for invalid_input in invalid_inputs:
            result = markdown_to_text(invalid_input)
            assert (
                result == ""
            ), f"Invalid input should return empty string: {type(invalid_input)}"

    @pytest.mark.unit
    def test_malformed_markdown(self):
        """Test handling of malformed markdown syntax."""
        malformed_cases = [
            "**unclosed bold",
            "*unclosed italic",
            "[unclosed link",
            "![unclosed image",
            "```unclosed code block",
            "# Header with unclosed **bold",
            "- List item with [unclosed link and *unclosed italic*",
        ]

        for malformed in malformed_cases:
            result = markdown_to_text(malformed)
            # Should not crash and should return some reasonable result
            assert isinstance(
                result, str
            ), f"Should return string for malformed input: {malformed}"
            assert len(result) >= 0, f"Should return non-negative length: {malformed}"

    @pytest.mark.unit
    def test_unicode_and_special_chars(self):
        """Test handling of unicode and special characters."""
        unicode_content = """# Héâdér with Ümläüts

- **Bôld tëxt** with spéciål characters
- Emoji content 🎉 🚀 ✨
- Smart quotes "curly" and 'apostrophes'
- Mathematical symbols: α β γ ∑ ∞
- Currency: $100 €50 ¥1000

[Ünïcödé link](http://example.com/pàth?query=tést)"""

        result = markdown_to_text(unicode_content)

        # Unicode should be preserved
        assert "Héâdér with Ümläüts" in result
        assert "Bôld tëxt with spéciål characters" in result
        assert "🎉 🚀 ✨" in result
        assert "α β γ ∑ ∞" in result
        assert "Ünïcödé link" in result

        # Markdown should be removed
        assert "**" not in result
        assert "[" not in result or "](" not in result

    # PERFORMANCE TESTING
    @pytest.mark.performance
    def test_large_document_performance(self):
        """Test performance with large documents (>10k characters)."""
        # Generate a large document
        sections = []
        for i in range(200):  # Create 200 sections
            section = f"""## Section {i}

**Bold text** and *italic text* in section {i}.

### Subsection {i}.1

- Bullet item {i}.1
- Bullet item {i}.2 with [link](http://example.com/section{i})
- Bullet item {i}.3 with `code_{i}`

1. Numbered item {i}.1
2. Numbered item {i}.2
3. Numbered item {i}.3

> Blockquote in section {i} with **emphasis**.

```python
def function_{i}():
    return f"Section {i} processing"
```

| Col A | Col B | Col C |
|-------|-------|-------|
| Data {i}.1 | Data {i}.2 | Data {i}.3 |

---

"""
            sections.append(section)

        large_document = "\n".join(sections)

        # Verify it's actually large
        assert (
            len(large_document) > 10000
        ), f"Document should be >10k chars, got {len(large_document)}"

        # Test processing time
        start_time = time.time()
        result = markdown_to_text(large_document)
        processing_time = time.time() - start_time

        # Performance assertion - should process in reasonable time
        assert (
            processing_time < 10.0
        ), f"Processing took {processing_time:.2f}s, should be <10s"

        # Verify result quality
        assert len(result) > 5000, "Result should contain substantial content"
        assert (
            "Section 0" in result and "Section 199" in result
        ), "Should contain first and last sections"
        assert "**" not in result, "Should remove all markdown syntax"

        # Test with performance helper
        perf_stats = performance_test(large_document[:5000], iterations=5)
        assert (
            perf_stats["avg_time"] < 2.0
        ), f"Average time {perf_stats['avg_time']:.3f}s should be <2s"

    @pytest.mark.performance
    def test_idempotency_verification(self):
        """Test that the function is truly idempotent."""
        test_documents = [
            "# Simple **bold** header",
            "- **Bold** list\n- *Italic* list\n- `Code` list",
            """***Complex*** document with:
- [Links](http://example.com)
- ![Images](img.jpg)
- `inline code`
- ```
  code blocks
  ```
- > **Bold** blockquotes""",
            """| **Table** | *With* | `Formatting` |
|-----------|--------|--------------|
| **Cell1** | *Cell2* | `Cell3` |""",
        ]

        for doc in test_documents:
            # Test helper function
            assert is_idempotent(doc), f"Document failed idempotency test: {doc}"

            # Manual verification
            first_pass = markdown_to_text(doc)
            second_pass = markdown_to_text(first_pass)
            third_pass = markdown_to_text(second_pass)

            assert (
                second_pass == third_pass
            ), f"Not idempotent: {doc} -> {first_pass} -> {second_pass} -> {third_pass}"

    # WHITESPACE AND FORMATTING TESTS
    @pytest.mark.unit
    def test_preserve_line_breaks_option(self):
        """Test preserve_line_breaks parameter functionality."""
        multiline_content = """Line 1


Line 4

Line 6"""

        # With line breaks preserved (default)
        result_preserved = markdown_to_text(
            multiline_content, preserve_line_breaks=True
        )
        assert "\n" in result_preserved, "Should preserve line breaks"
        assert result_preserved.count("\n") <= multiline_content.count(
            "\n"
        ), "Should not add extra line breaks"

        # Without line breaks preserved
        result_flat = markdown_to_text(multiline_content, preserve_line_breaks=False)
        assert "\n" not in result_flat, "Should not contain line breaks"
        assert (
            result_flat == "Line 1 Line 4 Line 6"
        ), f"Should be flattened: {result_flat}"

    @pytest.mark.unit
    def test_whitespace_cleanup(self):
        """Test proper whitespace normalization."""
        # Multiple spaces
        assert (
            markdown_to_text("Text    with    multiple     spaces")
            == "Text with multiple spaces"
        )

        # Tabs and mixed whitespace
        assert (
            markdown_to_text("Text\t\twith\ttabs   and  spaces")
            == "Text with tabs and spaces"
        )

        # Leading/trailing whitespace
        assert markdown_to_text("   Text with padding   ") == "Text with padding"

        # Multiple newlines should be reduced
        text_with_newlines = "Line 1\n\n\n\nLine 2"
        result = markdown_to_text(text_with_newlines)
        assert result.count("\n\n\n") == 0, "Should not have 3+ consecutive newlines"

    # REGRESSION TESTS
    @pytest.mark.unit
    def test_table_processing(self):
        """Test comprehensive table processing scenarios."""
        # Basic table
        basic_table = """| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |"""

        result = markdown_to_text(basic_table)
        expected_lines = [
            "Header 1 Header 2 Header 3",
            "Cell 1 Cell 2 Cell 3",
            "Cell 4 Cell 5 Cell 6",
        ]

        for expected_line in expected_lines:
            assert (
                expected_line in result
            ), f"Table processing failed for: {expected_line}"

        # Table with alignment
        aligned_table = """| Left | Center | Right |
|:-----|:------:|------:|
| L1   |   C1   |    R1 |"""

        result = markdown_to_text(aligned_table)
        assert "Left Center Right" in result
        assert "L1 C1 R1" in result

    @pytest.mark.unit
    def test_blockquote_processing(self):
        """Test blockquote processing with various nesting levels."""
        test_cases = [
            ("> Simple quote", "Simple quote"),
            ("> Multi line\n> quote here", "Multi line\nquote here"),
            ("> > Nested quote", "Nested quote"),
            ("> Quote with **bold** text", "Quote with bold text"),
        ]

        for markdown_input, expected in test_cases:
            result = markdown_to_text(markdown_input)
            assert (
                result.strip() == expected
            ), f"Blockquote test failed: {markdown_input} -> {result}"

    # INTEGRATION WITH CI/CD MARKERS
    @pytest.mark.integration
    def test_ci_integration_markers(self):
        """Test cases specifically designed for CI/CD pipeline validation."""
        # This test ensures the test suite works properly in CI environments

        # Test deterministic behavior - critical for CI
        sample_doc = "# Test **Document** with [link](http://example.com)"
        results = [markdown_to_text(sample_doc) for _ in range(5)]

        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert (
                result == first_result
            ), f"Non-deterministic behavior detected in run {i}"

        # Test memory efficiency - important for CI resource constraints
        import sys

        initial_size = sys.getsizeof(sample_doc)
        result_size = sys.getsizeof(markdown_to_text(sample_doc))

        # Result shouldn't be dramatically larger than input (reasonable overhead)
        assert (
            result_size <= initial_size * 3
        ), f"Result size {result_size} too large vs input {initial_size}"


# PYTEST CONFIGURATION AND FIXTURES
@pytest.fixture
def sample_markdown_documents():
    """Provide sample markdown documents for testing."""
    return {
        "simple": "# Header\n\n**Bold** text with [link](http://example.com).",
        "complex": """# Main Title

## Features
- **Feature 1** with `code`
- Feature 2 with [external link](https://github.com)

```python
def example():
    return "test"
```

| Column | Value |
|--------|-------|
| Test   | Data  |""",
        "mixed_lists": """- Unordered item 1
- Unordered item 2
1. Ordered item 1
2. Ordered item 2
- [x] Completed task
- [ ] Pending task""",
        "emphasis_heavy": "***Triple*** **double** *single* ~~strike~~ text",
        "unicode": "Héllo **Wörld** with émöji 🎉",
    }


@pytest.fixture
def performance_content():
    """Generate content for performance testing."""
    content_blocks = []
    for i in range(50):
        block = f"""## Section {i}
**Bold paragraph {i}** with *italic* and `code`.
- List item {i}.1 with [link](http://example.com/{i})
- List item {i}.2 with ![image](img{i}.jpg)

```javascript
function test{i}() {{
    return "performance test {i}";
}}
```

| Test | Data | Value |
|------|------|-------|
| {i}  | Item | Score |
"""
        content_blocks.append(block)

    return "\n".join(content_blocks)


# HELPER FUNCTIONS FOR TESTING
def assert_no_markdown_syntax(text: str) -> None:
    """Assert that text contains no markdown syntax markers."""
    forbidden_patterns = [
        "**",
        "*",
        "__",
        "_",
        "~~",
        "```",
        "`",
        "#",
        "- ",
        "+ ",
        "1. ",
        "2. ",
        "> ",
        "[",
        "](",
        "![",
        "|",
    ]

    for pattern in forbidden_patterns:
        assert (
            pattern not in text or text.count(pattern) == 0
        ), f"Found markdown syntax: {pattern} in {text[:100]}..."


def assert_content_preserved(
    original: str, processed: str, key_phrases: List[str]
) -> None:
    """Assert that key content phrases are preserved after processing."""
    for phrase in key_phrases:
        assert phrase in processed, f"Key phrase '{phrase}' not found in processed text"


# PARAMETERIZED TESTS FOR COMPREHENSIVE COVERAGE
@pytest.mark.parametrize(
    "header_level,marker",
    [(1, "#"), (2, "##"), (3, "###"), (4, "####"), (5, "#####"), (6, "######")],
)
def test_all_header_levels(header_level, marker):
    """Parameterized test for all header levels."""
    header_text = f"Header Level {header_level}"
    markdown_input = f"{marker} {header_text}"
    result = markdown_to_text(markdown_input)
    assert result == header_text


@pytest.mark.parametrize(
    "emphasis_type,marker,expected",
    [
        ("bold", "**text**", "text"),
        ("bold_alt", "__text__", "text"),
        ("italic", "*text*", "text"),
        ("italic_alt", "_text_", "text"),
        ("triple", "***text***", "text"),
        ("strikethrough", "~~text~~", "text"),
    ],
)
def test_all_emphasis_types(emphasis_type, marker, expected):
    """Parameterized test for all emphasis types."""
    result = markdown_to_text(marker)
    assert result == expected


@pytest.mark.parametrize("list_marker", ["-", "*", "+", "1.", "2)", "10."])
def test_all_list_markers(list_marker):
    """Parameterized test for all list marker types."""
    list_item = f"{list_marker} List item text"
    result = markdown_to_text(list_item)
    assert "List item text" in result
    assert list_marker not in result


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v", "--tb=short"])
