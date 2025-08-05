# AI Agent Golden Rules for the Claude-Gemini MCP Project

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Purpose:** Essential rules and guidelines for any AI agent interacting with or modifying this codebase  
**Scope:** All AI agents, coding assistants, automated development tools, and agentic IDEs  

This document provides comprehensive rules to ensure consistency, security, and maintainability. Adherence to these rules is mandatory.

---

## 1. Core Philosophy: You are an Intelligent Orchestrator

**DO:** Act as an intelligent agent, not a simple bridge. Your primary role is to add value by orchestrating complex workflows.
**DO:** Understand the five steps of your agentic process: Perception (receiving a task), Reasoning (choosing a model/tool), Orchestration (constructing a detailed prompt), Transformation (formatting the result), and Action (responding to the client).

### 1.1. Leveraging Multi-Contextual Platforms (MCPs)

**DO:** Utilize various MCP servers to enhance agentic AI capabilities and workflow orchestration. These platforms provide specialized contexts and functionalities that allow our AI tools to operate effectively and intelligently.

*   **Context7 (e.g., `resolve-library-id`, `get-library-docs`):** Used for comprehensive documentation and knowledge retrieval, enabling the agent to access and understand vast amounts of technical information.
*   **Perplexity (e.g., `perplexity-ask`, `perplexity-research`, `perplexity-reason`):** Leveraged for advanced reasoning, deep research, and conversational AI, providing the agent with sophisticated analytical capabilities.
*   **Git and GitHub MCP (e.g., `git-status`, `github-create-pull-request`, `github-list-issues`):** Essential for version control, code management, and collaborative development, allowing the agent to interact seamlessly with Git repositories and GitHub workflows.
*   **Pieces MCP (e.g., `create-pieces-memory`, `ask-pieces-ltm`):** Used for long-term memory management and contextual recall, allowing the agent to store and retrieve critical information and past experiences.
*   **Sequential Thinking MCP (e.g., `sequentialthinking`):** Facilitates complex problem-solving through structured, iterative thought processes, enabling the agent to break down tasks, revise approaches, and verify hypotheses.

These MCPs collectively empower the agent to perform a wide range of software engineering tasks with enhanced intelligence, context awareness, and operational efficiency.
**DON'T:** Merely pass raw text between the client and the AI backend.

---

## 2. Architectural Integrity

### 2.1. The Decoupled Module Pattern

**DO:** Strictly adhere to the project's decoupled architecture.
*   **`gemini_mcp_server.py`:** This is **The Communicator**. Its sole responsibility is handling MCP requests and responses. It orchestrates the workflow by calling other modules. **It must not contain direct AI API call logic.**
*   **`gemini_helper.py`:** This is **The AI Specialist**. Its sole responsibility is to manage all interactions with the Gemini backend (API or CLI).
*   **`helpers/` directory:** This contains specialized **Pre-Processing and Post-Processing Engines**. Use these helpers for their specific tasks (e.g., `codebase_analyzer`, `markdown_utils`).

**DON'T:** Add AI interaction logic to the server module. Don't add MCP communication logic to the helper module.

### 2.2. Configuration Management

**DO:** Use the central configuration system for all settings.
*   Read all configuration values (model names, timeouts, limits, feature flags) by calling the accessor functions in `config.py` (e.g., `cfg.get_model()`, `cfg.get_limit()`).
**DON'T:** Ever use `os.getenv()` or hard-code any configuration values outside of `config.py`.

### 2.3. Agentic Data Flow (ACP)

**DO:** Prioritize the Agentic Collaboration Protocol. When modifying or implementing features like `analyze_code`, your primary goal is to use the `instructor` library to request a structured JSON object (e.g., `AgenticCodePatch`) from the Gemini API.
**DON'T:** Default to requesting plain text from the AI. The evolution of this project depends on moving towards structured data exchange.

---

## 3. Code Modification and Documentation Standards

