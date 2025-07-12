# Claude Gemini MCP Integration

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Security](https://img.shields.io/badge/security-hardened-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-brightgreen.svg)
![Status](https://img.shields.io/badge/status-production%20ready-green.svg)
![Slash Commands](https://img.shields.io/badge/slash%20commands-20+-orange.svg)

**A lightweight integration that brings Google's Gemini AI capabilities to Claude Code through MCP (Model Context Protocol)**

## What This Does

This project creates a bridge between Claude Code and Google's Gemini AI models, giving you access to Gemini's powerful 1M+ token context window and latest AI capabilities directly within your Claude Code development environment.

## Key Features

### **Three Powerful Tools**

- **Quick Query** - Ask Gemini any development question instantly
- **Code Analysis** - Deep analysis of specific code sections with security, performance, and architecture insights
- **Codebase Analysis** - Full project analysis using Gemini's massive context window

### **Easy-to-Use Slash Commands**

- **20+ Slash Commands** - Simple shortcuts like `/g`, `/analyze`, `/security` for instant access
- **Smart Routing** - Commands automatically choose the right tool based on your target
- **Copy-Paste Ready** - Complete `.claude/` directory with all configurations included

### **Smart Model Selection**

- **Gemini Flash** - Fast responses for quick questions and simple tasks
- **Gemini Pro** - Deep analysis for complex code review and architecture decisions
- **Automatic fallback** - Direct API calls with CLI backup

### **Real-time Streaming**

- Live output streaming during analysis
- Progress indicators for long-running tasks
- No waiting for complete responses

## How It Works

### Architecture Overview

```
Claude Code ←→ MCP Server ←→ Gemini CLI/API ←→ Google Gemini Models
                    ↓
            Smart Model Selection
            (Flash for speed, Pro for depth)
```

### Core Components

**1. MCP Server (`gemini_mcp_server.py`)**

- Main integration point with Claude Code
- Handles tool registration and execution
- Manages streaming responses and error handling
- Smart model selection based on task complexity

**2. Helper Utility (`gemini_helper.py`)**

- Standalone CLI tool for direct Gemini interaction
- API-first approach with CLI fallback
- Real-time streaming output
- Progress tracking for long analyses

**3. Configuration**

- Environment-based model selection
- API key management
- File size and analysis limits

## Quick Start

### Shared MCP Setup

This MCP uses a **shared system architecture** that serves multiple AI clients (Claude Desktop, Claude Code, Windsurf, etc.) from one installation:

```bash
# 1. Create shared MCP environment
mkdir -p ~/mcp-servers && cd ~/mcp-servers
python3 -m venv shared-mcp-env
source shared-mcp-env/bin/activate
pip install mcp google-generativeai

# 2. Install Gemini CLI
npm install -g @google/gemini-cli
gemini  # Authenticate with Google

# 3. Set up Gemini MCP server
mkdir -p gemini-mcp/.claude/scripts
# (Download files from this repo to gemini-mcp/)
```

### **Configure AI Clients**

Add to your AI client configurations:

```json
{
  "mcpServers": {
    "gemini-mcp": {
      "command": "/Users/YOUR_USERNAME/mcp-servers/shared-mcp-env/bin/python",
      "args": ["/Users/YOUR_USERNAME/mcp-servers/gemini-mcp/gemini_mcp_server.py"],
      "env": { "GOOGLE_API_KEY": "your_key_here" }
    }
  }
}
```

---

## Please Read

**📖 [Complete Setup Guide](SETUP/SETUP.md) - Get running in 5 minutes!**

**⚡ [Slash Commands Guide](.claude/README-SLASH-COMMANDS.md) - 20+ shortcuts for instant access!**

---

**✅ Benefits of Shared Architecture:**

- One installation serves all AI clients and projects
- Clean project folders (no MCP dependencies)
- Easy maintenance and updates
- Professional deployment pattern

## Usage Examples

### Quick Development Questions

```
Use gemini_quick_query for:
- "How do I implement JWT authentication in Node.js?"
- "What's the difference between useEffect and useLayoutEffect?"
- "Best practices for error handling in Python async functions"
```

### Code Analysis

```
Use gemini_analyze_code for:
- Security review of authentication functions
- Performance analysis of database queries
- Architecture review before major refactoring
```

### Full Project Analysis

```
Use gemini_codebase_analysis for:
- Overall architecture assessment
- Security vulnerability scanning
- Performance bottleneck identification
```

## Code Architecture

### MCP Server Design

**Tool Registration**

```python
@server.list_tools()
async def list_tools() -> List[Tool]:
    # Defines three main tools with input schemas
    # Each tool has specific parameters and validation
```

**Smart Execution Engine**

```python
async def execute_gemini_cli_streaming(prompt: str, task_type: str):
    # 1. Model Selection (Flash vs Pro based on task)
    # 2. API Attempt (if GOOGLE_API_KEY available)
    # 3. CLI Fallback (with real-time streaming)
    # 4. Progress Tracking and Error Handling
```

**Tool Implementation**

```python
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    # Routes to appropriate analysis function
    # Handles file size limits and validation
    # Formats prompts for optimal Gemini responses
```

### Helper Utility Design

**Execution Strategies**

- `execute_gemini_api()` - Direct API calls (preferred)
- `execute_gemini_cli()` - CLI execution with streaming
- `execute_gemini_smart()` - Combined approach with fallback

**Real-time Features**

- Line-by-line output streaming
- Progress indicators every 15 seconds
- Timeout handling and process management

## Configuration

### Model Selection

```python
GEMINI_MODELS = {
    "flash": "gemini-2.5-flash",  # Fast responses
    "pro": "gemini-2.5-pro"       # Deep analysis
}

MODEL_ASSIGNMENTS = {
    "gemini_quick_query": "flash",      # Speed priority
    "gemini_analyze_code": "pro",       # Depth priority
    "gemini_codebase_analysis": "pro"   # Context priority
}
```

### File Limits

- **Maximum file size**: 80KB (81,920 bytes)
- **Maximum lines**: 800 lines
- **Response format**: Plain text (no markdown)
- **Timeout handling**: Progress indicators for long tasks

### Environment Variables

```bash
GOOGLE_API_KEY=your_api_key_here       # For direct API access
GEMINI_FLASH_MODEL=gemini-2.5-flash   # Override default models
GEMINI_PRO_MODEL=gemini-2.5-pro       # Override default models
```

## Benefits

### For Developers

- **Instant access** to Gemini's advanced AI capabilities
- **Seamless integration** within Claude Code workflow
- **Smart model selection** - fast responses when speed matters, deep analysis when needed
- **Real-time feedback** during long analysis tasks

### For Code Quality

- **Security analysis** using Gemini's latest training data
- **Performance insights** from large-scale pattern recognition
- **Architecture guidance** based on current best practices
- **Error prevention** through pre-edit analysis

### For Productivity

- **Reduced context switching** - stay in Claude Code
- **Faster debugging** with AI-powered error analysis
- **Better decisions** through comprehensive code review
- **Learning acceleration** via instant expert guidance

## Project Structure

### Repository Structure

```
claude-gemini-mcp-slim/
├── .claude/                           # Complete slash commands system
│   ├── hooks.json                     # Hook definitions for Claude Code
│   ├── slash-commands.json            # 20+ slash command configurations
│   ├── README-SLASH-COMMANDS.md       # Slash commands documentation
│   └── scripts/
│       ├── slim_gemini_hook.py        # Hook execution script
│       └── slash_commands.py          # Slash commands implementation
├── gemini_mcp_server.py               # Main MCP server
├── gemini_helper.py                   # Standalone CLI utility
├── requirements.txt                   # Python dependencies (for reference)
├── SETUP/
│   ├── SETUP.md                      # Complete setup guide
│   └── codebase-security-analysis.jpg
├── CLAUDE.md                          # Comprehensive documentation
└── README.md                          # This overview
```

### Deployed Structure (After Setup)

```
~/mcp-servers/                              ← Shared MCP servers
├── shared-mcp-env/                         ← Virtual environment for all MCPs
└── gemini-mcp/                             ← Complete Gemini MCP package
    ├── gemini_mcp_server.py                ← Main MCP server
    └── .claude/                            ← Complete slash commands system
        ├── hooks.json                      ← Hook definitions
        ├── slash-commands.json             ← 20+ slash command configurations
        ├── README-SLASH-COMMANDS.md        ← Slash commands documentation
        └── scripts/
            ├── slim_gemini_hook.py         ← Hook execution script
            └── slash_commands.py           ← Slash commands implementation

your-projects/
├── project-a/
│   ├── .claude → ~/mcp-servers/gemini-mcp/.claude  ← Symlink for automated hooks
│   └── src/                               ← Your project files
└── project-b/
    └── components/                         ← Clean project (no MCP files needed)
```

### Hook Setup for Projects

**Important:** Unless hooks are already in your project's CLAUDE.md folder, you need to create a symlink to access the hooks from the shared MCP server location.

**Current Setup:**
- MCP server deployed to: `~/mcp-servers/gemini-mcp/`
- Hooks available at: `~/mcp-servers/gemini-mcp/.claude/`  
- Your projects: Separate locations (e.g., `/Users/username/projects/my-project/`)

**To enable hooks in any project:**

```bash
# Navigate to your project directory
cd /path/to/your/project

# Create symlink to shared MCP hooks
ln -s ~/mcp-servers/gemini-mcp/.claude .claude

# Verify symlink was created
ls -la .claude
```

**What this symlink enables:**
- Pre-edit analysis before file modifications
- Pre-commit security and quality reviews
- Session summaries when Claude Code sessions end
- **20+ slash commands** like `/g`, `/analyze`, `/security` for instant access

**Without the symlink:** MCP tools work manually, but automated hooks and slash commands won't be available in your project.

## Troubleshooting

### Common Issues

**MCP Server Won't Start**

- Check Python path in Claude Desktop configuration
- Verify virtual environment has `mcp` package installed
- Ensure file permissions allow execution

**Gemini Authentication Errors**

- Run `gemini` command to re-authenticate
- Check Google account has API access enabled
- Verify network connectivity

**No Tools Available in Claude Code**

- Restart Claude Desktop after configuration changes
- Check MCP server logs in Claude Desktop console
- Verify configuration JSON syntax

**API vs CLI Behavior**

- API calls are faster but require `GOOGLE_API_KEY`
- CLI fallback always available if Gemini CLI is installed (test for research & education ONLY)
- Model selection works the same for both approaches

## Advanced Usage

### Direct CLI Usage

```bash
# Quick questions
python gemini_helper.py query "How do I optimize this SQL query?"

# Code analysis
python gemini_helper.py analyze my_file.py security

# Full project analysis
python gemini_helper.py codebase ./src performance
```

### Custom Model Configuration

```bash
export GEMINI_FLASH_MODEL="gemini-2.5-flash-exp"
export GEMINI_PRO_MODEL="gemini-2.5-pro-exp"
export GOOGLE_API_KEY="your_api_key_here"
```

## Security

### ✅ Security Hardened Version

This version includes comprehensive security fixes addressing all critical vulnerabilities identified in earlier versions. All security issues have been resolved with production-ready defensive measures.

**🔒 [Complete Security Documentation](SECURITY.md)**

### Security Features Implemented

**Critical Vulnerabilities Fixed:**
- ✅ **Command Injection (CWE-78):** Eliminated `shell=True` usage, implemented secure subprocess execution
- ✅ **Path Traversal (CWE-22):** Added path validation and directory boundary enforcement  
- ✅ **Prompt Injection (CWE-94):** Implemented input sanitization and dangerous pattern filtering
- ✅ **Secrets Exposure (CWE-200):** Added API key redaction and secure error handling
- ✅ **Input Validation (CWE-20):** Comprehensive type checking and bounds validation

**Security Architecture:**
- **Defense in Depth:** Multi-layer security controls at input, processing, and output stages
- **Secure by Default:** Fail-safe error handling and minimal privilege execution
- **Zero Trust Input:** All user input sanitized and validated before processing
- **Audit Trail:** Comprehensive logging with sensitive data redaction

### Security Status

| Component | Security Status | Last Review |
|-----------|----------------|-------------|
| MCP Server | ✅ Hardened | 2025-01-12 |
| Helper CLI | ✅ Hardened | 2025-01-12 |
| Hook Scripts | ✅ Hardened | 2025-01-12 |
| Documentation | ✅ Complete | 2025-01-12 |

**Ready for Production Use** - All critical security issues resolved.

## Contributing

This project is designed to be lightweight and focused. The core functionality is complete, but contributions are welcome for:

- Additional analysis types
- Better error handling
- Performance optimizations
- Documentation improvements

## Slash Commands

### **Quick Access to All Tools**

No need to remember complex MCP tool names! Use simple slash commands:

```bash
# Core tools
/gemini "How do I implement OAuth2?"    # or /g
/analyze auth.py security               # or /a
/codebase ./src performance             # or /c

# Focus commands  
/security ./api                         # or /s
/performance database.js                # or /p
/architecture ./components              # or /arch

# Developer assistance
/explain "React useEffect"              # or /e
/debug "ReferenceError: fetch undefined" # or /d
/review UserForm.vue                    # or /r
/research "Vue 3 best practices"
/optimize queries.py
/test validation.js
/fix "CORS error in Express"
```

### **Easy Setup**

Copy the entire `.claude/` directory to any project:

```bash
# Method 1: Direct copy
cp -r /path/to/claude-gemini-mcp-slim/.claude /your/project/

# Method 2: Symlink (recommended for shared MCP)
cd /your/project
ln -s ~/mcp-servers/gemini-mcp/.claude .claude
```

**📖 [Complete Slash Commands Guide](.claude/README-SLASH-COMMANDS.md)**

## Changelog

### Version 1.1.0 (2025-01-12)

**New Features:**
- **20+ Slash Commands** - Easy shortcuts like `/g`, `/analyze`, `/security`
- **Smart Command Routing** - Automatically chooses the right MCP tool
- **Copy-Paste Ready** - Complete `.claude/` directory with all configurations
- **Enhanced Documentation** - Comprehensive slash commands guide
- **Improved Gitignore** - Protects user settings while sharing configurations

**Slash Commands Added:**
- Core: `/gemini`, `/g`, `/analyze`, `/a`, `/codebase`, `/c`
- Focus: `/security`, `/s`, `/performance`, `/p`, `/architecture`, `/arch`
- Assistance: `/explain`, `/e`, `/debug`, `/d`, `/review`, `/r`, `/research`
- Improvement: `/optimize`, `/test`, `/fix`
- Utilities: `/help`, `/status`, `/models`

**Technical Improvements:**
- Smart analysis logic that detects file vs directory targets
- Parameter mapping system for seamless MCP integration
- Comprehensive help system with examples and usage guides
- Error handling with helpful messages and usage hints

### Version 1.0.0 (2025-01-12)

**Major Release - Security Hardened Version**

**New Features:**
- Complete MCP server implementation with three core tools
- Smart model selection (Gemini Flash for speed, Pro for depth)
- Real-time streaming output with progress indicators
- Shared MCP architecture supporting multiple AI clients
- API-first approach with CLI fallback
- Comprehensive hook system for automated workflows

**Security Enhancements:**
- **CRITICAL:** Fixed command injection vulnerabilities (CWE-78)
- **CRITICAL:** Fixed path traversal vulnerabilities (CWE-22)
- **CRITICAL:** Fixed prompt injection vulnerabilities (CWE-94)
- **CRITICAL:** Fixed secrets exposure issues (CWE-200)
- **CRITICAL:** Enhanced input validation (CWE-20)
- Implemented defense-in-depth security architecture
- Added comprehensive security testing suite
- Created detailed security documentation

**Technical Improvements:**
- Replaced all `shell=True` usage with secure subprocess execution
- Added path validation and directory boundary enforcement
- Implemented input sanitization for all user inputs
- Added API key redaction in error handling
- Enhanced error handling with fail-safe defaults
- Optimized for production deployment

**Documentation:**
- Complete setup guide with 5-minute quick start
- Comprehensive security documentation
- Architecture diagrams and code examples
- Troubleshooting guides and best practices
- Professional deployment patterns

**Breaking Changes:**
- Removed vulnerable test files and insecure code patterns
- Enhanced security may reject previously accepted inputs
- File access restricted to current directory tree only

---

### Pre-1.0.0 Development Versions

**Initial Development (July 10-12, 2025):**
- Initial MCP server prototype (July 10)
- Basic Gemini CLI integration (July 10-11)
- Experimental hook implementations (July 11)
- Security vulnerability identification and analysis (July 11-12)

**Note:** Versions prior to 1.0.0 contained critical security vulnerabilities and should not be used in production environments.

## License

MIT License

Copyright (c) 2025 Dr Muhammad Aizat Hawari

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Credits

Special thanks to the following tools and platforms that assisted during the research and development of this MCP:

- **[Claude](https://claude.ai/)** - AI assistant for code development and documentation
- **[Perplexity](https://www.perplexity.ai/)** - AI-powered research and information gathering
- **[Warp Terminal](https://www.warp.dev/)** - Modern terminal for enhanced development workflow
