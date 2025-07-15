---
description: "Analyze code or files with comprehensive insights"
allowed-tools: ["mcp__gemini-mcp__gemini_analyze_code"]
---

# Code Analysis

Analyze code files for bugs, security issues, performance, and best practices.

**Usage:** `/analyze [file_path] [analysis_type:optional]`

**Examples:**
- `/analyze src/auth.py security`
- `/analyze components/UserForm.vue`
- `/analyze ./utils/database.js performance`

**Analyzing:** $ARGUMENTS

!mcp__gemini-mcp__gemini_analyze_code code_content="@$1" analysis_type="$2"