### 3.1. Documentation and Clarity Requirements

**DO:** Generate code that is well-documented and follows project conventions.

**Documentation Standards:**
- **Docstrings:** All new public functions, methods, and classes must include a docstring explaining their purpose, arguments (`Args:`), and return values (`Returns:`).
- **Type Hinting:** Use Python type hints for all function signatures.
- **Comments:** Add comments to explain the **"why"** of complex logic, not the "what".

### 3.2. File Organization and Structure

**DO:** Place new files in the correct location according to their responsibility.

**File Placement Rules:**
- If you create a new, reusable utility (e.g., for security, data transformation, etc.), create a new file for it inside the `src/claude_gemini_mcp/helpers/` directory.
- Update the `helpers/__init__.py` file to expose any new public functions.
- Follow the established modular architecture with clear separation of concerns.

### 3.3. Testing and Quality Standards

**DO:** Ensure all code is thoroughly tested and adheres to quality standards.

**Quality Requirements:**
- **Testing:** Write comprehensive tests using `pytest` (unit, integration, e2e, security, performance, configuration matrix, stress tests).
- **Code Coverage:** Strive for high code coverage, measured by `pytest-cov`.
- **Linting & Formatting:** Run `black`, `flake8`, `isort`, and `mypy` checks. Ensure code is formatted correctly and passes all linting rules.
- **Security Scanning:** Use `bandit`, `pip-audit`, and `safety` to scan for vulnerabilities.

**DON'T:** Introduce code that reduces test coverage or fails any linting/security checks.

---

## 4. Core Development Principles

### P1: Security-First Development
**Rule:** Security considerations must be evaluated BEFORE any code implementation.

**Implementation:**
- ALL user inputs MUST be validated and sanitized using existing patterns in `gemini_mcp_server.py`
- Path operations MUST use `validate_path_security()` function 
- NO hardcoded secrets, API keys, or sensitive data in code
- Input size limits MUST be respected (80KB files, 800 lines, configurable via `config.py`)
- Use `sanitize_for_prompt()` for all user-provided content before AI model submission

**Code Example:**
```python
# ✅ CORRECT: Always validate and sanitize
def handle_user_input(user_content: str, file_path: str) -> Dict[str, Any]:
    # Validate path security first
    is_valid, error_msg, resolved_path = validate_path_security(file_path)
    if not is_valid:
        return {"success": False, "error": error_msg}
    
    # Sanitize content before processing
    sanitized_content = sanitize_for_prompt(user_content, max_length=cfg.get_limit("max_prompt_size"))
    
    # Proceed with secure implementation
    ...

# ❌ INCORRECT: Direct use of user input
def handle_user_input_bad(user_content: str, file_path: str):
    # This bypasses security controls
    return process_content(user_content, file_path)
```

### P2: Configuration-Driven Architecture
**Rule:** Use the centralized configuration system for all configurable values.

**Implementation:**
- Import and use `from claude_gemini_mcp.config import get_config` 
- Access models via `cfg.get_model(tool_name)` not hardcoded values
- Access limits via `cfg.get_limit(limit_name)` not magic numbers
- Access timeouts via `cfg.get_timeout(timeout_name)` 
- Support environment variable overrides for all configurations

**Code Example:**
```python
# ✅ CORRECT: Use configuration system
from claude_gemini_mcp.config import get_config
cfg = get_config()

async def analyze_code(code_content: str, analysis_type: str):
    # Get configured limits
    max_size = cfg.get_limit("max_file_size")
    max_lines = cfg.get_limit("max_lines")
    timeout = cfg.get_timeout("analysis_timeout")
    model = cfg.get_model("gemini_analyze_code")
    
    # Use configuration values
    if len(code_content) > max_size:
        return {"error": f"Code too large. Max: {max_size} bytes"}

# ❌ INCORRECT: Hardcoded values
async def analyze_code_bad(code_content: str, analysis_type: str):
    if len(code_content) > 81920:  # Magic number
        return {"error": "Code too large"}
```

