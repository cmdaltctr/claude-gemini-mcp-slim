# Gemini MCP Server Configuration Guide

This guide explains how to configure the Gemini MCP Server. Don't worry if you're new to configuration files - we'll walk through everything step by step!

## Table of Contents
- [Understanding Configuration Priority](#understanding-configuration-priority)
- [Environment Variables Reference](#environment-variables-reference)
- [Complete Configuration File Template](#complete-configuration-file-template)
- [Common Configuration Examples](#common-configuration-examples)
- [Troubleshooting Configuration Issues](#troubleshooting-configuration-issues)

## Understanding Configuration Priority

### How Configuration Works
The system reads configuration settings from multiple sources and uses them in a specific order of priority. Think of it like this: if you have the same setting in multiple places, the system will use the "highest priority" version.

### Priority Order (Highest to Lowest)
1. **Explicit arguments** - Settings passed directly to functions in code
2. **Environment variables** - Settings in your shell environment (like `export GEMINI_FLASH_MODEL="gemini-2.5-pro"`)
3. **config.json file** - Settings in a configuration file in your project
4. **Hard-coded defaults** - Built-in fallback values

### Example of Priority in Action
Let's say you have:
- `config.json` sets `"cli_timeout": 60`
- Environment variable `CLI_TIMEOUT=120`
- Code explicitly passes `explicit_timeout=30`

The system will use `30` seconds (explicit argument wins), ignoring the other values.

## Environment Variables Reference

Environment variables are settings you can set in your terminal or shell profile. They're useful for:
- Keeping sensitive information (like API keys) out of your code
- Different settings for development vs production
- Quick temporary overrides without editing files

### Core Model Configuration Variables

#### `FORCE_MODEL`
**What it does:** Forces ALL operations to use a specific Gemini model, overriding all other model assignments.

**When to use:** 
- Testing a new model across all features
- Debugging model-specific issues
- Cost control (force everything to use the cheapest model)

**Examples:**
```bash
# Force everything to use flash model
export FORCE_MODEL="flash"

# Force everything to use a specific model version
export FORCE_MODEL="gemini-2.5-pro-exp-0827"

# Use directly in command
FORCE_MODEL="flash" python gemini_helper.py analyze myfile.py
```

#### `GEMINI_FLASH_MODEL`
**What it does:** Changes what model is used when code asks for the "flash" model.

**Default:** `gemini-2.5-flash`

**When to use:**
- You want to try a different "fast" model
- Google releases a new flash model version

**Examples:**
```bash
# Use the experimental flash model
export GEMINI_FLASH_MODEL="gemini-2.5-flash-exp-0827"

# Use the 8B variant
export GEMINI_FLASH_MODEL="gemini-2.5-flash-8b"
```

#### `GEMINI_PRO_MODEL`
**What it does:** Changes what model is used when code asks for the "pro" model.

**Default:** `gemini-2.5-pro`

**When to use:**
- You want to try a different "powerful" model
- Google releases a new pro model version

**Examples:**
```bash
# Use the experimental pro model
export GEMINI_PRO_MODEL="gemini-2.5-pro-exp-0827"
```

### Timeout Configuration Variables

#### `CLI_TIMEOUT`
**What it does:** Sets maximum time (in seconds) to wait for command-line operations.

**Default:** `60` seconds

**When to use:**
- Your internet is slow and operations time out
- You're processing large files and need more time
- You want faster failures for testing

**Examples:**
```bash
# Give operations more time (5 minutes)
export CLI_TIMEOUT=300

# Fail fast for testing (30 seconds)
export CLI_TIMEOUT=30
```

#### `API_TIMEOUT`
**What it does:** Sets maximum time (in seconds) to wait for direct API calls.

**Default:** `30` seconds

**When to use:**
- API calls are timing out due to slow connection
- You want to fail faster when API is down

**Examples:**
```bash
# More patience for slow connections
export API_TIMEOUT=60

# Fail fast for development
export API_TIMEOUT=15
```

### Size Limit Variables

#### `MAX_FILE_SIZE`
**What it does:** Sets maximum file size (in bytes) that can be analyzed.

**Default:** `81920` bytes (80 KB)

**When to use:**
- You need to analyze larger files
- You want to save on API costs by limiting file sizes

**Examples:**
```bash
# Allow larger files (200 KB)
export MAX_FILE_SIZE=204800

# Smaller limit for cost control (40 KB)
export MAX_FILE_SIZE=40960
```

#### `MAX_CODEBASE_SIZE`
**What it does:** Sets maximum total size (in bytes) for codebase analysis.

**Default:** `500000` bytes (500 KB)

**When to use:**
- You have a very large codebase
- You want to limit costs for codebase analysis

**Examples:**
```bash
# Allow larger codebases (1 MB)
export MAX_CODEBASE_SIZE=1048576

# Smaller limit (250 KB)
export MAX_CODEBASE_SIZE=250000
```

### Feature Toggle Variables

#### `ENABLE_MARKDOWN_CONVERSION`
**What it does:** Controls whether Gemini's markdown output is converted to plain text.

**Default:** `true`

**Valid values:** `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off`

**When to use:**
- You prefer raw markdown output
- You're debugging formatting issues

**Examples:**
```bash
# Disable markdown conversion
export ENABLE_MARKDOWN_CONVERSION=false

# Enable it explicitly
export ENABLE_MARKDOWN_CONVERSION=true
```

#### `ENABLE_SANITIZATION`
**What it does:** Controls input sanitization to prevent prompt injection attacks.

**Default:** `true`

**⚠️ Warning:** Only disable this if you trust all inputs completely!

**Examples:**
```bash
# Disable for debugging (NOT recommended for production)
export ENABLE_SANITIZATION=false
```

### Setting Environment Variables

#### Temporary (Current Session Only)
```bash
# Set for just this command
FORCE_MODEL="flash" python gemini_helper.py query "What is Python?"

# Set for current terminal session
export GEMINI_FLASH_MODEL="gemini-2.5-flash-8b"
```

#### Permanent (Add to Shell Profile)
```bash
# Add to ~/.zshrc (for zsh) or ~/.bashrc (for bash)
echo 'export GEMINI_FLASH_MODEL="gemini-2.5-flash-8b"' >> ~/.zshrc
echo 'export CLI_TIMEOUT=120' >> ~/.zshrc

# Reload your shell
source ~/.zshrc
```

#### Using .env Files
Create a file called `.env` in your project directory:
```bash
# .env file
GEMINI_FLASH_MODEL=gemini-2.5-flash-8b
CLI_TIMEOUT=120
MAX_FILE_SIZE=204800
```

## Complete Configuration File Template

The configuration file should be named `config.json` and placed in one of these locations:
- Current working directory: `./config.json`
- Current working directory: `./gemini_config.json`
- Home directory: `~/.gemini/config.json`
- Project config directory: `./.config/gemini.json`

### Full Template with Detailed Comments

```json
{
  "models": {
    "nicknames": {
      // Model nicknames - these are shortcuts to full model names
      // You can change these to point to different model versions
      "flash": "gemini-2.5-flash",           // Fast, cost-effective model
      "pro": "gemini-2.5-pro",               // More powerful, higher cost
      "flash-8b": "gemini-2.5-flash-8b",     // Smaller flash variant
      "flash-exp": "gemini-2.5-flash-exp-0827", // Experimental flash
      "pro-exp": "gemini-2.5-pro-exp-0827"   // Experimental pro
    },
    "assignments": {
      // Which model nickname each tool should use
      // Tools use these assignments unless overridden
      
      // MCP Server tools
      "gemini_quick_query": "flash",        // Simple questions - use fast model
      "gemini_analyze_code": "pro",         // Code analysis - use powerful model
      "gemini_codebase_analysis": "pro",    // Large analysis - use powerful model
      
      // Helper script tools
      "quick_query": "flash",               // Simple questions
      "analyze_code": "pro",                // Single file analysis
      "analyze_codebase": "pro",            // Multi-file analysis
      
      // Future tools (examples of how to add new ones)
      "pre_edit": "flash",                  // Pre-edit suggestions
      "pre_commit": "pro",                  // Pre-commit analysis
      "session_summary": "flash",           // Session summaries
      
      // How to add a new tool:
      // 1. Add "your_new_tool": "flash" or "pro" here
      // 2. In your code: register_tool_if_missing("your_new_tool", "flash")
      // 3. Use cfg.get_model("your_new_tool") to get the model
      "example_new_tool": "flash",
      "another_tool": "pro"
    }
  },
  
  "limits": {
    // Size and content limits to prevent issues and control costs
    
    "max_file_size": 81920,              // Max file size in bytes (80 KB)
    "max_lines": 800,                    // Max lines in a single file
    "max_prompt_size": 1000000,          // Max prompt size in bytes (1 MB)
    "max_codebase_size": 500000,         // Max total codebase size (500 KB)
    "max_context_window": 1048576,       // Max tokens (~1M tokens)
    "sanitization_max_length": 100000    // Max length before sanitization truncates
  },
  
  "timeouts": {
    // Timeout settings in seconds
    
    "cli_timeout": 60,                   // How long to wait for CLI commands
    "api_timeout": 30,                   // How long to wait for API calls
    "stream_timeout": 90,                // How long to wait for streaming responses
    "analysis_timeout": 300              // How long to wait for large analysis (5 min)
  },
  
  "api_config_paths": [
    // Where to look for API keys (in order)
    "~/.config/claude-code/mcp_config.json",
    "~/Library/Application Support/Claude/claude_desktop_config.json",
    ".env",
    "gemini/.env"
  ],
  
  "security": {
    // Security settings to protect against malicious inputs
    
    "enable_sanitization": true,         // Clean inputs to prevent injection
    "allow_path_traversal": false,       // Block access outside project directory
    "allowed_extensions": [              // File types that can be analyzed
      // Programming languages
      ".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs",
      ".vue", ".html", ".css", ".scss", ".sass", ".jsx", ".tsx",
      ".go", ".php", ".rb", ".swift", ".kt", ".scala",
      
      // Config and documentation
      ".json", ".yaml", ".yml", ".toml", ".md", ".txt",
      
      // Scripts
      ".sh", ".bat", ".ps1"
    ]
  },
  
  "execution": {
    // How the system should behave during execution
    
    "prefer_api_over_cli": true,         // Try API first, fallback to CLI
    "enable_progress_indicators": true,   // Show progress during long operations
    "enable_markdown_conversion": true,   // Convert markdown output to plain text
    "enable_streaming": true,            // Stream output in real-time
    "max_parallel_processes": 4          // Max concurrent operations
  }
}
```

### Minimal Configuration Example
If you only want to change a few settings, you don't need the full template. Here's a minimal example:

```json
{
  "models": {
    "assignments": {
      "quick_query": "pro",
      "analyze_code": "pro"
    }
  },
  "timeouts": {
    "cli_timeout": 120
  }
}
```

## Common Configuration Examples

### 1. Cost-Optimized Setup (Use Flash for Everything)
**Use case:** You want to minimize API costs by using the fastest, cheapest model for all operations.

**Trade-off:** Lower cost, but potentially less detailed analysis for complex tasks.

```json
{
  "models": {
    "assignments": {
      "gemini_quick_query": "flash",
      "gemini_analyze_code": "flash",
      "gemini_codebase_analysis": "flash",
      "quick_query": "flash",
      "analyze_code": "flash",
      "analyze_codebase": "flash"
    }
  }
}
```

**Environment variable alternative:**
```bash
export FORCE_MODEL="flash"
```

### 2. Performance-Optimized Setup (Mixed Models)
**Use case:** Balance between cost and quality - use flash for simple tasks, pro for complex analysis.

**Trade-off:** Higher cost for complex tasks, but better quality analysis.

```json
{
  "models": {
    "assignments": {
      "gemini_quick_query": "flash",        // Simple questions - cheap
      "gemini_analyze_code": "pro",         // Code analysis - quality matters
      "gemini_codebase_analysis": "pro",    // Large analysis - quality matters
      "quick_query": "flash",
      "analyze_code": "pro",
      "analyze_codebase": "pro"
    }
  }
}
```

### 3. Quality-First Setup (Use Pro for Everything)
**Use case:** Cost is not a concern, you want the best possible analysis quality.

**Trade-off:** Higher costs, but maximum quality for all operations.

```json
{
  "models": {
    "assignments": {
      "gemini_quick_query": "pro",
      "gemini_analyze_code": "pro",
      "gemini_codebase_analysis": "pro",
      "quick_query": "pro",
      "analyze_code": "pro",
      "analyze_codebase": "pro"
    }
  }
}
```

**Environment variable alternative:**
```bash
export FORCE_MODEL="pro"
```

### 4. Experimental Models Setup
**Use case:** You want to test the latest experimental models.

**Trade-off:** Cutting-edge features, but potentially less stable.

```json
{
  "models": {
    "nicknames": {
      "flash": "gemini-2.5-flash-exp-0827",
      "pro": "gemini-2.5-pro-exp-0827"
    }
  }
}
```

### 5. Large File Processing Setup
**Use case:** You work with larger files and codebases than the defaults allow.

```json
{
  "limits": {
    "max_file_size": 204800,             // 200 KB instead of 80 KB
    "max_codebase_size": 1048576,        // 1 MB instead of 500 KB
    "max_lines": 1600                    // 1600 lines instead of 800
  },
  "timeouts": {
    "cli_timeout": 180,                  // 3 minutes instead of 1 minute
    "analysis_timeout": 600              // 10 minutes for very large analysis
  }
}
```

### 6. Development/Testing Setup
**Use case:** Fast feedback during development, with debugging features enabled.

```json
{
  "models": {
    "assignments": {
      "gemini_quick_query": "flash",
      "gemini_analyze_code": "flash",
      "gemini_codebase_analysis": "flash"
    }
  },
  "timeouts": {
    "cli_timeout": 30,                   // Fail fast for quick iteration
    "api_timeout": 15
  },
  "execution": {
    "enable_markdown_conversion": false,  // See raw output for debugging
    "enable_progress_indicators": true
  }
}
```

### 7. Production/Stable Setup
**Use case:** Reliable configuration for production use with conservative settings.

```json
{
  "models": {
    "nicknames": {
      "flash": "gemini-2.5-flash",         // Use stable versions
      "pro": "gemini-2.5-pro"
    }
  },
  "timeouts": {
    "cli_timeout": 120,                  // Generous timeouts
    "api_timeout": 60,
    "analysis_timeout": 600
  },
  "security": {
    "enable_sanitization": true,         // Maximum security
    "allow_path_traversal": false
  },
  "execution": {
    "prefer_api_over_cli": true,         // API is more reliable
    "enable_streaming": false            // Batch processing for stability
  }
}
```

## Troubleshooting Configuration Issues

### Common Problems and Solutions

#### Problem: "Invalid or missing API key"
**Symptoms:**
- Error messages about API key validation
- System falls back to CLI when you expect API usage

**Solutions:**
1. **Check environment variable:**
   ```bash
   echo $GOOGLE_API_KEY
   # Should show your API key (partially hidden)
   ```

2. **Check API key length:**
   ```bash
   echo ${#GOOGLE_API_KEY}
   # Should be more than 10 characters
   ```

3. **Check API key in configuration files:**
   ```bash
   # Check Claude Code MCP config
   cat ~/.config/claude-code/mcp_config.json
   
   # Check Claude Desktop config
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

4. **Check project .env file:**
   ```bash
   cat .env
   cat gemini/.env
   ```

5. **Set API key properly:**
   ```bash
   export GOOGLE_API_KEY="your-actual-api-key-here"
   ```

#### Problem: "Configuration loading failed"
**Symptoms:**
- System reports configuration errors on startup
- Falls back to default settings unexpectedly

**Solutions:**
1. **Check JSON syntax:**
   ```bash
   # Use a JSON validator
   python -m json.tool config.json
   ```

2. **Check file permissions:**
   ```bash
   ls -la config.json
   # Should be readable (r--r--r-- or similar)
   ```

3. **Check file location:**
   ```bash
   # System looks in these locations:
   ls -la ./config.json
   ls -la ./gemini_config.json
   ls -la ~/.gemini/config.json
   ls -la ./.config/gemini.json
   ```

4. **Start with minimal config:**
   ```json
   {
     "models": {
       "assignments": {
         "quick_query": "flash"
       }
     }
   }
   ```

#### Problem: "Model assignment warnings"
**Symptoms:**
- Warnings like "Invalid model assignment for tool_name"
- Tools using unexpected models

**Solutions:**
1. **Check model nicknames exist:**
   ```json
   {
     "models": {
       "nicknames": {
         "flash": "gemini-2.5-flash",
         "pro": "gemini-2.5-pro"
       },
       "assignments": {
         "my_tool": "flash"  // "flash" must exist in nicknames
       }
     }
   }
   ```

2. **Check spelling in assignments:**
   - Tool names are case-sensitive
   - Model nicknames are case-sensitive

3. **Use valid model nicknames:**
   - Built-in: `flash`, `pro`, `flash-8b`, `flash-exp`, `pro-exp`
   - Or full model names like `gemini-2.5-flash`

#### Problem: "Timeout errors"
**Symptoms:**
- Operations fail with timeout messages
- Partial results with timeout warnings

**Solutions:**
1. **Increase timeout values:**
   ```json
   {
     "timeouts": {
       "cli_timeout": 120,    // Double the default
       "api_timeout": 60,     // Double the default
       "analysis_timeout": 600 // For very large files
     }
   }
   ```

2. **Use environment variables for quick testing:**
   ```bash
   CLI_TIMEOUT=180 python gemini_helper.py analyze large_file.py
   ```

3. **Check your internet connection:**
   ```bash
   ping google.com
   ```

4. **Try API vs CLI:**
   ```json
   {
     "execution": {
       "prefer_api_over_cli": false  // Try CLI if API is slow
     }
   }
   ```

#### Problem: "File too large" or "Path outside allowed directory"
**Symptoms:**
- Files rejected with size errors
- Security errors about file paths

**Solutions:**
1. **Increase file size limits:**
   ```json
   {
     "limits": {
       "max_file_size": 204800,      // Increase as needed
       "max_codebase_size": 1048576  // For codebase analysis
     }
   }
   ```

2. **Check file paths:**
   ```bash
   # Make sure you're in the right directory
   pwd
   
   # Check file exists and is readable
   ls -la your_file.py
   ```

3. **Use relative paths:**
   ```bash
   # Good
   python gemini_helper.py analyze ./src/main.py
   
   # Bad (might trigger security check)
   python gemini_helper.py analyze /absolute/path/to/file.py
   ```

#### Problem: "Environment variables not taking effect"
**Symptoms:**
- Setting environment variables but seeing no change
- System still uses default values

**Solutions:**
1. **Check if variable is set:**
   ```bash
   env | grep GEMINI
   env | grep FORCE_MODEL
   ```

2. **Export variables properly:**
   ```bash
   # Wrong - only sets for current command
   FORCE_MODEL="flash"
   
   # Right - exports to environment
   export FORCE_MODEL="flash"
   ```

3. **Check variable spelling:**
   - `FORCE_MODEL` (not `FORCED_MODEL`)
   - `CLI_TIMEOUT` (not `CLI_TIMEOUT_SEC`)
   - `GEMINI_FLASH_MODEL` (not `GEMINI_FLASH`)

4. **Restart your shell:**
   ```bash
   # If you added to ~/.zshrc or ~/.bashrc
   source ~/.zshrc
   ```

#### Problem: "Unknown tool" errors
**Symptoms:**
- Tools report as unknown or unregistered
- Missing model assignments for new tools

**Solutions:**
1. **Register new tools in config:**
   ```json
   {
     "models": {
       "assignments": {
         "your_new_tool": "flash"
       }
     }
   }
   ```

2. **Use the registration pattern in code:**
   ```python
   from config import register_tool_if_missing
   
   # Register your tool with default model
   register_tool_if_missing("your_new_tool", "flash")
   
   # Then use it
   model = cfg.get_model("your_new_tool")
   ```

### Getting Help and Debugging

#### Enable Debug Logging
```bash
# Set logging level for more details
export PYTHONPATH=.:$PYTHONPATH
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

#### Check Current Configuration
```python
# Run this to see your current configuration
from config import get_config

cfg = get_config()
print("Current config:")
import json
print(json.dumps(cfg.get_raw_config(), indent=2))
```

#### Test Basic Functionality
```bash
# Test basic query
python gemini_helper.py query "Hello, world!"

# Test with specific model
FORCE_MODEL="flash" python gemini_helper.py query "Hello, world!"
```

#### Common Log Messages and What They Mean

- `"Configuration loaded successfully"` - Good! Config file was read properly
- `"No API key found in any location"` - System will use CLI instead of API
- `"Applying FORCE_MODEL override"` - Your FORCE_MODEL setting is working
- `"Invalid model assignment for tool_name, using 'flash'"` - Check your model assignments
- `"Failed to load config file"` - Check JSON syntax and file permissions

Remember: When in doubt, start with the simplest possible configuration and build up from there. The system is designed to work with sensible defaults, so you only need to configure what you want to change!
