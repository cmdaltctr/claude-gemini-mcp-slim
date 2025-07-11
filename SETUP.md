# Gemini CLI MCP Server Setup

## ✅ Completed Steps
1. ✅ Virtual environment created
2. ✅ MCP package installed
3. ✅ `gemini_cli_mcp_server.py` is ready to use
4. ✅ Unused files moved to `backup/` folder

## Claude Desktop Configuration

Add this to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "gemini-cli-analysis": {
      "command": "/Users/aizat/Windsurf Projects/claude-gemini-mcp-slim/venv/bin/python3",
      "args": ["/Users/aizat/Windsurf Projects/claude-gemini-mcp-slim/gemini_cli_mcp_server.py"],
      "env": {}
    }
  }
}
```

## Available Tools

1. **gemini_quick_query** - Ask Gemini CLI quick questions
2. **gemini_analyze_code** - Analyze code sections  
3. **gemini_codebase_analysis** - Analyze entire directories

## Testing

After configuring Claude Desktop, restart it and the MCP server should load without the "mcp module not found" error.

## File Structure

```
claude-gemini-mcp-slim/
├── gemini_cli_mcp_server.py  ← Main MCP server (using venv)
├── gemini_helper.py          ← Helper utilities
├── requirements.txt          ← Dependencies
├── venv/                     ← Virtual environment with MCP
├── backup/                   ← Old/unused files
└── SETUP.md                  ← This file
```