### P3: Comprehensive Error Handling
**Rule:** All functions must implement proper error handling with user-friendly messages.

**Implementation:**
- Use try-catch blocks for all external API calls and file operations
- Return structured error responses: `{"success": bool, "error": str, "output": str}`
- Log errors with appropriate levels using the configured logger
- Sanitize error messages to prevent information leakage
- Provide actionable error messages for users

**Code Example:**
```python
# ✅ CORRECT: Comprehensive error handling
async def execute_gemini_query(prompt: str) -> Dict[str, Any]:
    try:
        # Validate inputs first
        if not isinstance(prompt, str) or not prompt.strip():
            return {"success": False, "error": "Prompt must be a non-empty string"}
        
        # Attempt API call with timeout
        result = await gemini_api_call(prompt)
        return {"success": True, "output": result}
        
    except asyncio.TimeoutError:
        logger.error("Gemini API call timed out")
        return {"success": False, "error": "Request timed out. Please try again."}
    except Exception as e:
        # Sanitize error message
        sanitized_error = str(e)[:200]  # Limit error message length
        logger.error(f"Gemini API error: {sanitized_error}")
        return {"success": False, "error": "API call failed. Check logs for details."}

# ❌ INCORRECT: Poor error handling
async def execute_gemini_query_bad(prompt: str):
    result = await gemini_api_call(prompt)  # No error handling
    return result  # No structured response
```

## Architecture Standards

### A1: Modular Component Design
**Rule:** Follow the established modular architecture with clear separation of concerns.

**Component Responsibilities:**
- **MCP Server Layer** (`gemini_mcp_server.py`): Protocol handling, request routing, tool registration
- **Configuration Layer** (`config.py`): Settings management, environment variables, validation
- **Security Layer** (validation functions): Input sanitization, path security, access controls
- **Tool Handlers** (tool-specific functions): Business logic for each MCP tool
- **Helper Modules** (`helpers/`): Specialized utilities, analysis engines, progress tracking

**Implementation Pattern:**
```python
# ✅ CORRECT: Layered architecture
async def handle_tool_request(tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """MCP Server Layer - delegates to specific handlers"""
    if tool_name in TOOL_HANDLERS:
        return await TOOL_HANDLERS[tool_name](arguments)
    else:
        return _create_error_response(f"Unknown tool: {tool_name}")

async def _handle_code_analysis(arguments: Dict[str, Any]) -> List[TextContent]:
    """Tool Handler Layer - implements business logic"""
    # Input validation
    validation_result = _validate_analysis_input(arguments)
    if validation_result:
        return _create_error_response(validation_result)
    
    # Delegate to analysis layer
    analysis_result = await perform_code_analysis(arguments)
    
    # Response formatting
    return _create_success_response(analysis_result)

# ❌ INCORRECT: Monolithic function
async def handle_everything_bad(tool_name: str, arguments: Dict[str, Any]):
    # Mixing protocol, validation, business logic, and formatting
    if tool_name == "analyze":
        if not arguments.get("code"):
            return [TextContent(text="Error: No code")]
        result = await call_gemini(arguments["code"])
        return [TextContent(text=result)]
```

### A2: Async/Await Patterns
**Rule:** Use proper async/await patterns following the project's established conventions.

**Implementation:**
- ALL I/O operations (API calls, file operations) MUST be async
- Use `asyncio.wait_for()` for timeout handling  
- Use `asyncio.create_subprocess_exec()` for CLI subprocess calls
- Implement proper cleanup with `try/finally` or async context managers
- Use existing patterns from `execute_gemini_cli_streaming()`

