# Claude Gemini MCP Integration

<!-- CI workflow trigger -->
![Version](https://img.shields.io/badge/version-1.3.1-blue.svg)
![Security](https://img.shields.io/badge/security-hardened-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-brightgreen.svg)
![Status](https://img.shields.io/badge/status-production%20ready-green.svg)
![Slash Commands](https://img.shields.io/badge/slash%20commands-20+-orange.svg)

> **🚀 What's Coming Next:**
> I'm building an **AI Agent Feedback Loop System** that enables intelligent collaboration between Claude Code and Gemini AI. This will create a continuous improvement cycle where both AI agents learn from each other's suggestions, creating smarter code analysis and more contextual development assistance. Starting with Claude Code, then expanding to other IDEs. Stay tuned!

**A lightweight integration that brings Google's Gemini AI capabilities to Claude Code through MCP (Model Context Protocol)**

This project connects Claude Code (your coding assistant) with Google's Gemini AI models. Think of it as adding a second AI expert to your development team - one that can read and understand massive amounts of code at once (1M+ tokens, which is like reading hundreds of code files simultaneously).

With this integration, you can ask Gemini questions about your code, get security reviews, performance suggestions, and architectural advice - all without leaving your coding environment. It automatically chooses the right AI model for each task: fast responses for quick questions, deeper analysis for complex problems.

## Table of Contents

- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Architecture Overview](#architecture-overview)
  - [Key Benefits](#key-benefits)
  - [File Structure](#file-structure)
  - [Project Structure](#project-structure-with-hooks-enabled)
  - [Multi-Client Support](#multi-client-support)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
  - [Quick Development Questions](#quick-development-questions)
  - [Code Analysis](#code-analysis)
  - [Full Project Analysis](#full-project-analysis)
  - [Automated Hooks System](#automated-hooks-system)
- [Benefits](#benefits)
  - [For Developers](#for-developers)
  - [For Code Quality](#for-code-quality)
  - [For Productivity](#for-productivity)
- [Usage Examples with Slash Commands](#usage-examples-with-slash-commands)
- [What's Next?](#whats-next)
- [Need Help?](#need-help)
- [Further Documentation](#further-documentation)
- [Changelog](#changelog)
- [Contributing](#contributing)
- [License](#license)
- [Credits](#credits)

## Key Features

- **Quick Query** - Ask Gemini any development question instantly
- **Code Analysis** - Deep analysis with security, performance, and architecture insights
- **Codebase Analysis** - Full project analysis using Gemini's massive context window
- **Automated Hooks** - Pre-edit analysis, pre-commit review, and session summaries
- **20+ Slash Commands** - Simple shortcuts like `/g`, `/analyze`, `/security`
- **Smart Model Selection** - Flash for speed, Pro for depth, automatic fallback
- **Real-time Streaming** - Live output with progress indicators

## How It Works

```
Claude Code ←→ MCP Server ←→ Gemini CLI/API ←→ Google Gemini Models
                    ↓
            Smart Model Selection
            (Flash for speed, Pro for depth)
```

## Architecture Overview

The Gemini MCP server uses a shared architecture where one installation serves multiple AI clients and projects:

```
    Claude Desktop  │  Claude Code  │  Cursor IDE  │  VS Code + Extensions
                    │              │             │
                    └──────────────┼─────────────┘
                                   │
                      ┌─────────────────────────┐
                      │     MCP Protocol        │
                      │   (Tool Requests)       │
                      └─────────────────────────┘
                                   │
                          ┌─────────────────┐
                          │  Gemini MCP     │
                          │    Server       │
                          │ (Python/Shell)  │
                          └─────────────────┘
                                   │
                    ┌───────────────┼───────────────┐
                    │               │               │
          ┌─────────────────┐  ┌─────────────────┐  │
          │  Gemini API     │  │  Gemini CLI     │  │
          │  (Direct HTTP)  │  │  (Shell Command)│  │
          └─────────────────┘  └─────────────────┘  │
                    │               │               │
                    └───────────────┼───────────────┘
                                   │
                      ┌─────────────────────────┐
                      │   Google Gemini AI      │
                      │   (1M+ Token Context)   │
                      └─────────────────────────┘
```

### Key Benefits

- **One installation** serves all AI clients and projects
- **No project pollution** - keeps your projects clean
- **Easy maintenance** - update once, benefits everywhere
- **Smart fallbacks** - API-first approach with CLI backup

### File Structure

```
~/mcp-servers/                              ← Central location for all MCP servers
├── shared-mcp-env/                         ← Shared virtual environment
│   ├── bin/python                         ← Python interpreter for all MCPs
│   └── lib/python3.x/site-packages/       ← Shared dependencies (mcp, google-generativeai, etc.)
└── gemini-mcp/                             ← Complete Gemini MCP package
    ├── gemini_mcp_server.py                ← Main MCP server
    └── .claude/                            ← Complete slash commands system
        ├── hooks.json                      ← Hook definitions
        ├── commands/                       ← Native slash commands (10+ commands)
        │   ├── gemini.md                   ← /gemini command
        │   ├── analyze.md                  ← /analyze command
        │   └── ...                         ← Other command definitions
        └── scripts/
            └── slim_gemini_hook.py         ← Hook execution script
```

### Project Structure (with hooks enabled)

```
your-project/
├── .claude → ~/mcp-servers/gemini-mcp/.claude  ← Symlink to shared hooks
├── src/                                    ← Your project files
├── README.md
└── (no venv or MCP files needed!)           ← Clean project structure
```

### Multi-Client Support

The shared MCP architecture supports multiple AI clients simultaneously:

**Supported Clients:**
- Claude Desktop - Core MCP tools only
- Claude Code - Core MCP tools + hooks (if configured)
- VS Code with Claude Code extension - Core MCP tools + hooks (if configured)
- Cursor IDE - Core MCP tools only
- Windsurf - Core MCP tools only
- VS Code with other MCP extensions - Core MCP tools only
- Any MCP-compatible client - Core MCP tools only

**Important:** Hook functionality (.claude/hooks.json) is exclusive to Claude Code ecosystem (Claude Code standalone + VS Code with Claude Code extension). No other AI client currently supports this automation system.

## Quick Start

**New to this project?** Here's what you need to do:

1. **Get your Google API key** from [Google AI Studio](https://makersuite.google.com/)
2. **Follow the complete setup guide** in [docs/SETUP/SETUP.md](docs/SETUP/SETUP.md)
3. **Test the integration** with a simple query
4. **Explore the 20+ slash commands** in [docs/README-SLASH-COMMANDS.md](docs/README-SLASH-COMMANDS.md)

**Installation time:** ~5 minutes | **Prerequisites:** Python 3.10+, Node.js 16+

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

### Codebase Analysis with Code Analyzer

```
Use analyze_codebase from helpers.code_analyzer for:
- Comprehensive project analysis
- Structure and tech stack inspection
- Architecture patterns and design insights

Example:

result = analyze_codebase('/path/to/project')
print(f"Total files: {result.structure.total_files}")
print(f"Primary language: {result.project_report['summary']['primary_language']}")
```

### Full Project Analysis

```
Use gemini_codebase_analysis for:
- Overall architecture assessment
- Security vulnerability scanning
- Performance bottleneck identification
```

### Hybrid Progress Streaming

The system includes a sophisticated hybrid progress utility that provides visual feedback during operations:

```python
# Quick operations with spinner
from hybrid_progress import create_spinner_progress

progress = create_spinner_progress("🤖 Gemini Query")
progress.start("Processing request")

# Your operation here...
time.sleep(2)

# Stream response in chunks
response_chunks = ["Here's", "your", "detailed", "response"]
for chunk in response_chunks:
    progress.stream_chunk(chunk + " ")
    time.sleep(0.1)

progress.complete("Query completed")
```

```python
# Code analysis with pulse indicator
from hybrid_progress import create_pulse_progress

progress = create_pulse_progress("📊 Code Analysis")
progress.start("Analyzing structure")

# Analysis phases
phases = ["Security scan", "Performance check", "Best practices"]
for phase in phases:
    progress.config.prefix = f"🔍 {phase} "
    # Your analysis logic here
    time.sleep(1)

progress.stream_chunk("Analysis complete!\n")
progress.complete("Code analysis finished")
```

```python
# Long operations with progress bar
from hybrid_progress import create_bar_progress

progress = create_bar_progress("📈 Codebase Scan", width=30, show_elapsed=True)
progress.start("Initializing scan")

# Multi-phase operation
for phase_name in ["Structure", "Security", "Performance", "Report"]:
    progress.config.prefix = f"🔍 {phase_name} "
    # Your processing here
    time.sleep(1.5)

# Stream final results
for line in final_report.split('\n'):
    progress.stream_chunk(line + "\n")
    time.sleep(0.05)

progress.complete("Comprehensive scan completed")
```

### Automated Hooks System

```
The hooks system provides intelligent automation that runs at key development moments:

Pre-edit Analysis:
- Automatically analyzes files before Claude Code edits them
- Provides context about security, performance, and architecture concerns
- Helps prevent issues by informing Claude Code before changes are made

Pre-commit Review:
- Analyzes staged changes before git commits
- Reviews code for critical bugs, security vulnerabilities, and quality issues
- Provides final quality check before code enters version control

Session Summary:
- Generates brief recap when Claude Code session ends
- Highlights key changes made and potential next steps
- Maintains development context between sessions
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

## Usage Examples with Slash Commands

The slash commands provide a much simpler way to access Gemini's powerful analysis without remembering the full MCP tool syntax:

```
# Instead of typing:
/mcp__gemini-mcp__gemini_quick_query "How do I implement JWT authentication in Node.js?"

# You can simply use:
/gemini How do I implement JWT authentication in Node.js?
# or even shorter:
/g How do I implement JWT authentication in Node.js?
```

```
# Instead of typing:
/mcp__gemini-mcp__gemini_codebase_analysis "./src" security

# You can simply use:
/codebase ./src security
# or even shorter:
/c ./src security
```

See [docs/README-SLASH-COMMANDS.md](docs/README-SLASH-COMMANDS.md) for all available shortcuts.

## What's Next?

Once everything is working:

1. **Try the tools** - Start with simple queries: `/mcp__gemini-mcp__gemini_quick_query "How do I optimize React performance?"`
2. **Analyze some code** - Analyze specific functions: `/mcp__gemini-mcp__gemini_analyze_code "your function code here" security`
3. **Review your project** - Get architectural insights: `/mcp__gemini-mcp__gemini_codebase_analysis "./src" architecture`
4. **Explore slash commands** - Check `docs/README-SLASH-COMMANDS.md` for 20+ shortcuts

## Need Help?

- **Submit an Issue:** If you encounter any problems, please submit an issue on our [GitHub repository](https://github.com/cmdaltctr/claude-gemini-mcp-slim/issues) with details about your environment, steps to reproduce, and any error messages you received.
- **Use Labels:** When submitting issues, please use appropriate labels/tags such as `bug`, `feature-request`, `documentation`, and so on ([available labels](https://github.com/cmdaltctr/claude-gemini-mcp-slim/labels)) to help us categorize and address your concerns more efficiently.
- **Test files:** Check the `tests/` folder for examples and testing scripts
- **Slash commands:** See `docs/README-SLASH-COMMANDS.md` for comprehensive command reference
- **Console Logs:** Check your Claude Desktop/Code console for detailed error messages that can help diagnose issues

## Further Documentation

- [docs/SETUP/SETUP.md](docs/SETUP/SETUP.md) - Complete installation and configuration guide
- [docs/README-SLASH-COMMANDS.md](docs/README-SLASH-COMMANDS.md) - Slash commands reference
- [docs/SECURITY.md](docs/SECURITY.md) - Security documentation and hardening details
- [docs/TESTING.md](docs/TESTING.md) - Testing guide and best practices

## Changelog

**📋 Complete Changelog:** For detailed release notes and full version history, see [docs/CHANGELOG.md](docs/CHANGELOG.md)

## Contributing

This project is designed to be lightweight and focused. The core functionality is complete, but contributions are welcome for:

- Additional analysis types
- Better error handling
- Performance optimizations
- Documentation improvements

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**: Implement your feature or bug fix
4. **Test with MCP integration**: Ensure your changes work with this repo's MCP server
5. **Submit a pull request**: Push to your fork and submit a PR to the main repository

### Development Guidelines

- **Clean Python Code**: Use type hints, docstrings, and follow the existing code structure
- **Security-First Approach**: Implement proper input sanitization and API key protection
- **Modular Design**: Keep functions focused and reusable with clear error handling
- **MCP Protocol Compliance**: Follow the MCP server specifications for all tools
- **Comprehensive Documentation**: Document all tools with clear descriptions and schemas
- **Concise Code Comments**: Add brief comments to explain code blocks' purpose and functionality
- **Fallback Mechanisms**: Implement API with CLI fallbacks for resilience
- **Testing**: Verify changes work with both direct API and CLI integrations

### Development Setup

To set up a local development environment for this MCP server:

#### Quick Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-gemini-mcp-slim.git
cd claude-gemini-mcp-slim

# Run the automated setup script
./setup-dev.sh
```

The setup script will:
- Create a Python virtual environment (`.venv`)
- Install all production and development dependencies
- Set up unified Husky hooks for code quality and commit validation
- Run a quick test to verify everything is working

#### Manual Setup

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up unified Husky hooks (handled by setup-dev.sh)
# This includes pre-commit formatting/linting and commit-msg validation

# Run tests
python -m pytest
```

#### Development Workflow

Once set up, your typical development workflow will be:

```bash
# Activate virtual environment
source .venv/bin/activate

# Make your changes
# ...

# Run tests
python -m pytest

# Run Husky hooks manually (optional, they run automatically on commit)
.husky/pre-commit  # Run formatting, linting, and tests
.husky/commit-msg  # Validate commit message format

# Commit changes (pre-commit hooks will run automatically)
git add .
git commit -m "Your commit message"
```

**Important Notes:**
- The virtual environment (`.venv`) is automatically ignored by git
- Husky hooks will run automatically on every commit to ensure code quality and enforce conventional commit messages
- If you're using an IDE like Windsurf, make sure it's configured to use the virtual environment

## License

MIT License

Copyright (c) 2025 Dr Muhammad Aizat Hawari

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

## Credits

Special thanks to the following tools and platforms that assisted during the research and development of this MCP:

- **[Claude](https://claude.ai/)** - AI assistant for code development and documentation
- **[Perplexity](https://www.perplexity.ai/)** - AI-powered research and information gathering
- **[Warp Terminal](https://www.warp.dev/)** - Modern terminal for enhanced development workflow
