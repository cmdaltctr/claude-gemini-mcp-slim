---
description: "Debug assistance for code issues and errors"
allowed-tools: ["mcp__gemini-mcp__gemini_quick_query"]
---

# Debug Assistance

Get help debugging code issues, errors, and problems.

**Usage:** `/debug [code_or_error]`

**Examples:**
- `/debug ReferenceError: fetch is not defined`
- `/debug Why is my React component not re-rendering?`
- `/debug function calculateTotal() { return items.reduce(...) }`

**Debugging:** $ARGUMENTS

!mcp__gemini-mcp__gemini_quick_query query="Help me debug this issue: $ARGUMENTS. Provide specific solutions and common causes."