**Code Example:**
```python
# ✅ CORRECT: Proper async patterns
async def call_external_service(data: str) -> Dict[str, Any]:
    timeout = cfg.get_timeout("api_timeout", 30)
    
    try:
        # Use timeout for external calls
        async with asyncio.timeout(timeout):
            result = await external_api.call(data)
            return {"success": True, "output": result}
    except asyncio.TimeoutError:
        return {"success": False, "error": "Operation timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ❌ INCORRECT: Blocking calls in async function
async def call_external_service_bad(data: str):
    result = external_api.call_sync(data)  # Blocking call
    return result
```

### A3: Testing Integration Requirements  
**Rule:** All new code MUST include comprehensive tests following the project's testing architecture.

**Test Structure Requirements:**
- **Unit Tests** (`tests/unit/`): Fast, isolated, mocked dependencies
- **Integration Tests** (`tests/integration/`): Real components, controlled environment  
- **End-to-End Tests** (`tests/e2e/`): Full workflow validation
- **Test Coverage**: Minimum 70% coverage for new code
- **Test Performance**: Unit tests <10s, integration tests <30s

**Code Example:**
```python
# ✅ CORRECT: Comprehensive test structure
# tests/unit/test_new_feature.py
import pytest
from unittest.mock import AsyncMock, patch
from claude_gemini_mcp.new_feature import process_request

class TestNewFeature:
    @pytest.mark.asyncio
    async def test_process_request_success(self, parallel_safe_mock):
        """Test successful request processing"""
        # Arrange
        mock_gemini = AsyncMock(return_value={"success": True, "output": "result"})
        
        with patch('claude_gemini_mcp.new_feature.call_gemini', mock_gemini):
            # Act
            result = await process_request("test input")
            
            # Assert
            assert result["success"] is True
            assert "result" in result["output"]
            mock_gemini.assert_called_once_with("test input")
    
    @pytest.mark.asyncio
    async def test_process_request_invalid_input(self):
        """Test error handling for invalid input"""
        result = await process_request("")
        assert result["success"] is False
        assert "invalid" in result["error"].lower()

# tests/integration/test_new_feature_integration.py
class TestNewFeatureIntegration:
    @pytest.mark.asyncio
    async def test_full_workflow(self, test_workspace, resource_cleanup):
        """Test complete feature workflow with real components"""
        # Test with real configuration and controlled environment
        ...

# ❌ INCORRECT: Missing tests
# New code without any tests - breaks CI/CD pipeline
```

## Code Quality Standards

### Q1: Type Hints and Documentation
**Rule:** All functions must have proper type hints and docstrings.

**Requirements:**
- Function signatures MUST include complete type hints
- Docstrings MUST follow Google/NumPy style format
- Public APIs MUST have comprehensive documentation  
- Complex logic MUST include inline comments explaining the "why"

**Code Example:**
```python
# ✅ CORRECT: Proper typing and documentation
async def analyze_codebase(
    directory_path: str, 
    analysis_scope: str = "all",
    max_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Analyze entire codebase using Gemini's large context window.
    
    Args:
        directory_path: Path to directory to analyze
        analysis_scope: Type of analysis ('structure', 'security', 'performance', 'all')
        max_size: Maximum total size in bytes to analyze (overrides config)
        
    Returns:
        Dict containing analysis results:
        - success: bool indicating if analysis completed successfully
        - output: str with analysis results if successful
        - error: str with error message if failed
        
    Raises:
        ValueError: If directory_path is invalid or analysis_scope unknown
        ConfigurationError: If configuration cannot be loaded
        
    Example:
        >>> result = await analyze_codebase("./src", "security")
        >>> if result["success"]:
        >>>     print(result["output"])
    """
    # Validate inputs using established patterns
    is_valid, error_msg, resolved_path = validate_path_security(directory_path)
    if not is_valid:
        return {"success": False, "error": error_msg}
    
    # Use configuration system for limits
    cfg = get_config()
    effective_max_size = max_size or cfg.get_limit("max_codebase_size")
    
    # Implementation continues...

# ❌ INCORRECT: Missing type hints and documentation
async def analyze_codebase(directory_path, analysis_scope="all"):
    # No docstring, no type hints, unclear return type
    return some_analysis_function(directory_path, analysis_scope)
```

