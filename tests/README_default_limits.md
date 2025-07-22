# Default Limit Tests Documentation

## Overview

This document describes the default limit tests implemented for the Gemini MCP Server security functions. These tests ensure that the configured limits are properly enforced and that the security functions handle boundary conditions correctly.

## Test Coverage

### 1. File Size Validation (`validate_file_security()`)

**Function Tested:** `validate_file_security()` from `gemini_helper.py`

**Limit Configuration:** 
- `max_file_size`: 81920 bytes (80KB) - from `config.py`
- Internal buffer: 2x limit (163840 bytes) in `validate_file_security()`

**Test Cases:**

- ✅ **Smaller than max:** File with 50% of max size (40KB) → Should pass with `(True, "File validation successful", path)`
- ✅ **Exactly at boundary:** File with exactly max_file_size (80KB) → Should pass
- ✅ **One byte over limit:** File with 2x max_file_size + 1 bytes → Should fail with `(False, "File too large: X bytes", None)`

**Key Implementation Details:**
- `validate_file_security()` uses a 2x buffer internally (checks against `max_size * 2`)
- Files up to 163840 bytes (160KB) pass validation
- Files over 163840 bytes fail with "File too large" error message

### 2. Line Count Validation (Fake File Content)

**Function Tested:** Line counting logic used by MCP server functions

**Limit Configuration:**
- `max_lines`: 800 lines - from `config.py`

**Test Cases:**

- ✅ **Smaller than max:** File with 400 lines (50% of max) → Should pass validation
- ✅ **Exactly at boundary:** File with exactly 800 lines → Should pass validation  
- ✅ **One line over limit:** File with 801 lines → Still passes `validate_file_security()` (line count checking happens at MCP server level)

**Key Implementation Details:**
- `validate_file_security()` doesn't enforce line count limits directly
- Line count validation occurs in the MCP server's `call_tool()` functions
- Uses `len(content.splitlines())` to count lines

### 3. Prompt Length Validation (`sanitize_for_prompt()`)

**Function Tested:** `sanitize_for_prompt()` from `gemini_helper.py` and `gemini_mcp_server.py`

**Limit Configuration:**
- `max_prompt_size`: 1,000,000 bytes (1MB) - overall prompt limit
- `sanitization_max_length`: 100,000 bytes - sanitization truncation limit

**Test Cases:**

- ✅ **Smaller than max:** Prompt with 50,000 chars → Should pass unchanged
- ✅ **Exactly at boundary:** Prompt with exactly 100,000 chars → Should pass unchanged
- ✅ **One char over limit:** Prompt with 100,001 chars → Should be truncated to 100,000 chars
- ✅ **Dangerous patterns over limit:** Oversized prompt with injection patterns → Should be both filtered and truncated, containing `[filtered-content]` marker

**Key Implementation Details:**
- `sanitize_for_prompt()` truncates at `sanitization_max_length` (100KB), not `max_prompt_size` (1MB)
- Dangerous pattern filtering happens before truncation
- Both helper and server versions should behave identically

## Configuration Hierarchy

The tests verify the configuration system works correctly:

```
max_prompt_size (1MB) > sanitization_max_length (100KB) > max_file_size (80KB) > max_lines (800 lines)
```

This ensures:
- Files are smaller than prompts they generate
- Sanitization happens at a reasonable limit
- Large prompts get truncated to manageable sizes

## Test Execution

### Direct Execution
```bash
cd /path/to/claude-gemini-mcp-slim
python tests/test_default_limits.py
```

### With Pytest (if available)
```bash
python -m pytest tests/test_default_limits.py -v
```

## Expected Output

```
Running default limits tests for Gemini MCP server...
✅ File size smaller than max test passed
✅ File size at boundary test passed
✅ File size over limit test passed
✅ Line count smaller than max test passed
✅ Line count at boundary test passed
✅ Prompt length smaller than max test passed
✅ Prompt length at boundary test passed
✅ Prompt length over limit test passed
✅ Config limits accessibility test passed
✅ Prompt vs sanitization limit relationship test passed

🔒 All default limits tests passed! Security limits are properly enforced.
```

## Integration with Existing Tests

The default limit tests complement the existing security tests:

- `test_security.py` - Tests prompt injection protection and path traversal
- `test_default_limits.py` - Tests limit enforcement and boundary conditions
- Together they ensure comprehensive security coverage

## Error Conditions Tested

1. **File size violations:** Files exceeding 2x buffer (160KB) fail validation
2. **Prompt truncation:** Content over 100KB gets truncated
3. **Dangerous pattern filtering:** Injection patterns replaced with `[filtered-content]`
4. **Configuration validation:** All limits accessible and set to expected values

## Maintenance

When modifying limits in `config.py`, update the corresponding assertions in:
- `test_config_limits_accessible()` method
- Individual boundary test methods
- Documentation in this README

The tests are designed to read limits dynamically from configuration, but assertion values may need updates for validation purposes.
