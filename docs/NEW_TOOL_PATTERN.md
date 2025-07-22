# New Tool Scaffolding Pattern

This document describes the recommended pattern for adding new tools to the Gemini MCP system with automatic configuration management.

## Quick Start

For any new tool, follow these 3 simple steps:

```python
# 1. Import the configuration system
from config import get_config, register_tool_if_missing

# 2. Register your tool with a default model during initialization
register_tool_if_missing("my_new_tool", "flash")  # or "pro"

# 3. Get the configured model for your tool
cfg = get_config()
model_name = cfg.get_model("my_new_tool")
```

## Detailed Integration Guide

### Step 1: Import Configuration System

```python
from config import get_config, register_tool_if_missing
```

### Step 2: Register Tool During Initialization

Call `register_tool_if_missing()` early in your tool's initialization:

```python
def initialize_my_tool():
    # Register tool with default model if not already configured
    register_tool_if_missing("my_new_tool", "flash")  # Use "flash" for fast tools
    # or
    register_tool_if_missing("my_analysis_tool", "pro")  # Use "pro" for thorough analysis
```

**Available Model Nicknames:**
- `"flash"` - gemini-2.5-flash (fast, lightweight)
- `"pro"` - gemini-2.5-pro (thorough, comprehensive)  
- `"flash-8b"` - gemini-2.5-flash-8b (experimental fast)
- `"flash-exp"` - gemini-2.5-flash-exp-0827 (experimental)
- `"pro-exp"` - gemini-2.5-pro-exp-0827 (experimental pro)

### Step 3: Use the Configuration

```python
def my_tool_function():
    cfg = get_config()
    
    # Get the model for your tool (handles all precedence automatically)
    model_name = cfg.get_model("my_new_tool")
    
    # Get other configuration values
    max_file_size = cfg.get_limit("max_file_size")
    timeout = cfg.get_timeout("cli_timeout")
    
    # Use model_name with your API calls
    result = gemini_api_call(model=model_name, prompt=my_prompt)
```

## Configuration Precedence

The system automatically handles configuration precedence in this order:

1. **Explicit function arguments** (highest priority)
2. **Environment variables** (GEMINI_FLASH_MODEL, GEMINI_PRO_MODEL, etc.)
3. **config.json file** (in working directory or standard locations)
4. **Hard-coded defaults** (lowest priority)

## Configuration File Structure

Add your tool to `config.json` (optional - it will use defaults if not specified):

```json
{
  "models": {
    "assignments": {
      "my_new_tool": "flash",
      "my_analysis_tool": "pro"
    }
  }
}
```

## Environment Variable Overrides

Users can override model assignments using environment variables:

```bash
# Override specific models
export GEMINI_FLASH_MODEL="gemini-2.5-flash-8b"
export GEMINI_PRO_MODEL="gemini-2.5-pro-exp-0827"

# Force all tools to use the same model
export FORCE_MODEL="pro"
```

## Benefits of This Pattern

### ✅ For Tool Developers
- **Zero Configuration Required**: Tools work immediately with sensible defaults
- **Automatic Registration**: Tools are automatically added to the configuration system
- **Consistent API**: Same `cfg.get_model()` call for all tools
- **Environment Override Support**: Users can override models without code changes

### ✅ For Users
- **Centralized Control**: All model assignments in one place
- **Easy Customization**: Edit config.json to change model assignments
- **Environment Flexibility**: Override via environment variables
- **Backwards Compatible**: Existing configurations continue to work

### ✅ For System Maintainers
- **No Manual Registration**: New tools automatically integrate
- **Consistent Logging**: All configuration operations are logged
- **Thread-Safe**: Configuration system is thread-safe
- **Validation**: Invalid configurations fallback to safe defaults

## Complete Example

```python
#!/usr/bin/env python3
"""
Example New Tool - Document Analyzer
"""

import sys
from pathlib import Path

# Import configuration system
try:
    from config import get_config, register_tool_if_missing
except ImportError:
    print("❌ Error: config.py not found")
    sys.exit(1)

def initialize_document_analyzer():
    """Initialize the document analyzer with configuration"""
    # Register tool with default model (only runs if not already configured)
    register_tool_if_missing("document_analyzer", "pro")  # Use pro for thorough analysis
    
def analyze_document(file_path: str):
    """Analyze a document using the configured model"""
    cfg = get_config()
    
    # Get the configured model for this tool
    model_name = cfg.get_model("document_analyzer")
    
    # Get other configuration values
    max_file_size = cfg.get_limit("max_file_size")
    timeout = cfg.get_timeout("cli_timeout")
    
    print(f"🤖 Using {model_name} for document analysis")
    print(f"📏 File size limit: {max_file_size} bytes")
    print(f"⏱️ Timeout: {timeout} seconds")
    
    # Your tool logic here...
    # result = gemini_api_call(model=model_name, prompt=f"Analyze: {file_path}")
    
if __name__ == "__main__":
    initialize_document_analyzer()
    
    if len(sys.argv) != 2:
        print("Usage: document_analyzer.py <file_path>")
        sys.exit(1)
        
    analyze_document(sys.argv[1])
```

## Migration from Old Pattern

If you have existing tools using hardcoded models, migrate like this:

### Old Pattern ❌
```python
# Hardcoded model selection
MODELS = {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro"
}

def my_tool():
    model = MODELS["flash"]  # Hardcoded
```

### New Pattern ✅
```python
# Centralized configuration
from config import get_config, register_tool_if_missing

def initialize():
    register_tool_if_missing("my_tool", "flash")

def my_tool():
    cfg = get_config()
    model = cfg.get_model("my_tool")  # Configurable
```

## Error Handling

The configuration system handles errors gracefully:

```python
def robust_tool():
    try:
        cfg = get_config()
        model_name = cfg.get_model("my_tool")
    except Exception as e:
        print(f"⚠️ Configuration error: {e}")
        # Fallback to hardcoded default
        model_name = "gemini-2.5-flash"
    
    # Continue with model_name...
```

## Testing Your Integration

Test your tool with different configurations:

```bash
# Test with default configuration
python my_tool.py

# Test with environment override
export GEMINI_FLASH_MODEL="gemini-2.5-flash-8b"
python my_tool.py

# Test with force override
export FORCE_MODEL="pro"
python my_tool.py

# Test with config file
echo '{"models":{"assignments":{"my_tool":"pro"}}}' > config.json
python my_tool.py
```

## Best Practices

1. **Choose Appropriate Defaults**: Use "flash" for quick tasks, "pro" for thorough analysis
2. **Register Early**: Call `register_tool_if_missing()` during initialization, not during execution
3. **Handle Failures Gracefully**: Have fallback behavior if configuration fails
4. **Log Configuration**: Use the model name in your tool's output for debugging
5. **Test Multiple Scenarios**: Test with defaults, config files, and environment variables

## Troubleshooting

### Tool Not Found Error
```
KeyError: 'my_tool' not found in assignments
```
**Solution**: Call `register_tool_if_missing("my_tool", "flash")` before `cfg.get_model("my_tool")`

### Import Error
```
ImportError: cannot import name 'get_config' from 'config'
```
**Solution**: Ensure `config.py` is in your Python path or adjust import path

### Configuration Not Loading
```
⚠️ Configuration error: Failed to load configuration
```
**Solution**: Check file permissions and JSON syntax in config.json

For more help, check the logs or create an issue in the repository.
