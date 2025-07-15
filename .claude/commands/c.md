---
description: "Quick alias for /codebase"
allowed-tools: ["mcp__gemini-mcp__gemini_codebase_analysis"]
---

# Quick Codebase Analysis

Fast codebase analysis with Gemini's large context.

**Usage:** `/c [directory_path] [scope:optional]`

**Examples:**
- `/c ./src`
- `/c . security`

**Analyzing:** $ARGUMENTS

!mcp__gemini-mcp__gemini_codebase_analysis directory_path="$1" analysis_scope="$2"
