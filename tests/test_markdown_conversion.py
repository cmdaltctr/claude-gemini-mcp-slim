#!/usr/bin/env python3
import re

def markdown_to_plain_text(text: str) -> str:
    """Convert markdown formatted text to clean plain text"""
    # Remove bold/italic formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)     # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)       # _italic_
    
    # Remove code formatting
    text = re.sub(r'`([^`]+)`', r'\1', text)       # `code`
    text = re.sub(r'```[\s\S]*?```', '', text)     # ```code blocks```
    
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove links but keep the text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
    text = text.strip()
    
    return text

# Test with sample Gemini response
sample_markdown = """**Query:** What are the best practices for error handling in Python?

Here are the best practices for error handling in Python:

1.  **Use `try-except` blocks:** The fundamental mechanism for handling anticipated errors.
2.  **Catch specific exceptions:** Avoid broad `except` clauses (e.g., `except Exception as e:` or bare `except:`) unless you explicitly intend to catch *all* errors and re-raise. Specificity leads to clearer, more robust code.
3.  **Utilize `finally` or `with` statements:** For guaranteed resource cleanup (e.g., closing files, network connections), regardless of whether an error occurred. `with` statements (context managers) are generally preferred for this.
4.  **Log errors with sufficient detail:** Instead of just printing, use Python's `logging` module to record errors, including traceback information, for debugging and monitoring.
5.  **Re-raise exceptions:** If your code catches an exception but cannot fully handle it, re-raise it (e.g., `raise`) to propagate it up the call stack for higher-level handling.
6.  **Validate inputs early:** Prevent errors before they occur by validating function arguments or user inputs at the earliest possible stage.
7.  **Provide clear, informative error messages:** Ensure that error messages (whether logged or presented to the user) are helpful for diagnosis and resolution.
8.  **Avoid silently swallowing errors:** Never just `pass` on an `except` block without logging, raising, or handling the error. This hides bugs and makes debugging extremely difficult."""

print("ORIGINAL (with markdown):")
print("=" * 50)
print(sample_markdown)
print("\n" + "=" * 50)
print("CONVERTED (plain text):")
print("=" * 50)
converted = markdown_to_plain_text(sample_markdown)
print(converted)
