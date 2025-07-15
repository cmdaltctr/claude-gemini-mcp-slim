---
description: "Ask Gemini any development question"
allowed-tools: ["mcp__gemini-mcp__gemini_quick_query"]
---

# Ask Gemini

Use Gemini's powerful AI to answer any development question or provide coding assistance.

**Usage:** `/gemini [your question]`

**Examples:**
- `/gemini How do I implement JWT authentication in Node.js?`
- `/gemini What's the difference between React hooks and class components?`
- `/gemini Best practices for error handling in Python?`

**What you asked:** $ARGUMENTS

Let me ask Gemini your question using the MCP tool:

!mcp__gemini-mcp__gemini_quick_query query="$ARGUMENTS"
