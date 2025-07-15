---
description: "Quick alias for /debug"
allowed-tools: ["mcp__gemini-mcp__gemini_quick_query"]
---

# Quick Debug

Fast debugging help with Gemini.

**Usage:** `/d [code_or_error]`

**Examples:**
- `/d Cannot resolve module 'react'`
- `/d Memory leak in useEffect`

**Debugging:** $ARGUMENTS

!mcp__gemini-mcp__gemini_quick_query query="Help me debug this issue: $ARGUMENTS. Provide specific solutions and common causes."
