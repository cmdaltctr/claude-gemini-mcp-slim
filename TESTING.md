# Testing Guide

This document provides comprehensive information about testing the Claude Gemini MCP Slim project.

## Quick Start

```bash
# Install dependencies
make install

# Run smoke test to verify setup
make test-smoke

# Run fast unit tests
make test-fast

# Run integration tests (sequential)
make test-integration

# Run all tests with coverage
make test-all
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_gemini_helper.py
│   └── test_security.py
├── integration/             # Integration tests (slower, real components)
│   ├── test_cli_fallback.py
│   ├── test_gemini_api_mocked.py
│   └── test_mcp_server_integration.py
└── e2e/                     # End-to-end tests (full system)
    └── test_full_workflow.py
```

## Test Execution Modes

### 1. Fast Unit Tests (Parallel)
```bash
make test-fast
# or
python3 scripts/run_tests.py fast
```
- Runs in parallel using all CPU cores
- 10-second timeout per test
- No coverage collection for speed
- Ideal for development workflow

### 2. Integration Tests (Sequential)
```bash
make test-integration
# or
python3 scripts/run_tests.py integration
```
- Runs sequentially to avoid resource conflicts
- 30-second timeout per test
- Stops on first failure
- Proper resource isolation

### 3. Integration Tests (Parallel)
```bash
make test-integration-parallel
# or
python3 scripts/run_tests.py integration-parallel
```
- Limited parallel execution (2 workers)
- Better for stable integration tests
- Uses loadscope distribution

### 4. All Tests with Coverage
```bash
make test-all
# or
python3 scripts/run_tests.py all
```
- Runs all tests with coverage report
- Generates HTML coverage report
- Requires 70% coverage to pass

### 5. Debug Mode
```bash
make test-debug TEST_PATTERN=tests/integration/test_cli_fallback.py
# or
python3 scripts/run_tests.py debug --test-pattern="tests/integration/test_cli_fallback.py"
```
- No parallel execution
- Detailed output and logging
- No output capture
- 60-second timeout

### 6. Specific Test Patterns
```bash
# Run specific test file
make test-specific TEST_PATTERN=tests/unit/test_gemini_helper.py

# Run specific test class
make test-specific TEST_PATTERN=tests/unit/test_gemini_helper.py::TestPromptSanitization

# Run specific test method
make test-specific TEST_PATTERN=tests/unit/test_gemini_helper.py::TestPromptSanitization::test_basic_sanitization

# Run tests with keyword matching
make test-specific TEST_PATTERN='-k sanitization'

# Run tests with markers
make test-specific TEST_PATTERN='-m "not slow"'
```

## Test Configuration

### Pytest Configuration (pyproject.toml)
```toml
[tool.pytest.ini_options]
addopts = [
    "--timeout=30",           # 30 second timeout per test
    "--timeout-method=thread", # Thread-based timeout
    "-n auto",                # Auto-detect CPU cores
    "--maxfail=5",            # Stop after 5 failures
    "--tb=short",             # Short traceback format
]
```

### Test Markers
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.security` - Security-focused tests
- `@pytest.mark.timeout` - Tests that should timeout

## Fixing Hanging Tests

The project includes several mechanisms to prevent hanging tests:

### 1. Timeout Mechanisms
- Global 30-second timeout per test
- Thread-based timeout method
- Configurable timeouts for different test types

### 2. Parallel Execution
- pytest-xdist for parallel execution
- Automatic CPU core detection
- Process isolation prevents deadlocks

### 3. Resource Management
- Proper fixture cleanup
- Mock object isolation
- Temporary workspace creation

### 4. Test Isolation
- Environment reset between tests
- Patch cleanup
- Resource tracking

## Common Issues and Solutions

### Issue: Tests Hang During Execution
**Solutions:**
1. Use sequential mode: `make test-integration`
2. Check for infinite loops in test code
3. Verify mock objects are properly configured
4. Use debug mode for detailed output

### Issue: AsyncIO Event Loop Errors
**Solutions:**
1. Use the session-scoped event loop fixture
2. Ensure proper async/await patterns
3. Check for event loop conflicts in parallel execution

### Issue: Resource Leaks
**Solutions:**
1. Use `resource_cleanup` fixture
2. Ensure proper teardown in fixtures
3. Check for unclosed files/processes

### Issue: Flaky Tests
**Solutions:**
1. Use `parallel_safe_mock` fixture
2. Implement proper test isolation
3. Avoid global state dependencies

## Performance Optimization

### 1. Skip Coverage for Speed
```bash
# Unit tests without coverage
python3 -m pytest tests/unit/ --no-cov -n auto

# Integration tests without coverage
python3 -m pytest tests/integration/ --no-cov -n 1
```

### 2. Run Only Changed Tests
```bash
# Run tests related to specific files
make test-specific TEST_PATTERN=tests/unit/test_gemini_helper.py
```

### 3. Use Test Markers
```bash
# Skip slow tests
python3 -m pytest -m "not slow"

# Run only unit tests
python3 -m pytest -m unit
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run fast tests
  run: make test-fast

- name: Run integration tests
  run: make test-integration

- name: Run all tests with coverage
  run: make test-all
```

### Local CI Simulation
```bash
# Full CI pipeline
make ci

# Quick development check
make check

# Full validation
make validate
```

## Debugging Failed Tests

### 1. Use Debug Mode
```bash
make test-debug TEST_PATTERN=tests/integration/test_cli_fallback.py::TestCLIFallbackSecurity::test_no_shell_injection
```

### 2. Enable Detailed Logging
```bash
python3 -m pytest tests/integration/ -vv --log-cli-level=DEBUG --capture=no
```

### 3. Run Single Test
```bash
python3 -m pytest tests/integration/test_cli_fallback.py::TestCLIFallbackSecurity::test_no_shell_injection -vv
```

## Best Practices

### 1. Test Writing
- Use descriptive test names
- Keep tests focused and isolated
- Use appropriate fixtures
- Mock external dependencies

### 2. Test Organization
- Group related tests in classes
- Use proper test markers
- Maintain test independence

### 3. Performance
- Use parallel execution for unit tests
- Use sequential execution for integration tests
- Skip coverage collection during development

### 4. Maintenance
- Regularly run the full test suite
- Monitor test execution times
- Clean up test artifacts regularly

## Dependencies

The testing infrastructure requires:
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-xdist>=3.8.0` - Parallel execution
- `pytest-timeout>=2.4.0` - Timeout management
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.11.0` - Mock utilities

Install all dependencies with:
```bash
make install
```

## Getting Help

For additional help with test patterns:
```bash
make test-help
```

For general help with available commands:
```bash
make help
```
