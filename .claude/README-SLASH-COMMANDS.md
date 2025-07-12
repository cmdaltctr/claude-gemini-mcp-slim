# Gemini MCP Slash Commands

**Easy-to-use shortcuts for all Gemini MCP tools**

## Quick Copy Setup

Copy the entire `.claude/` directory from this repo to your project:

```bash
# Method 1: Copy to your project
cp -r /path/to/claude-gemini-mcp-slim/.claude /path/to/your/project/

# Method 2: Create symlink (recommended for shared MCP setup)
cd /path/to/your/project
ln -s ~/mcp-servers/gemini-mcp/.claude .claude
```

## Available Commands

### 🚀 Core Tools
| Command | Description | Usage |
|---------|-------------|-------|
| `/gemini [query]` | Ask any development question | `/gemini How to optimize React performance?` |
| `/g [query]` | Quick alias for gemini | `/g Best practices for Vue 3?` |
| `/analyze [file]` | Analyze code with insights | `/analyze src/auth.py security` |
| `/a [file]` | Quick alias for analyze | `/a UserForm.vue` |
| `/codebase [dir]` | Analyze entire directories | `/codebase ./src security` |
| `/c [dir]` | Quick alias for codebase | `/c . all` |

### 🔍 Analysis Focus
| Command | Description | Usage |
|---------|-------------|-------|
| `/security [target]` | Security-focused analysis | `/security ./api` |
| `/s [target]` | Quick security alias | `/s auth.py` |
| `/performance [target]` | Performance analysis | `/performance ./components` |
| `/p [target]` | Quick performance alias | `/p database.js` |
| `/architecture [target]` | Architecture review | `/architecture ./src` |
| `/arch [target]` | Quick architecture alias | `/arch .` |

### 🛠️ Developer Assistance
| Command | Description | Usage |
|---------|-------------|-------|
| `/explain [concept]` | Explain code or concepts | `/explain async/await in JavaScript` |
| `/e [concept]` | Quick explain alias | `/e React useEffect` |
| `/debug [issue]` | Debug assistance | `/debug ReferenceError: fetch is not defined` |
| `/d [issue]` | Quick debug alias | `/d Memory leak in useEffect` |
| `/review [file]` | Code review | `/review src/utils.js` |
| `/r [file]` | Quick review alias | `/r Header.vue` |
| `/research [topic]` | Research best practices | `/research Vue 3 state management` |

### ⚡ Code Improvement
| Command | Description | Usage |
|---------|-------------|-------|
| `/optimize [target]` | Get optimization suggestions | `/optimize ./queries.js` |
| `/test [file]` | Generate test strategies | `/test validation.js` |
| `/fix [issue]` | Get specific solutions | `/fix CORS error in Express API` |

### 🔧 Utilities
| Command | Description | Usage |
|---------|-------------|-------|
| `/help [cmd]` | Show command help | `/help analyze` |
| `/status` | Check MCP connection | `/status` |
| `/models` | Show available models | `/models` |

## Smart Analysis

Commands automatically choose the right tool:

- **File targets** → Uses `gemini_analyze_code`
- **Directory targets** → Uses `gemini_codebase_analysis`  
- **Analysis types** → Maps to appropriate focus (security, performance, architecture)

## Examples

```bash
# Quick questions
/g How do I implement JWT in Node.js?
/e Promise.all vs Promise.allSettled

# Code analysis
/a src/auth.py security
/s ./api
/p components/UserList.vue

# Project analysis  
/c ./src security
/arch .

# Debug help
/d TypeError: Cannot read property 'map'
/fix CORS error in my API
/test utils/validation.js

# Research
/research React testing strategies 2025
/optimize database/queries.py
```

## Configuration

The commands are configured in `slash-commands.json`:

- **MCP Server**: `gemini-mcp`
- **Models**: Flash for quick queries, Pro for deep analysis
- **File Limits**: 80KB max, 800 lines max
- **Supported Types**: `.py`, `.js`, `.ts`, `.vue`, `.html`, `.css`, etc.

## How It Works

1. **Command Detection**: Recognizes slash commands in Claude Code
2. **Smart Routing**: Chooses appropriate MCP tool based on target type
3. **Parameter Mapping**: Automatically maps arguments to MCP tool parameters
4. **Error Handling**: Provides helpful error messages and usage hints

## Installation

### For Individual Projects
```bash
# Copy entire .claude directory
cp -r /path/to/claude-gemini-mcp-slim/.claude /your/project/
```

### For Shared MCP Setup (Recommended)
```bash
# Symlink to shared MCP hooks
cd /your/project
ln -s ~/mcp-servers/gemini-mcp/.claude .claude
```

## Benefits

### For Developers
- **Instant access** - No need to remember MCP tool names
- **Smart defaults** - Commands choose the right analysis type
- **Quick aliases** - Single-letter shortcuts for common tasks
- **Consistent syntax** - All commands follow same pattern

### For Teams
- **Easy onboarding** - Copy-paste setup for any project
- **Standardized workflow** - Same commands across all projects
- **Self-documenting** - Built-in help system

### For Productivity
- **Faster analysis** - Skip the "which tool should I use?" decision
- **Better discoverability** - Help system shows all options
- **Reduced friction** - Type `/s file.py` instead of complex MCP calls

## Advanced Usage

### Custom Analysis Types
```bash
/analyze auth.py security     # Security-focused
/analyze queries.js performance  # Performance-focused  
/analyze App.vue architecture    # Architecture-focused
```

### Batch Operations
```bash
/c ./src security     # Scan entire src for security issues
/p ./components      # Performance review of all components
/arch .              # Architecture review of full project
```

### Research and Learning
```bash
/research Python async patterns 2025
/explain design patterns in React
/debug why my Vue component won't update
```

This slash commands system transforms the Gemini MCP from powerful but complex tools into intuitive, developer-friendly shortcuts that anyone can use immediately.