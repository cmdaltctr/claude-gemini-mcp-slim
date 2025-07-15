---
description: "Analyze entire directories using Gemini's 1M token context"
allowed-tools: ["mcp__gemini-mcp__gemini_codebase_analysis"]
---

# Codebase Analysis

Analyze entire directories and codebases with Gemini's large context window.

**Usage:** `/codebase [directory_path] [scope:optional]`

**Examples:**
- `/codebase ./src`
- `/codebase ./components security`
- `/codebase . all`

**Analyzing codebase:** $ARGUMENTS

!mcp__gemini-mcp__gemini_codebase_analysis directory_path="$1" analysis_scope="$2"
