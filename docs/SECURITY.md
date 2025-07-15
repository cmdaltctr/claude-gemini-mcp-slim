# Security Documentation - Claude Gemini MCP Integration

## Overview

This document outlines the security measures implemented in the Claude Gemini MCP Integration project to protect against common vulnerabilities and ensure safe operation.

## Security Vulnerabilities Fixed

### Critical Issues Resolved (2025-01-12)

#### 1. Command Injection (CVE-2023-48795 Class)
**Files affected:**
- `gemini_helper.py:80` (shell=True with user input)
- `gemini_mcp_server.py:158` (create_subprocess_shell with user input)  
- `.claude/scripts/slim_gemini_hook.py:117` (subprocess arguments)

**Fix implemented:**
- Replaced `shell=True` with argument lists
- Added input validation for model names and prompts
- Implemented strict character validation for command arguments
- Used minimal environment variables in subprocess calls

**Security impact:** Prevents arbitrary command execution via malicious input

#### 2. Path Traversal (CWE-22)
**Files affected:**
- `gemini_helper.py:178` (unrestricted file access)
- `gemini_mcp_server.py:276-277` (direct path checking)
- Hook scripts file validation

**Fix implemented:**
- Added `validate_path_security()` function across all modules
- Implemented path resolution and boundary checking
- Restricted file access to current directory tree only
- Added file type validation with allowlist approach

**Security impact:** Prevents access to files outside project directory

#### 3. Prompt Injection (CWE-94)
**Files affected:** All prompt construction areas

**Fix implemented:**
- Added `sanitize_for_prompt()` function to all modules
- Filters dangerous prompt injection patterns
- Escapes control characters
- Limits input length to prevent buffer overflow
- Validates input types before processing

**Security impact:** Prevents manipulation of AI model behavior via malicious prompts

#### 4. Secrets Exposure (CWE-200)
**Files affected:** Error handling and logging throughout codebase

**Fix implemented:**
- Added API key validation with minimum length checks
- Implemented regex-based secret redaction in error messages
- Sanitized subprocess environment variables
- Removed sensitive data from logs and error outputs

**Security impact:** Prevents API keys and tokens from being leaked in logs or errors

#### 5. Input Validation Gaps (CWE-20)
**Files affected:** All parameter handling functions

**Fix implemented:**
- Added comprehensive type checking for all inputs
- Implemented bounds checking for strings and numeric values
- Added enumeration validation for analysis types and scopes
- Enhanced error handling with secure failure modes

**Security impact:** Prevents various attack vectors through malformed input

## Security Architecture

### Defense in Depth Strategy

1. **Input Validation Layer**
   - Type checking at entry points
   - Length limits and bounds checking
   - Enumeration validation
   - Character set restrictions

2. **Sanitization Layer**
   - Prompt injection pattern filtering
   - Path normalization and validation
   - Secret redaction in outputs
   - Control character filtering

3. **Execution Layer**
   - Subprocess argument lists (no shell execution)
   - Minimal environment variables
   - Path boundary enforcement
   - File type restrictions

4. **Output Layer**
   - Error message sanitization
   - Log data filtering
   - Response size limits
   - Structured error responses

### Security Functions

#### `sanitize_for_prompt(text: str, max_length: int) -> str`
**Purpose:** Prevents prompt injection attacks
**Features:**
- Filters dangerous instruction patterns
- Removes control characters
- Enforces length limits
- Case-insensitive pattern matching

#### `validate_path_security(file_path: str) -> tuple[bool, str, Path]`
**Purpose:** Prevents path traversal attacks
**Features:**
- Path resolution and normalization
- Directory boundary checking
- File existence validation
- Type validation (file vs directory)

#### API Key Validation
**Purpose:** Secure credential handling
**Features:**
- Minimum length validation
- Type checking
- Secret pattern redaction in errors
- Environment isolation

## File Security Restrictions

### Allowed File Types
```python
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.rs',     # Programming
    '.vue', '.html', '.css', '.scss', '.sass', '.jsx', '.tsx',  # Frontend
    '.json', '.yaml', '.toml', '.md', '.txt'               # Configuration
}
```

### Size Limits
- **Maximum file size:** 80KB (81,920 bytes)
- **Maximum lines:** 800 lines per file
- **Maximum prompt:** 1MB (1,000,000 characters)

