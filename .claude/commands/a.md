---
description: "Quick alias for /analyze"
allowed-tools: ["mcp__gemini-mcp__gemini_analyze_code"]
---

# Quick Code Analysis

Fast code analysis with Gemini's insights.

**Usage:** `/a [file_path] [analysis_type:optional]`

**Examples:**
- `/a auth.py`
- `/a UserForm.vue security`

**Analyzing:** $ARGUMENTS

!mcp__gemini-mcp__gemini_analyze_code code_content="@$1" analysis_type="$2"