### Q2: Logging and Observability
**Rule:** Implement comprehensive logging using the established logging patterns.

**Logging Standards:**
- Use the configured logger: `logger = logging.getLogger(__name__)`
- Log levels: DEBUG (detailed flow), INFO (major operations), WARNING (recoverable issues), ERROR (failures)
- Include contextual information: function name, parameters, execution time
- Use structured logging for complex operations
- NEVER log sensitive data (API keys, user content, file contents)

**Code Example:**
```python
# ✅ CORRECT: Proper logging patterns
import logging
logger = logging.getLogger(__name__)

async def process_analysis_request(request_id: str, content: str) -> Dict[str, Any]:
    """Process analysis request with comprehensive logging."""
    start_time = time.time()
    logger.info(f"Starting analysis request {request_id}, content length: {len(content)}")
    
    try:
        # Log major steps
        logger.debug(f"Request {request_id}: Validating input")
        validation_result = validate_input(content)
        
        if not validation_result.is_valid:
            logger.warning(f"Request {request_id}: Input validation failed - {validation_result.error}")
            return {"success": False, "error": validation_result.error}
        
        logger.debug(f"Request {request_id}: Calling Gemini API")
        result = await call_gemini_api(content)
        
        execution_time = time.time() - start_time
        logger.info(f"Request {request_id} completed successfully in {execution_time:.2f}s")
        
        return {"success": True, "output": result}
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Request {request_id} failed after {execution_time:.2f}s: {str(e)}")
        return {"success": False, "error": "Internal processing error"}

# ❌ INCORRECT: Poor logging practices
async def process_analysis_request_bad(content):
    print("Starting analysis")  # Use logger, not print
    try:
        result = await call_gemini_api(content)
        print(f"API returned: {result}")  # Don't log potentially sensitive content
        return result
    except Exception as e:
        print(e)  # Not using proper logging levels
        raise  # Re-raising without handling
```

### Q3: Performance and Resource Management
**Rule:** Implement efficient resource usage following project performance patterns.

**Performance Requirements:**
- Use streaming responses for long operations (see `execute_gemini_cli_streaming`)
- Implement progress tracking for operations >10 seconds
- Respect memory limits and clean up resources properly
- Use connection pooling and reuse for external APIs
- Implement timeouts for all I/O operations

**Code Example:**
```python
# ✅ CORRECT: Efficient resource management
async def stream_large_analysis(
    content: str, 
    progress_callback: Optional[Callable[[str], None]] = None
) -> AsyncGenerator[str, None]:
    """Stream analysis results for large content with progress tracking."""
    
    # Resource management with proper cleanup
    process = None
    try:
        # Use configured timeouts
        timeout = cfg.get_timeout("analysis_timeout")
        
        # Create subprocess with resource limits
        process = await asyncio.create_subprocess_exec(
            "gemini", "-m", model_name, "-p", content,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"PATH": os.environ.get("PATH", "")}
        )
        
        # Stream output with progress tracking
        start_time = asyncio.get_event_loop().time()
        last_progress = start_time
        
        while process.returncode is None:
            try:
                # Read with timeout to avoid hanging
                line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                
                if line:
                    decoded_line = line.decode("utf-8", errors="replace")
                    yield decoded_line
                    
                    # Update progress periodically
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_progress > 10:  # Every 10 seconds
                        elapsed = int(current_time - start_time)
                        if progress_callback:
                            progress_callback(f"Analysis in progress... {elapsed}s elapsed")
                        last_progress = current_time
                        
            except asyncio.TimeoutError:
                # Continue processing, just no data available
                continue
                
    finally:
        # Ensure cleanup even if exceptions occur
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()

# ❌ INCORRECT: Poor resource management
async def stream_large_analysis_bad(content):
    # No timeout, no cleanup, no progress tracking
    process = await asyncio.create_subprocess_exec("gemini", "-p", content)
    while True:
        line = await process.stdout.readline()  # Can hang forever
        if not line:
            break
        yield line.decode()
    # No cleanup of process resources
```

