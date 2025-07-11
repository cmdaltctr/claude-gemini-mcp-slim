# Gemini MCP Server Setup Guide

A simple MCP server that integrates Google's Gemini CLI with Claude Desktop and Claude Code, giving you access to Gemini's 1M token context window.

## Prerequisites

Before you start, make sure you have:

1. **Python 3.8+** installed
2. **Node.js 16+** installed
3. **Gemini CLI** installed and authenticated:
   ```bash
   npm install -g @google/gemini-cli
   gemini  # Run this to authenticate with Google
   ```

## Quick Setup (5 minutes)

### Step 1: Install Python Dependencies

```bash
# Install the required Python packages
pip install mcp python-dotenv
```

### Step 2: Create a Dedicated MCP Server Folder

1. Create a dedicated folder for the Gemini MCP server (e.g., `~/gemini-mcp-server/`)
2. Download all required files from this repository to that folder:
   - `gemini_mcp_server.py` - Main MCP server file
   - `gemini_helper.py` - Helper functions
   - `requirements.txt` - Dependencies list
3. Create a `scripts` folder inside .claude in your MCP server folder
   - Download `slim_gemini_hook.py` to the scripts folder
   - Make it executable: `chmod +x ~/gemini-mcp-server/scripts/slim_gemini_hook.py`
4. Add `hooks.json` to .claude folder - Hook definitions for Claude Code integration

**Note:** Keep this folder separate from your projects. It will contain the virtual environment (`venv/`) and cache files (`__pycache__/`) after installation.

### Step 3: Configure Claude Desktop

Add this configuration to your Claude Desktop MCP settings:

**Location:** Claude Desktop → Settings → Developer → MCP Servers

```json
{
  "mcpServers": {
    "gemini mcp": {
      "command": "python3",
      "args": ["/full/path/to/gemini_mcp_server.py"],
      "env": {}
    }
  }
}
```

**Important:** Replace `/full/path/to/gemini_mcp_server.py` with the actual path to your downloaded file.

### Step 4: Configure Claude Desktop & Claude Code

**Important:** Replace `/path/to/venv/bin/python3` with the actual path to your Python virtual environment.

**Important:** Replace `your_key_here` with your actual Google API key.

a) Add this configuration to your Claude Desktop MCP settings:

**Location:** `~/.config/claude-desktop/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "gemini-mcp": {
      "command": "/path/to/venv/bin/python3",
      "args": ["/path/to/gemini_mcp_server.py"],
      "env": {
        "GOOGLE_API_KEY": "your_key_here",
        "GEMINI_FLASH_MODEL": "gemini-2.5-flash",
        "GEMINI_PRO_MODEL": "gemini-2.5-pro"
      }
    }
  }
}
```

b) Add this configuration to your Claude Desktop MCP settings:

**Location:** `/Users/%USERNAME%/.claude.json` (macOS/Linux) or `C:\Users\%USERNAME%\.claude.json (Windows)`

**Important:** Decide where to place the MCP, either in Project/Local/User scopes.

```json
{
  "mcpServers": {
    "gemini-mcp": {
      "command": "/path/to/venv/bin/python3",
      "args": ["/path/to/gemini_mcp_server.py"],
      "env": {
        "GOOGLE_API_KEY": "your_key_here",
        "GEMINI_FLASH_MODEL": "gemini-2.5-flash",
        "GEMINI_PRO_MODEL": "gemini-2.5-pro"
      }
    }
  }
}
```

### Step 5: Test the Setup

1. **Restart Claude Desktop and Claude Code**
2. **Test Gemini CLI directly:**

   ```bash
   gemini -p "Hello, test connection"
   ```

   You should get a response from Gemini.

3. **Test in Claude Desktop/Code:**
   - Look for "gemini mcp" in available tools
   - Try asking: "Use gemini_quick_query to ask what is 2+2"

## Available Tools

Once set up, you'll have access to these tools in both Claude Desktop and Claude Code:

### 🔍 `gemini_quick_query`

- **Purpose:** Ask Gemini CLI any quick question
- **Example:** "What's the best way to handle async errors in JavaScript?"
- **When to use:** Quick coding questions, explanations, general help

### 🔬 `gemini_analyze_code`

- **Purpose:** Analyze specific code sections with detailed insights
- **Example:** Analyze a function for security issues or performance
- **When to use:** Before making changes, code reviews, debugging

### 📊 `gemini_codebase_analysis`

- **Purpose:** Analyze entire directories using Gemini's 1M token context
- **Example:** Review whole project architecture, find patterns
- **When to use:** Project planning, refactoring, architecture reviews

## Usage Examples

### In Claude Desktop

```
User: I have a slow SQL query, can you help optimize it?
User: [paste SQL query]
Claude: I'll analyze this with Gemini. *uses gemini_analyze_code*
```

### In Claude Code

```
User: Analyze this entire src/ directory for security issues
Claude: I'll use Gemini's codebase analysis. *uses gemini_codebase_analysis*
```
![Codebase security analysis example](codebase-security-analysis.jpg)

## Troubleshooting

### "Server not found" or "Connection failed"

- ✅ Check that the file path in your MCP config is correct
- ✅ Restart Claude Desktop/Code after config changes
- ✅ Test that `python3 /path/to/gemini_mcp_server.py` runs without errors

