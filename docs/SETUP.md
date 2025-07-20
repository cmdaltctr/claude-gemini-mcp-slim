# Gemini MCP Server Installation Guide

This project provides a bridge between Claude Code and Google's Gemini AI models, giving you access to Gemini's powerful 1M+ token context window and latest AI capabilities directly within your Claude Code development environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Create Shared MCP Environment](#create-shared-mcp-environment)
3. [Install Python and Node Dependencies](#install-python-and-node-dependencies)
4. [Set Up Gemini MCP Folder](#set-up-gemini-mcp-folder)
5. [Configure AI Clients](#configure-ai-clients)
6. [Optional Hook and Slash Command Setup](#optional-hook-and-slash-command-setup)
7. [Verification and Testing](#verification-and-testing)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Architecture Overview](#architecture-overview)

## Installation

### Clone the Repository

```bash
# Replace with the actual repository URL
git clone https://github.com/cmdaltctr/claude-gemini-mcp-slim
cd claude-gemini-mcp-slim
```

### Prerequisites

Before you start, make sure you have:

1. **Python 3.8+** installed
2. **Node.js 16+** installed
3. **Gemini API Key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Visit the link above
   - Click "Create API key"
   - Copy the generated key (keep it secure!)
4. **Gemini CLI** installed and authenticated:
   ```bash
   npm install -g @google/gemini-cli
   gemini  # Run this to authenticate with Google
   ```

### Create Shared MCP Environment

Create a dedicated system-wide location for all your MCP servers:

```bash
# Create shared MCP directory
mkdir -p ~/mcp-servers
cd ~/mcp-servers

# Create virtual environment for all MCP servers
python3 -m venv shared-mcp-env
source shared-mcp-env/bin/activate
```

### Install Python and Node Dependencies

```bash
# Install MCP dependencies inside virtual environment
pip install mcp google-generativeai python-dotenv

# Install Node.js dependencies for unified Husky hook system (recommended)
npm install --save-dev @commitlint/config-conventional @commitlint/cli husky

# Initialize Husky git hooks
npx husky install
```

### Set Up Gemini MCP Folder

```bash
# Create Gemini MCP folder structure
mkdir -p gemini-mcp/.claude/scripts

# Copy files from cloned repository to gemini-mcp/
# Note: Replace /path/to/claude-gemini-mcp-slim with the actual path where you cloned the repository
cp /path/to/claude-gemini-mcp-slim/gemini_mcp_server.py gemini-mcp/
cp /path/to/claude-gemini-mcp-slim/.claude/hooks.json gemini-mcp/.claude/
cp -r /path/to/claude-gemini-mcp-slim/.claude/commands/ gemini-mcp/.claude/
cp /path/to/claude-gemini-mcp-slim/.claude/scripts/slim_gemini_hook.py gemini-mcp/.claude/scripts/

# Make scripts executable
chmod +x gemini-mcp/.claude/scripts/slim_gemini_hook.py
```

**Quick tip:** If you cloned the repository in your home directory, the path would be `~/claude-gemini-mcp-slim/`

### Configure AI Clients

Configure your AI clients to use the shared Gemini MCP server:

#### For Claude Desktop

**Location:** `~/.config/claude-desktop/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "gemini-mcp": {
      "command": "/Users/YOUR_USERNAME/mcp-servers/shared-mcp-env/bin/python",
      "args": ["/Users/YOUR_USERNAME/mcp-servers/gemini-mcp/gemini_mcp_server.py"],
      "env": {
        "GOOGLE_API_KEY": "your_api_key_here",  // Keep this secure - never commit to version control!
        "GEMINI_FLASH_MODEL": "gemini-2.5-flash",
        "GEMINI_PRO_MODEL": "gemini-2.5-pro"
      }
    }
  }
}
```

#### For Claude Code

**Global Location:** `~/.claude.json` (macOS/Linux) or `C:\Users\USERNAME\.claude.json` (Windows)
**Project-specific Location:** `.claude/` folder in your project directory

```json
{
  "mcpServers": {
    "gemini-mcp": {
      "command": "/Users/YOUR_USERNAME/mcp-servers/shared-mcp-env/bin/python",
      "args": ["/Users/YOUR_USERNAME/mcp-servers/gemini-mcp/gemini_mcp_server.py"],
      "env": {
        "GOOGLE_API_KEY": "your_api_key_here",
        "GEMINI_FLASH_MODEL": "gemini-2.5-flash",
        "GEMINI_PRO_MODEL": "gemini-2.5-pro"
      }
    }
  }
}
```

**Important:** Replace `YOUR_USERNAME` with your actual username and `your_api_key_here` with your Google API key.

**To find your username:**
- **macOS/Linux:** Run `echo $USER` in terminal
- **Windows:** Run `echo %USERNAME%` in command prompt
- **Example:** If your username is `john`, the path would be `/Users/john/mcp-servers/shared-mcp-env/bin/python`

### Optional Hook and Slash Command Setup

Hooks and slash commands require a `.claude/` folder in your project directory and only work in the Claude Code ecosystem. This folder contains:
- **Hooks**: `.claude/hooks.json` and `.claude/scripts/` for pre-edit/pre-commit analysis
- **Slash Commands**: `.claude/commands/` for convenient shortcuts like `/analyze`, `/codebase`, etc.

You have three options:

#### Option A: Symlink to Shared .claude Folder (Recommended)

**Best for:** Teams, multiple projects, easy maintenance, access to both hooks and slash commands

```bash
cd /path/to/your-project
ln -s ~/mcp-servers/gemini-mcp/.claude .claude
```

#### Option B: Copy .claude Files Directly

**Best for:** Project-specific customization, offline work, full control over hooks and slash commands

```bash
cd /path/to/your-project
mkdir -p .claude/scripts
cp ~/mcp-servers/gemini-mcp/.claude/hooks.json .claude/
cp -r ~/mcp-servers/gemini-mcp/.claude/commands/ .claude/
cp ~/mcp-servers/gemini-mcp/.claude/scripts/slim_gemini_hook.py .claude/scripts/
```

#### Option C: No Hooks or Slash Commands

**Best for:** Simple workflows, non-Claude Code clients, MCP tools only

```bash
# Do nothing - no .claude folder needed
# MCP tools still work perfectly
# Note: You'll need to use full MCP syntax like /mcp__gemini-mcp__gemini_quick_query
```

**.claude Setup Comparison:**

| Feature | Symlink | Copy | No .claude |
|---------|---------|------|-----------|
| Easy updates | Yes | No | N/A |
| Consistency | Yes | No | N/A |
| Quick setup | Yes | No | Yes |
| Version control friendly | Yes | Yes | Yes |
| Independent customization | No | Yes | N/A |
| Full control | No | Yes | N/A |
| Hooks support | Yes | Yes | No |
| Slash commands support | Yes | Yes | No |
| Clean projects | No | No | Yes |
| Universal compatibility | No | No | Yes |
| Zero maintenance | No | No | Yes |

### Verification and Testing

1. **Restart all AI clients** (Claude Desktop, Claude Code, Windsurf)
2. **Test Gemini CLI directly:**

   ```bash
   gemini -p "Hello, test connection"
   ```

   You should get a response from Gemini.

3. **Test in AI clients:**
   - Look for "gemini-mcp" in available tools
   - Try using the MCP tool: "/mcp__gemini-mcp__gemini_quick_query What is 2+2?"

## Available Tools

Once set up, you'll have access to these tools in both Claude Desktop and Claude Code:

### `gemini_quick_query`

- **Purpose:** Ask Gemini CLI any quick question
- **Syntax:** `/mcp__gemini-mcp__gemini_quick_query "your question"`
- **Example:** `/mcp__gemini-mcp__gemini_quick_query "What's the best way to handle async errors in JavaScript?"`
- **When to use:** Quick coding questions, explanations, general help

### `gemini_analyze_code`

- **Purpose:** Analyze specific code sections with detailed insights
- **Syntax:** `/mcp__gemini-mcp__gemini_analyze_code "code content" [analysis_type]`
- **Example:** `/mcp__gemini-mcp__gemini_analyze_code "function validateUser(data) { ... }" security`
- **When to use:** Before making changes, code reviews, debugging

### `gemini_codebase_analysis`

- **Purpose:** Analyze entire directories using Gemini's 1M token context
- **Syntax:** `/mcp__gemini-mcp__gemini_codebase_analysis "directory_path" [analysis_scope]`
- **Example:** `/mcp__gemini-mcp__gemini_codebase_analysis "./src" security`
- **When to use:** Project planning, refactoring, architecture reviews

## Usage Examples

### In Claude Desktop

```
User: I have a slow SQL query, can you help optimize it?
User: /mcp__gemini-mcp__gemini_analyze_code "SELECT * FROM users WHERE status = 'active' AND created_at > '2023-01-01'" performance

[Gemini analyzes the SQL query and provides optimization suggestions]
```

### In Claude Code

**Option 1: Direct MCP Tool Call**
```
User: /mcp__gemini-mcp__gemini_codebase_analysis "./src" security

[Gemini analyzes the entire src directory for security vulnerabilities and provides a comprehensive report]
```

**Option 2: Simplified Slash Command (Easier)**
```
User: /codebase ./src security

[Same analysis as above, but using the convenient slash command shortcut]
```

The slash commands provide a much simpler way to access the same powerful Gemini analysis without remembering the full MCP tool syntax. See [.claude/README-SLASH-COMMANDS.md](.claude/README-SLASH-COMMANDS.md) for all available shortcuts.

### Standalone Helper CLI

**`gemini_helper.py`** - A standalone CLI tool for direct Gemini interaction
- **query**: Ask quick development questions
  - **Usage**: `python gemini_helper.py query "What's the difference between async and defer in JavaScript?"`
- **analyze**: Analyze code files for security or performance
  - **Usage**: `python gemini_helper.py analyze my_file.py security`
- **codebase**: Analyze entire codebases for architectural insights
  - **Usage**: `python gemini_helper.py codebase ./src performance`
- **When to use:** Without a full MCP setup or when needing quick insights directly from the command line

## Configuration

### File Analysis Limits

**Default Values:**
- Maximum file size: 80KB (81,920 bytes)
- Maximum lines: 800 lines
- Response limit: 800 words (200 for session summaries)

**When to adjust:**
- **Larger files**: Increase limits for projects with big source files
- **Performance**: Decrease limits on slower systems or to save tokens
- **Detailed analysis**: Increase response limits for more comprehensive reviews

```json
{
  "mcpServers": {
    "gemini-mcp": {
      "command": "/Users/YOUR_USERNAME/mcp-servers/shared-mcp-env/bin/python",
      "args": ["/Users/YOUR_USERNAME/mcp-servers/gemini-mcp/gemini_mcp_server.py"],
      "env": {
        "MAX_FILE_SIZE": "120000",      // 120KB for larger files
        "MAX_FILE_LINES": "1000",       // 1000 lines for bigger files
        "MAX_RESPONSE_WORDS": "1000"    // More detailed analysis
      }
    }
  }
}
```

### Timeout Settings

**Default Values:**
- Session summary: 30 seconds
- Code analysis: 60 seconds
- Codebase analysis: 120 seconds

**When to adjust:**
- **Slow network**: Increase timeouts for unstable connections
- **Large projects**: Increase for comprehensive codebase analysis
- **Quick feedback**: Decrease for faster responses

```json
{
  "env": {
    "ANALYSIS_TIMEOUT": "90",         // 90 seconds for code analysis
    "CODEBASE_TIMEOUT": "180",        // 3 minutes for full codebase
    "SESSION_TIMEOUT": "45"           // 45 seconds for summaries
  }
}
```

### Model Selection and Performance

**Default Models:**
- Quick queries: `gemini-2.5-flash` (fast, cost-effective)
- Code analysis: `gemini-2.5-pro` (deep analysis)
- Codebase analysis: `gemini-2.5-pro` (large context)

**When to customize:**
- **Cost optimization**: Use Flash for all operations
- **Maximum quality**: Use Pro for all operations
- **Beta testing**: Try experimental models

```json
{
  "env": {
    "GEMINI_FLASH_MODEL": "gemini-2.5-flash-exp",  // Experimental Flash
    "GEMINI_PRO_MODEL": "gemini-2.5-pro-exp",      // Experimental Pro
    "FORCE_MODEL": "flash",                         // Force all operations to use Flash
    "GOOGLE_API_KEY": "your_api_key_here"           // Required for API access
  }
}
```

### Hook Configuration

**Default Behavior:**
- Pre-edit analysis: Files under 800 lines, 80KB
- Pre-commit review: All staged changes
- Session summary: 200-word brief recap

**Customization options:**

```json
{
  "env": {
    "HOOK_FILE_LIMIT": "1000",        // Analyze files up to 1000 lines
    "HOOK_SIZE_LIMIT": "100000",      // Analyze files up to 100KB
    "HOOK_SUMMARY_WORDS": "300",      // 300-word session summaries
    "HOOK_ANALYSIS_WORDS": "1000",    // 1000-word pre-edit analysis
    "DISABLE_PRE_EDIT": "false",      // Set to "true" to disable pre-edit analysis
    "DISABLE_PRE_COMMIT": "false"     // Set to "true" to disable commit reviews
  }
}
```

### Configuration Tips

**For Large Projects:**
- Increase file size/line limits
- Extend timeout settings
- Use Pro model for better context handling

**For Quick Development:**
- Use Flash model for all operations
- Reduce response word limits
- Shorter timeouts for faster feedback

**For Cost Optimization:**
- Use Flash model exclusively: `"FORCE_MODEL": "flash"`
- Reduce file size limits to analyze smaller files
- Shorter response limits to use fewer tokens

## Troubleshooting

### "Server not found" or "Connection failed"

- Check that the file path in your MCP config is correct
- Restart Claude Desktop/Code after config changes
- Test that `python3 /path/to/gemini_mcp_server.py` runs without errors

### "Gemini authentication failed"

```bash
# Re-authenticate with Gemini CLI
gemini
```

### "No tools available"

- Check that `pip install mcp python-dotenv` was successful
- Verify your MCP config JSON syntax is valid
- Check Claude Desktop/Code logs for error messages

### "Module not found" errors

```bash
# Make sure you have the right Python environment
pip list | grep mcp
# Should show: mcp, python-dotenv
```

## Need Help?

- **Submit an Issue:** If you encounter any problems, please submit an issue on our [GitHub repository](https://github.com/cmdaltctr/claude-gemini-mcp-slim/issues) with details about your environment, steps to reproduce, and any error messages you received.
- **Use Labels:** When submitting issues, please use appropriate labels/tags such as `bug`, `feature-request`, `documentation`, and so on ([available labels](https://github.com/cmdaltctr/claude-gemini-mcp-slim/labels)) to help me categorize and address your concerns more efficiently.
- **Check Documentation:** Review the [README.md](../README.md) and [.claude/README-SLASH-COMMANDS.md](../.claude/README-SLASH-COMMANDS.md) for comprehensive guides.
- **Console Logs:** Check your Claude Desktop/Code console for detailed error messages that can help diagnose issues.
