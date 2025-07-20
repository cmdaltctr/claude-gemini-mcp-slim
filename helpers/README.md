# Markdown to Text Utility

A robust, deterministic markdown-to-text converter designed for high-performance processing with comprehensive edge case handling.

## Features

- **Deterministic Processing**: Applies regex replacements in a specific order for consistent results
- **Comprehensive Markdown Support**: Handles all major markdown elements including nested emphasis, mixed lists, tables, code blocks, links, images, blockquotes, and horizontal rules
- **Edge Case Handling**: Properly processes nested emphasis, mixed bullet types, numbered lists, and task lists
- **Table Processing**: Treats tables as plain text lines while preserving content
- **Idempotent**: Running the function multiple times on the same input produces identical results
- **High Performance**: Optimized for >10k character texts with sub-second processing times
- **Unicode Support**: Handles international characters and emojis correctly

## Usage

```python
from helpers.markdown_utils import markdown_to_text

# Basic usage
text = markdown_to_text("# Hello **World**")
# Output: "Hello World"

# With line break preservation (default)
text = markdown_to_text("Line 1\n\nLine 2", preserve_line_breaks=True)
# Output: "Line 1\n\nLine 2"

# Without line break preservation
text = markdown_to_text("Line 1\n\nLine 2", preserve_line_breaks=False)
# Output: "Line 1 Line 2"
```

## Supported Markdown Elements

### Headers
- ATX headers: `# Header`, `## Header 2`
- Setext headers: `Header\n====`, `Header\n----`

### Emphasis
- Bold: `**text**`, `__text__`
- Italic: `*text*`, `_text_`
- Bold + Italic: `***text***`, `___text___`
- Nested emphasis: `**bold with *italic***`

### Lists
- Unordered: `- item`, `* item`, `+ item`
- Ordered: `1. item`, `2) item`
- Task lists: `- [ ] unchecked`, `- [x] checked`
- Nested lists with proper indentation

### Code
- Inline code: `` `code` ``, ``` ``code`` ```
- Fenced code blocks: ``` ```lang\ncode\n``` ```
- Indented code blocks (4+ spaces)

### Links and Images
- Inline links: `[text](url)`
- Reference links: `[text][ref]`
- Images: `![alt](src)`
- Autolinks: `<http://url>`, `<email@domain.com>`

### Tables
- Standard tables with `|` separators
- Header separators (`|---|---|`)
- Alignment markers (`:--:`, `--:`, `:--`)
- Empty cells handled gracefully

### Other Elements
- Blockquotes: `> text`
- Nested blockquotes: `>> text`
- Horizontal rules: `---`, `***`, `___`
- Strikethrough: `~~text~~`

## Processing Order

The function processes markdown elements in a specific order to avoid conflicts:

1. **Code blocks and inline code** (highest priority)
2. **Links and images** (before other processing)
3. **Headers** (before emphasis to avoid conflicts)
4. **Horizontal rules** (before emphasis)
5. **Emphasis and formatting** (nested processing)
6. **Lists** (complex structures)
7. **Tables** (treated as plain text)
8. **Blockquotes** (block elements)
9. **Whitespace cleanup** (final step)

## Performance

The function is optimized for high-performance processing:

- **>10k character texts**: Processes in <1 second
- **50k+ character documents**: ~4.4M characters/second throughput
- **Memory efficient**: Uses streaming regex processing
- **Idempotent**: Safe to run multiple times

## Testing

The implementation includes comprehensive unit tests covering:

- Basic functionality for all markdown elements
- Nested emphasis edge cases
- Mixed list types and task lists
- Table processing with various formats
- Idempotency testing
- Performance testing with large documents
- Unicode and special character handling
- Malformed markdown resilience

Run tests with:
```bash
python -m unittest tests.unit.test_markdown_utils -v
# or
python test_markdown.py
```

## API Reference

### `markdown_to_text(markdown: str, preserve_line_breaks: bool = True) -> str`

Convert markdown text to plain text.

**Parameters:**
- `markdown` (str): The markdown content to convert
- `preserve_line_breaks` (bool): Whether to preserve line breaks in output

**Returns:**
- str: Plain text with markdown syntax removed

**Example:**
```python
result = markdown_to_text("# Hello **World**")
assert result == "Hello World"
```

### `is_idempotent(markdown: str, max_iterations: int = 3) -> bool`

Test if the markdown_to_text function is idempotent for given input.

### `performance_test(text: str, iterations: int = 100) -> dict`

Test performance of markdown_to_text function and return statistics.

## Error Handling

The function gracefully handles:
- Non-string input (returns empty string)
- Empty or whitespace-only input
- Malformed markdown syntax
- Incomplete markdown elements
- Mixed line endings
- Very large documents

## License

This utility is part of the claude-gemini-mcp-slim project.