### Path Restrictions
- **Allowed access:** Current directory tree only
- **Blocked patterns:** `../`, symbolic links outside tree
- **Validation:** Path resolution and boundary checking

## Subprocess Security

### Command Execution Security
```python
# SECURE: Use argument lists
process = subprocess.Popen(
    ["gemini", "-m", model_name, "-p", prompt],
    shell=False,  # Critical: Never use shell=True
    env={"PATH": os.environ.get("PATH", "")}  # Minimal environment
)

# INSECURE: Never use shell commands
# cmd = f"gemini -m {model_name} -p {prompt}"  # VULNERABLE
# subprocess.run(cmd, shell=True)              # NEVER DO THIS
```

### Environment Security
- **Minimal environment:** Only PATH variable passed
- **No shell expansion:** Argument lists prevent injection
- **Process isolation:** Limited subprocess permissions

## Error Handling Security

### Secret Redaction Patterns
```python
# API key patterns automatically redacted
error_message = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[API_KEY_REDACTED]', error_message)
error_message = re.sub(r'sk-[A-Za-z0-9_-]{32,}', '[API_KEY_REDACTED]', error_message)
error_message = re.sub(r'Bearer [A-Za-z0-9_.-]{10,}', '[TOKEN_REDACTED]', error_message)
```

### Safe Error Responses
- Generic error messages for security failures
- No sensitive information in user-facing errors
- Detailed logging for debugging (sanitized)
- Graceful degradation on security violations

## Security Best Practices

### For Developers

1. **Input Validation**
   - Always validate input types and ranges
   - Use allowlists instead of blocklists when possible
   - Implement fail-secure defaults

2. **Path Handling**
   - Always use `validate_path_security()` before file operations
   - Never trust user-provided paths
   - Use absolute paths internally

3. **Subprocess Calls**
   - Never use `shell=True` with user input
   - Always use argument lists
   - Validate command arguments before execution

4. **Prompt Construction**
   - Always use `sanitize_for_prompt()` for user inputs
   - Never interpolate user data directly into prompts
   - Validate AI model responses

5. **Error Handling**
   - Sanitize error messages before logging
   - Never expose internal paths or configurations
   - Use structured error responses

### For Users

1. **Environment Security**
   - Keep API keys secure and rotate regularly
   - Use environment variables for sensitive configuration
   - Monitor for unusual activity in logs

2. **File Organization**
   - Keep sensitive files outside project directory
   - Use appropriate file permissions
   - Regularly review file access patterns

3. **Update Management**
   - Keep dependencies updated
   - Monitor security advisories
   - Test security updates in isolated environments

## Compliance and Auditing

### Security Controls Implemented

- **CWE-22:** Path Traversal - ✅ Fixed with boundary validation
- **CWE-78:** Command Injection - ✅ Fixed with argument lists  
- **CWE-94:** Code Injection - ✅ Fixed with input sanitization
- **CWE-200:** Information Exposure - ✅ Fixed with secret redaction
- **CWE-20:** Input Validation - ✅ Fixed with comprehensive validation

### Audit Trail

All security improvements are tracked in git history with detailed commit messages:
- Path validation functions added
- Input sanitization implemented
- Subprocess security hardened
- Error handling secured

### Testing Recommendations

1. **Static Analysis**
   - Run security scanners on codebase
   - Check for hardcoded secrets
   - Validate input handling patterns

2. **Dynamic Testing**
   - Test with malicious file paths
   - Attempt prompt injection attacks
   - Verify error message sanitization

3. **Integration Testing**
   - Test security boundaries
   - Verify access control enforcement
   - Validate error handling paths

## Security Contact

For security issues or questions:
- Create issue in project repository (for non-sensitive issues)
- Review security documentation before implementation
- Follow secure coding practices in all contributions

## Changelog

### Version 1.0.0 (2025-01-12)
- **CRITICAL:** Fixed 5 major security vulnerabilities
- Added comprehensive input validation framework
- Implemented secure subprocess handling
- Added path traversal protection
- Enhanced error handling security
- Created comprehensive security documentation

---

**Last Updated:** 2025-01-12  
**Security Review Status:** ✅ Current  
**Next Review Due:** 2025-04-12