---
description: "Explain code concepts, functions, or error messages"
allowed-tools: ["mcp__gemini-mcp__gemini_quick_query"]
---

# Code Explanation

Get detailed explanations of code concepts, functions, or error messages.

**Usage:** `/explain [code_or_concept]`

**Examples:**
- `/explain async/await in JavaScript`
- `/explain const handleSubmit = async (data) => {...}`
- `/explain TypeError: Cannot read property 'map' of undefined`

**Explaining:** $ARGUMENTS

!mcp__gemini-mcp__gemini_quick_query query="Explain this code or concept in detail: $ARGUMENTS"