## Tool-Specific Development Rules

### T1: MCP Tool Implementation Pattern
**Rule:** Follow the established pattern for implementing MCP tools.

**Required Structure:**
1. Tool registration in `list_tools()` with proper schema
2. Input validation with structured error responses  
3. Business logic delegation to handler functions
4. Consistent response formatting using `_create_success_response()` and `_create_error_response()`
5. Integration with the `TOOL_HANDLERS` registry

**Code Example:**
```python
# ✅ CORRECT: Proper MCP tool implementation

# 1. Tool registration in list_tools()
Tool(
    name="new_analysis_tool",
    description="Performs specialized analysis using advanced techniques",
    inputSchema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "Content to analyze"
            },
            "analysis_type": {
                "type": "string",
                "enum": ["deep", "quick", "specialized"],
                "default": "deep",
                "description": "Type of analysis to perform"
            }
        },
        "required": ["content"]
    }
)

# 2. Handler function with validation
async def _handle_new_analysis(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle new_analysis_tool requests with comprehensive validation."""
    
    # Input validation
    content = arguments.get("content", "")
    analysis_type = arguments.get("analysis_type", "deep")
    
    if not isinstance(content, str) or not content.strip():
        return _create_error_response("Content must be a non-empty string")
    
    valid_types = ["deep", "quick", "specialized"]
    if analysis_type not in valid_types:
        return _create_error_response(f"Invalid analysis type. Must be one of: {valid_types}")
    
    # Size validation using config
    max_size = cfg.get_limit("max_analysis_content")
    if len(content) > max_size:
        return _create_error_response(f"Content too large ({len(content)} bytes). Max: {max_size} bytes")
    
    # Security validation
    sanitized_content = sanitize_for_prompt(content, max_length=max_size)
    
    # Business logic delegation
    try:
        result = await perform_specialized_analysis(sanitized_content, analysis_type)
        
        if result["success"]:
            header = f"Specialized Analysis ({analysis_type})"
            return _create_success_response(result["output"], header)
        else:
            return _create_error_response(result["error"])
            
    except Exception as e:
        logger.error(f"New analysis tool error: {str(e)}")
        return _create_error_response("Analysis failed. Check logs for details.")

# 3. Registry integration
TOOL_HANDLERS = {
    "gemini_quick_query": _handle_quick_query,
    "gemini_analyze_code": _handle_code_analysis,
    "gemini_codebase_analysis": _handle_codebase_analysis,
    "new_analysis_tool": _handle_new_analysis,  # Add new tool
}

# ❌ INCORRECT: Poor tool implementation
async def handle_new_tool_bad(arguments):
    # No validation, no error handling, inconsistent response format
    content = arguments["content"]  # Can fail if key missing
    result = await some_analysis(content)  # No error handling
    return [TextContent(type="text", text=result)]  # Inconsistent format
```

### T2: Configuration Extensions
**Rule:** Extend the configuration system properly when adding new configurable features.

**Implementation Process:**
1. Add defaults to `DEFAULT_CONFIG` in `config.py`
2. Add environment variable support in `_load_env_config()`
3. Add validation in `_validate_and_normalize()`  
4. Add typed accessor methods if needed
5. Update documentation and examples

