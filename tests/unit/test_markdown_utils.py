#!/usr/bin/env python3
"""
Unit tests for markdown_to_text function.

Tests cover all specified requirements:
- Deterministic order of regex replacements
- Nested emphasis handling
- Mixed bullets and numbered lists
- Tables treated as plain lines
- Idempotency testing
- Performance with >10k character texts
- Edge cases and boundary conditions
"""

import time
import unittest

from helpers.markdown_utils import is_idempotent, markdown_to_text, performance_test


class TestMarkdownToText(unittest.TestCase):
    """Test suite for markdown_to_text function."""

    def test_basic_functionality(self):
        """Test basic markdown conversion."""
        # Headers
        self.assertEqual(markdown_to_text("# Header 1"), "Header 1")
        self.assertEqual(markdown_to_text("## Header 2"), "Header 2")
        self.assertEqual(markdown_to_text("### Header 3 ###"), "Header 3")

        # Basic emphasis
        self.assertEqual(markdown_to_text("**bold**"), "bold")
        self.assertEqual(markdown_to_text("*italic*"), "italic")
        self.assertEqual(markdown_to_text("_italic_"), "italic")

        # Links
        self.assertEqual(
            markdown_to_text("[link text](http://example.com)"), "link text"
        )
        self.assertEqual(markdown_to_text("![image alt](image.jpg)"), "image alt")

    def test_nested_emphasis(self):
        """Test nested emphasis handling - critical edge case."""
        # Triple emphasis (bold + italic)
        self.assertEqual(markdown_to_text("***bold italic***"), "bold italic")
        self.assertEqual(markdown_to_text("___bold italic___"), "bold italic")

        # Mixed nested emphasis
        self.assertEqual(
            markdown_to_text("**bold with *nested italic***"), "bold with nested italic"
        )
        self.assertEqual(
            markdown_to_text("*italic with **nested bold***"), "italic with nested bold"
        )

        # Complex nesting
        self.assertEqual(
            markdown_to_text("***really **bold** italic***"), "really bold italic"
        )
        self.assertEqual(
            markdown_to_text("**bold _with_ emphasis**"), "bold with emphasis"
        )

        # Edge case: overlapping emphasis
        self.assertEqual(markdown_to_text("*italic **and bold*}**"), "italic and bold}")

    def test_mixed_list_types(self):
        """Test mixed bullet and numbered lists - critical edge case."""
        mixed_list = """- Bullet item 1
* Bullet item 2
+ Bullet item 3
1. Numbered item 1
2. Numbered item 2
3) Alternative numbered item
- [ ] Task item unchecked
- [x] Task item checked"""

        expected = """Bullet item 1
Bullet item 2
Bullet item 3
Numbered item 1
Numbered item 2
Alternative numbered item
Task item unchecked
Task item checked"""

        result = markdown_to_text(mixed_list)
        self.assertEqual(result.strip(), expected.strip())

    def test_nested_lists(self):
        """Test nested list structures."""
        nested_list = """- Top level item
  - Nested item 1
  - Nested item 2
    - Deep nested item
1. Numbered top level
   1. Nested numbered
   2. Another nested"""

        expected = """Top level item
Nested item 1
Nested item 2
Deep nested item
Numbered top level
Nested numbered
Another nested"""

        result = markdown_to_text(nested_list)
        self.assertEqual(result.strip(), expected.strip())

    def test_tables_as_plain_lines(self):
        """Test that tables are treated as plain text lines."""
        table = """| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |"""

        expected = """Column 1 Column 2 Column 3
Cell 1 Cell 2 Cell 3
Cell 4 Cell 5 Cell 6"""

        result = markdown_to_text(table)
        self.assertEqual(result.strip(), expected.strip())

    def test_complex_table_edge_cases(self):
        """Test complex table scenarios."""
        # Table with alignment markers
        table_with_alignment = """| Left | Center | Right |
|:-----|:------:|------:|
| L1   |   C1   |    R1 |
| L2   |   C2   |    R2 |"""

        expected = """Left Center Right
L1 C1 R1
L2 C2 R2"""

        result = markdown_to_text(table_with_alignment)
        self.assertEqual(result.strip(), expected.strip())

        # Table with empty cells
        table_with_empty = """| A |   | C |
|---|---|---|
| 1 |   | 3 |
|   | 2 |   |"""

        expected = """A C
1 3
2"""

        result = markdown_to_text(table_with_empty)
        self.assertEqual(result.strip(), expected.strip())

    def test_code_blocks_and_inline_code(self):
        """Test code block and inline code handling."""
        # Fenced code blocks
        fenced_code = """Here's some code:
```python
def hello():
    print("Hello, World!")
```
And some text after."""

        expected = """Here's some code:
def hello():
    print("Hello, World!")
And some text after."""

        result = markdown_to_text(fenced_code)
        self.assertEqual(result.strip(), expected.strip())

        # Inline code
        inline = "Use the `print()` function to output text."
        expected = "Use the print() function to output text."
        self.assertEqual(markdown_to_text(inline), expected)

        # Multiple backticks
        multiple_backticks = "``code with backticks`` and ```more code```"
        expected = "code with backticks and more code"
        self.assertEqual(markdown_to_text(multiple_backticks), expected)

    def test_blockquotes(self):
        """Test blockquote handling."""
        blockquote = """> This is a quote
> with multiple lines
>> And nested quotes"""

        expected = """This is a quote
with multiple lines
And nested quotes"""

        result = markdown_to_text(blockquote)
        self.assertEqual(result.strip(), expected.strip())

    def test_horizontal_rules(self):
        """Test horizontal rule removal."""
        hr_text = """Before rule
---
After rule
***
Another section
___
Final section"""

        expected = """Before rule

After rule

Another section

Final section"""

        result = markdown_to_text(hr_text)
        self.assertEqual(result.strip(), expected.strip())

    def test_complex_links_and_images(self):
        """Test complex link and image scenarios."""
        # Reference links
        ref_links = """[link text][1] and [another link][ref]

[1]: http://example.com
[ref]: http://another.com "Title\""""

        expected = "link text and another link"
        result = markdown_to_text(ref_links)
        self.assertEqual(result.strip(), expected.strip())

        # Autolinks
        autolinks = "Visit <http://example.com> or email <test@example.com>"
        expected = "Visit http://example.com or email test@example.com"
        self.assertEqual(markdown_to_text(autolinks), expected)

    def test_strikethrough(self):
        """Test strikethrough formatting."""
        strikethrough = "This is ~~crossed out~~ text."
        expected = "This is crossed out text."
        self.assertEqual(markdown_to_text(strikethrough), expected)

    def test_edge_cases(self):
        """Test various edge cases."""
        # Empty input
        self.assertEqual(markdown_to_text(""), "")
        self.assertEqual(markdown_to_text("   "), "")

        # Non-string input
        self.assertEqual(markdown_to_text(None), "")
        self.assertEqual(markdown_to_text(123), "")

        # Only whitespace after processing
        self.assertEqual(markdown_to_text("   \n\n   "), "")

        # Mixed line endings
        mixed_endings = "Line 1\r\nLine 2\nLine 3\r"
        result = markdown_to_text(mixed_endings)
        self.assertIn("Line 1", result)
        self.assertIn("Line 2", result)
        self.assertIn("Line 3", result)

    def test_preserve_line_breaks_option(self):
        """Test preserve_line_breaks parameter."""
        text = """Line 1

Line 3
Line 4"""

        # With line breaks preserved (default)
        result_preserved = markdown_to_text(text, preserve_line_breaks=True)
        self.assertIn("\n", result_preserved)

        # Without line breaks preserved
        result_flat = markdown_to_text(text, preserve_line_breaks=False)
        self.assertNotIn("\n", result_flat)
        self.assertEqual(result_flat, "Line 1 Line 3 Line 4")

    def test_idempotency(self):
        """Test that function is idempotent - critical requirement."""
        test_cases = [
            "# Header with **bold** text",
            "- List item 1\n- List item 2",
            "***Triple emphasis*** and ~~strikethrough~~",
            "[Link](http://example.com) and ![image](img.jpg)",
            """> Blockquote
> with multiple lines""",
            """| Table | Header |
|-------|--------|
| Cell  | Data   |""",
            """```python
def test():
    pass
```""",
        ]

        for case in test_cases:
            with self.subTest(case=case):
                # Test using helper function
                self.assertTrue(
                    is_idempotent(case), f"Failed idempotency test for: {case}"
                )

                # Manual verification
                first_pass = markdown_to_text(case)
                second_pass = markdown_to_text(first_pass)
                third_pass = markdown_to_text(second_pass)

                self.assertEqual(
                    second_pass,
                    third_pass,
                    f"Not idempotent: {case} -> {first_pass} -> {second_pass} -> {third_pass}",
                )

    def test_deterministic_order(self):
        """Test that regex replacements happen in deterministic order."""
        # This text is designed to test order dependency
        complex_text = """# ***Header with triple emphasis***
- **Bold list item** with [link](http://example.com)
> Blockquote with `inline code` and ~~strikethrough~~
| **Bold** | *Italic* | `Code` |
|----------|----------|--------|
| Cell     | Data     | Value  |"""

        # Run multiple times to ensure same result
        results = [markdown_to_text(complex_text) for _ in range(10)]

        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            self.assertEqual(
                result, first_result, f"Results differ between runs 0 and {i}"
            )

    def test_large_text_performance(self):
        """Test performance with >10k character texts."""
        # Create a large markdown document
        large_sections = []

        # Add various markdown elements
        for i in range(100):
            section = f"""
## Section {i}

This is **bold text** and *italic text* in section {i}.

- List item {i}.1
- List item {i}.2
- List item {i}.3

Here's a [link to section {i}](http://example.com/section{i}).

> This is a quote in section {i}
> with multiple lines of quoted text.

```python
def function_{i}():
    return "Section {i} code"
```

| Column A | Column B | Column C |
|----------|----------|----------|
| Data {i}.1 | Data {i}.2 | Data {i}.3 |

---

"""
            large_sections.append(section)

        large_text = "\n".join(large_sections)

        # Verify it's actually >10k characters
        self.assertGreater(
            len(large_text), 10000, "Test text should be >10k characters"
        )

        # Test performance
        start_time = time.time()
        result = markdown_to_text(large_text)
        end_time = time.time()

        processing_time = end_time - start_time

        # Should process reasonably quickly (adjust threshold as needed)
        self.assertLess(
            processing_time,
            5.0,
            f"Processing took {processing_time:.2f}s, should be <5s",
        )

        # Verify result is not empty and processed correctly
        self.assertGreater(len(result), 1000, "Result should not be too small")
        self.assertNotIn("**", result, "Bold markers should be removed")
        self.assertNotIn("##", result, "Header markers should be removed")

        # Test using performance helper
        perf_stats = performance_test(
            large_text[:5000], iterations=10
        )  # Use smaller sample for speed
        self.assertLess(
            perf_stats["avg_time"], 1.0, "Average processing time should be reasonable"
        )

    def test_whitespace_handling(self):
        """Test proper whitespace cleanup."""
        # Multiple consecutive spaces
        text = "Text    with    multiple     spaces"
        expected = "Text with multiple spaces"
        self.assertEqual(markdown_to_text(text), expected)

        # Multiple consecutive newlines
        text_newlines = "Line 1\n\n\n\nLine 2"
        result = markdown_to_text(text_newlines)
        # Should reduce to maximum 2 consecutive newlines
        self.assertNotIn("\n\n\n", result)

        # Trailing whitespace on lines
        text_trailing = "Line 1   \nLine 2\t\n  Line 3  "
        result = markdown_to_text(text_trailing)
        lines = result.split("\n")
        for line in lines:
            if line:  # Skip empty lines
                self.assertEqual(
                    line,
                    line.rstrip(),
                    f"Line should not have trailing whitespace: '{line}'",
                )

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        unicode_text = """# Héâdér with ümläüts

- Bullet with émöji 🎉
- **Bold tëxt** with spéciäl chars

> Blockquote with "smart quotes" and —em dash—

[Link with unicode](http://example.com/pàth)"""

        result = markdown_to_text(unicode_text)

        # Should preserve unicode characters while removing markdown
        self.assertIn("Héâdér with ümläüts", result)
        self.assertIn("émöji 🎉", result)
        self.assertIn("spéciäl chars", result)
        self.assertIn('"smart quotes"', result)
        self.assertIn("—em dash—", result)

        # But markdown syntax should be gone
        self.assertNotIn("#", result)
        self.assertNotIn("**", result)
        self.assertNotIn("[", result)
        self.assertNotIn("](", result)

    def test_setext_headers(self):
        """Test setext-style headers (underlined with = or -)."""
        setext = """Header 1
========

Header 2
--------

Regular text"""

        expected = """Header 1

Header 2

Regular text"""

        result = markdown_to_text(setext)
        self.assertEqual(result.strip(), expected.strip())

    def test_malformed_markdown(self):
        """Test handling of malformed or incomplete markdown."""
        # Unclosed emphasis
        malformed = "This has **unclosed bold and *unclosed italic"
        result = markdown_to_text(malformed)
        # Should handle gracefully without crashing
        self.assertIsInstance(result, str)

        # Malformed links
        malformed_link = "This is [incomplete link and ![incomplete image"
        result = markdown_to_text(malformed_link)
        self.assertIsInstance(result, str)

        # Malformed table
        malformed_table = """| Header |
| Cell without proper structure
| Another | Cell |"""
        result = markdown_to_text(malformed_table)
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)
