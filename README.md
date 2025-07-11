# Claude Gemini MCP Integration

**A lightweight integration that brings Google's Gemini AI capabilities to Claude Code through MCP (Model Context Protocol)**

## What This Does

This project creates a bridge between Claude Code and Google's Gemini AI models, giving you access to Gemini's powerful 1M+ token context window and latest AI capabilities directly within your Claude Code development environment.

## Key Features

### 🚀 **Three Powerful Tools**

- **Quick Query** - Ask Gemini any development question instantly
- **Code Analysis** - Deep analysis of specific code sections with security, performance, and architecture insights
- **Codebase Analysis** - Full project analysis using Gemini's massive context window

### 🔧 **Smart Model Selection**

- **Gemini Flash** - Fast responses for quick questions and simple tasks
- **Gemini Pro** - Deep analysis for complex code review and architecture decisions
- **Automatic fallback** - Direct API calls with CLI backup

### ⚡ **Real-time Streaming**

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

### 1. Install Prerequisites

```bash
# Install Gemini CLI
npm install -g @google/gemini-cli
gemini  # Authenticate with Google

# Install Python dependencies
pip install mcp python-dotenv google-generativeai
```

### 2. Configure Claude Code

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "gemini mcp": {
      "command": "/path/to/venv/bin/python3",
      "args": ["/path/to/gemini_mcp_server.py"],
      "env": {}
    }
  }
}
```
---

**Follow the [setup guide](SETUP/SETUP.md) to get started in 5 minutes!**

---

### 3. Test the Integration

```bash
# Test Gemini CLI
gemini -p "Hello, test connection"

# Restart Claude Desktop and look for "gemini mcp" tools
```

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

```
claude-gemini-mcp-slim/
├── .claude/                  # Hook configuration (optional automation)
│   ├── hooks.json           # Hook definitions for Claude Code
│   └── scripts/
│       └── slim_gemini_hook.py  # Hook execution script
├── gemini_mcp_server.py      # Main MCP server (Claude Code integration)
├── gemini_helper.py          # Standalone CLI utility
├── requirements.txt          # Python dependencies
├── venv/                     # Virtual environment
├── SETUP/
│   ├── SETUP.md             # Quick setup guide
│   └── codebase-security-analysis.jpg
├── CLAUDE.md                 # Comprehensive documentation
└── README.md                 # This overview
```

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
- CLI fallback always available if Gemini CLI is installed
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

### **WARNING** Notice about Security Analysis of this MCP

The codebase has multiple critical security vulnerabilities requiring immediate attention before using it in production:

Critical Issues (🚨 HIGH PRIORITY)

1. Arbitrary File Read Vulnerability (MCP Server)

- gemini_mcp_server.py allows unrestricted file access via path traversal
- Risk: Read system credentials, private keys, any accessible file
- Location: gemini_mcp_server.py:276-277

2. Prompt Injection Vulnerabilities

- Both MCP server and hook scripts vulnerable to malicious prompts
- Risk: AI model instruction hijacking, bypassing security reviews
- Locations: Multiple prompt construction areas

3. Command Injection Risk (Hook Script)

- Environment variables used directly in subprocess calls
- Risk: Arbitrary command execution via model name manipulation
- Location: .claude/scripts/slim_gemini_hook.py:117

Security Configuration Issues

4. Unsafe Subprocess Usage

- Test files use shell=True with user input
- Hook configurations execute with elevated timeouts (300s)
- Missing input validation and sanitization

5. Secrets Exposure Risk

- API keys logged in error messages
- Broad exception handling may expose sensitive data
- No log sanitization implemented

Recommended Immediate Actions

1. Implement file access restrictions - Add workspace directory validation
2. Add prompt injection defenses - System prompts, input sanitization
3. Validate environment variables - Allowlist model names
4. Remove shell=True usage - Use secure subprocess patterns
5. Sanitize logging - Remove sensitive data from error messages

The codebase requires significant security hardening before production use.

## Contributing

This project is designed to be lightweight and focused. The core functionality is complete, but contributions are welcome for:

- Additional analysis types
- Better error handling
- Performance optimizations
- Documentation improvements

## License

MIT License

Copyright (c) 2025 Dr Muhammad Aizat Hawari

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.