**Code Example:**
```python
# ✅ CORRECT: Proper configuration extension

# 1. Add to DEFAULT_CONFIG
"specialized_analysis": {
    "max_depth": 5,
    "cache_enabled": True,
    "parallel_workers": 2,
    "output_format": "detailed"
}

# 2. Add environment variable support
if os.getenv("SPECIALIZED_MAX_DEPTH"):
    try:
        env_config.setdefault("specialized_analysis", {})["max_depth"] = int(os.getenv("SPECIALIZED_MAX_DEPTH"))
    except ValueError:
        logger.warning(f"Invalid SPECIALIZED_MAX_DEPTH value: {os.getenv('SPECIALIZED_MAX_DEPTH')}")

# 3. Add validation
specialized = self._config.get("specialized_analysis", {})
max_depth = specialized.get("max_depth")
if not isinstance(max_depth, int) or max_depth <= 0:
    logger.warning(f"Invalid max_depth for specialized analysis: {max_depth}")
    specialized["max_depth"] = self.DEFAULT_CONFIG["specialized_analysis"]["max_depth"]

# 4. Add accessor method if needed
def get_specialized_setting(self, setting_name: str, explicit_value: Optional[Any] = None) -> Any:
    """Get specialized analysis setting with load precedence"""
    if explicit_value is not None:
        return explicit_value
    
    specialized = self._config.get("specialized_analysis", {})
    setting_value = specialized.get(setting_name)
    
    if setting_value is not None:
        return setting_value
    
    # Fallback to default
    default_specialized = self.DEFAULT_CONFIG.get("specialized_analysis", {})
    return default_specialized.get(setting_name)

# ❌ INCORRECT: Hardcoded configuration
def perform_specialized_analysis(content: str):
    max_depth = 5  # Hardcoded instead of using config
    cache_enabled = True  # Not configurable
    # Missing environment variable support and validation
```

## Security and Compliance Rules

### S1: Input Validation and Sanitization
**Rule:** ALL user inputs must be validated and sanitized before processing.

**Security Checklist:**
- ✅ Path inputs use `validate_path_security()` 
- ✅ Content inputs use `sanitize_for_prompt()`
- ✅ Size limits enforced via configuration system
- ✅ No direct shell execution with user input
- ✅ No SQL injection vectors (though not applicable here)
- ✅ No code injection through eval/exec

### S2: API Key and Credential Management
**Rule:** Handle credentials securely following established patterns.

**Security Requirements:**
- API keys ONLY from environment variables, never hardcoded
- Mask/redact credentials in logs and error messages
- Use the existing credential sanitization patterns
- No credentials in configuration files checked into version control
- Support for credential rotation without code changes

### S3: Error Information Disclosure
**Rule:** Error messages must not leak sensitive information.

**Implementation:**
- Use existing error sanitization patterns from `_sanitize_error_output()`
- Generic error messages for users, detailed logs for developers
- No file paths, API keys, or user content in error responses
- Stack traces only in debug mode and logs, never in user responses

## Documentation Standards

### D1: Code Documentation Requirements
**Rule:** Follow the established documentation patterns for consistency.

**Documentation Checklist:**
- ✅ All public functions have comprehensive docstrings
- ✅ Complex algorithms have inline comments explaining logic
- ✅ Configuration options documented with examples
- ✅ Error conditions and return values clearly specified
- ✅ Usage examples provided for new tools

### D2: API Documentation Updates
**Rule:** Update relevant documentation when adding or modifying tools.

**Required Updates:**
- Update `README.md` with new tool descriptions and examples
- Update `docs/SETUP.md` if configuration changes
- Update tool schemas in `list_tools()` 
- Add slash command documentation if applicable
- Update troubleshooting guides if new error conditions

## Testing and Quality Assurance

### QA1: Test Coverage Requirements
**Rule:** Maintain minimum 70% test coverage for all new code.

**Test Categories:**
- **Unit Tests**: Fast, isolated, mocked dependencies
- **Integration Tests**: Real components, controlled environment
- **Security Tests**: Input validation, injection prevention
- **Performance Tests**: Response times, resource usage
- **Error Handling Tests**: All error conditions covered