### "Gemini authentication failed"

```bash
# Re-authenticate with Gemini CLI
gemini
```

### "No tools available"

- ✅ Check that `pip install mcp python-dotenv` was successful
- ✅ Verify your MCP config JSON syntax is valid
- ✅ Check Claude Desktop/Code logs for error messages

### "Module not found" errors

```bash
# Make sure you have the right Python environment
pip list | grep mcp
# Should show: mcp, python-dotenv
```

## File Structure

After setup, your structure should look like:

### After Setup, Your Structure Should Look Like:

```
~/gemini-mcp-server/              ← Dedicated folder for the MCP server (separate from your projects)
├── gemini_mcp_server.py          ← Main MCP server file
├── gemini_helper.py              ← Helper functions for Gemini integration
├── requirements.txt              ← Python dependencies list
├── hooks.json                    ← Hook definitions for Claude Code
├── .claude/
│   ├── hooks.json                ← Hook definitions for Claude Code
│   └── scripts/                  ← Scripts directory
│       └── slim_gemini_hook.py   ← Hook execution script
│ 
├── venv/                         ← Python virtual environment (created during installation)
└── __pycache__/                  ← Python cache files (created during execution)

```

**Important:** The MCP server folder should be kept separate from your development projects. You'll reference this folder in your Claude configuration.

## Advanced Configuration

### Using a Virtual Environment (Recommended)

If you prefer to use a virtual environment:

```bash
# Create and activate virtual environment
python3 -m venv gemini-mcp-env
source gemini-mcp-env/bin/activate  # On Windows: gemini-mcp-env\Scripts\activate

# Install dependencies
pip install mcp python-dotenv

# Update your MCP config to use the virtual environment Python
```

Then update your MCP configuration:

```json
{
  "mcpServers": {
    "gemini mcp": {
      "command": "/path/to/gemini-mcp-env/venv/bin/python3", # Use /venv/ if you created a virtual environment 
      "args": ["/path/to/gemini_mcp_server.py"],
      "env": {}
    }
  }
}
```

**Note**: For the line `"command": "/path/to/gemini-mcp-env/venv/bin/python3",`, Use /venv/ if you created a virtual environment, otherwise just use `/bin.python3`.

### Advanced Configuration Parameters

You can customize behavior by adding environment variables to your MCP config:

#### File Analysis Limits

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
    "gemini mcp": {
      "command": "python3",
      "args": ["/path/to/gemini_mcp_server.py"],
      "env": {
        "MAX_FILE_SIZE": "120000",      // 120KB for larger files
        "MAX_FILE_LINES": "1000",       // 1000 lines for bigger files
        "MAX_RESPONSE_WORDS": "1000"    // More detailed analysis
      }
    }
  }
}
```

#### Timeout Settings

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

#### Model Selection & Performance

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

#### Hook Configuration (If Using Automation)

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

#### Complete Configuration Example

```json
{
  "mcpServers": {
    "gemini mcp": {
      "command": "/path/to/venv/bin/python3",
      "args": ["/path/to/gemini_mcp_server.py"],
      "env": {
        "GOOGLE_API_KEY": "your_actual_api_key_here",
        "GEMINI_FLASH_MODEL": "gemini-2.5-flash",
        "GEMINI_PRO_MODEL": "gemini-2.5-pro",
        "MAX_FILE_SIZE": "100000",
        "MAX_FILE_LINES": "1000",
        "ANALYSIS_TIMEOUT": "90",
        "CODEBASE_TIMEOUT": "180",
        "MAX_RESPONSE_WORDS": "1000"
      }
    }
  }
}
```

#### Configuration Tips

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

## Optional: Advanced Hook Automation

For automated pre-edit analysis and commit review, you can set up Claude Code hooks:

### Step 6: Setup Hook Configuration (Optional)

If you want automated analysis before edits and commits:

1. **Create the hooks directory:**
   ```bash
   mkdir -p .claude/scripts
   ```

2. **Download the hook files:**
   - Download `hooks.json` to `.claude/hooks.json`
   - Download `slim_gemini_hook.py` to `.claude/scripts/slim_gemini_hook.py`

3. **Make the hook script executable:**
   ```bash
   chmod +x .claude/scripts/slim_gemini_hook.py
   ```

**Expected structure with hooks:**
```
your-project/
├── .claude/
│   ├── hooks.json               ← Hook configuration
│   └── scripts/
│       └── slim_gemini_hook.py  ← Hook execution script
├── gemini_mcp_server.py         ← The MCP server file
└── your-claude-config.json      ← Your Claude MCP configuration
```

**Note:** Hooks provide automated pre-edit analysis and commit review but are optional. The core MCP tools work without them.

## What's Next?

Once everything is working:

1. **Try the tools** - Start with simple `gemini_quick_query` requests
2. **Analyze some code** - Use `gemini_analyze_code` on functions you're working on
3. **Review your project** - Use `gemini_codebase_analysis` to get architectural insights
4. **Read CLAUDE.md** - For advanced automation and hook configurations

## Need Help?

- **Test files:** Check the `tests/` folder for examples and testing scripts
- **Full documentation:** See `CLAUDE.md` for comprehensive usage guide
- **Issues:** Check your Claude Desktop/Code console for error messages