### QA2: CI/CD Integration
**Rule:** All code must pass the established CI/CD pipeline.

**Pipeline Requirements:**
- ✅ All tests pass (unit, integration, e2e)
- ✅ Code coverage meets minimum threshold
- ✅ Security scans pass (bandit, safety)
- ✅ Code quality checks pass (flake8, mypy, black)
- ✅ Documentation builds successfully

## Deployment and Operations

### O1: CI/CD and Release Process

**DO:** Leverage the automated CI/CD pipeline for all changes.

**CI/CD Requirements:**
- **CI:** Ensure your changes pass all checks in the GitHub Actions `test.yml` workflow (including all test types and quality gates).
- **Release:** Understand that releases are automated via `release-please` based on conventional commits.
- **Dependency Management:** Use `pip` for now, but be aware of `uv` as a faster, more reliable alternative for future consideration.

**DON'T:** Bypass CI checks or manually manage releases.

### O2: Environment Configuration
**Rule:** Support all deployment environments through configuration.

**Environment Support:**
- **Development**: Enhanced logging, debug features, relaxed timeouts
- **Testing**: Mocked external services, isolated environments  
- **Production**: Optimized performance, security hardening, monitoring

### O3: Monitoring and Observability
**Rule:** Include appropriate monitoring hooks for operational visibility.

**Monitoring Requirements:**
- Structured logging for parsing by log aggregation systems
- Performance metrics (response times, error rates, resource usage)
- Health check endpoints for load balancer integration
- Graceful shutdown handling for deployment updates

### O4: Security Requirements

**DO:** Treat all external input as untrusted and implement comprehensive security measures.

**Security Implementation:**
- Use the centralized security helper (`src/claude_gemini_mcp/helpers/security.py` - **to be created**) for all input sanitization and path validation.
- ALL user inputs MUST be validated and sanitized using existing patterns in `gemini_mcp_server.py`
- Path operations MUST use `validate_path_security()` function
- NO hardcoded secrets, API keys, or sensitive data in code
- Input size limits MUST be respected (80KB files, 800 lines, configurable via `config.py`)

**DON'T:** Implement your own one-off security or validation checks in other modules.

## Best Practices Summary

### Development Workflow
1. **Read First**: Study existing code patterns before implementing
2. **Security First**: Validate inputs, sanitize outputs, check permissions
3. **Configuration Driven**: Use the config system, support environment overrides
4. **Test Comprehensively**: Unit tests for logic, integration tests for workflows
5. **Document Thoroughly**: Code comments, docstrings, usage examples
6. **Error Gracefully**: Structured error handling, user-friendly messages
7. **Log Appropriately**: Contextual logging without sensitive data
8. **Perform Efficiently**: Streaming responses, resource cleanup, timeouts

### Code Review Checklist
- [ ] Security validation implemented and tested
- [ ] Configuration system used consistently  
- [ ] Error handling comprehensive and user-friendly
- [ ] Type hints and documentation complete
- [ ] Tests written and passing with adequate coverage
- [ ] Logging implemented without sensitive data exposure
- [ ] Performance considerations addressed
- [ ] Integration with existing architecture maintained

### Common Anti-Patterns to Avoid
- ❌ Hardcoded configuration values instead of using config system
- ❌ Missing input validation and sanitization
- ❌ Poor error handling that exposes internal details
- ❌ Blocking I/O operations in async functions
- ❌ Missing tests for new functionality
- ❌ Logging sensitive data (API keys, user content)
- ❌ Inconsistent response formats across tools
- ❌ Resource leaks (unclosed files, processes, connections)

---

**Document Maintenance:**
- **Review Schedule**: Monthly or when significant changes are made
- **Update Triggers**: New security requirements, architecture changes, tool additions
- **Stakeholders**: Development team, security team, AI tool maintainers
- **Version Control**: Track changes with rationale and approval