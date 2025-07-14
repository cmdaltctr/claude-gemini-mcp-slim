# Makefile for Claude Gemini MCP Slim Testing
# ==========================================

.PHONY: help install test-fast test-integration test-integration-parallel test-all test-smoke test-debug clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install                 - Install development dependencies"
	@echo "  test-fast              - Run fast unit tests in parallel"
	@echo "  test-integration       - Run integration tests sequentially"
	@echo "  test-integration-parallel - Run integration tests in parallel"
	@echo "  test-all               - Run all tests with coverage"
	@echo "  test-smoke             - Run smoke test"
	@echo "  test-debug             - Run specific test in debug mode"
	@echo "  test-specific          - Run specific test pattern"
	@echo "  clean                  - Clean test artifacts"
	@echo "  ci                     - Run CI pipeline tests"
	@echo ""
	@echo "Environment variables:"
	@echo "  TEST_PATTERN           - Specific test pattern for debug/specific modes"
	@echo ""
	@echo "Examples:"
	@echo "  make test-fast"
	@echo "  make test-integration"
	@echo "  make test-debug TEST_PATTERN=tests/integration/test_cli_fallback.py"
	@echo "  make test-specific TEST_PATTERN=tests/unit/test_gemini_helper.py::TestPromptSanitization"

# Install dependencies
install:
	python3 scripts/run_tests.py install

# Fast unit tests
test-fast:
	python3 scripts/run_tests.py fast

# Integration tests (sequential)
test-integration:
	python3 scripts/run_tests.py integration

# Integration tests (parallel)
test-integration-parallel:
	python3 scripts/run_tests.py integration-parallel

# All tests with coverage
test-all:
	python3 scripts/run_tests.py all

# Smoke test
test-smoke:
	python3 scripts/run_tests.py smoke

# Debug mode
test-debug:
	@if [ -z "$(TEST_PATTERN)" ]; then \
		echo "Error: TEST_PATTERN environment variable is required"; \
		echo "Usage: make test-debug TEST_PATTERN=tests/integration/test_cli_fallback.py"; \
		exit 1; \
	fi
	python3 scripts/run_tests.py debug --test-pattern="$(TEST_PATTERN)"

# Specific test
test-specific:
	@if [ -z "$(TEST_PATTERN)" ]; then \
		echo "Error: TEST_PATTERN environment variable is required"; \
		echo "Usage: make test-specific TEST_PATTERN=tests/unit/test_gemini_helper.py"; \
		exit 1; \
	fi
	python3 scripts/run_tests.py specific --test-pattern="$(TEST_PATTERN)"

# Clean test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# CI pipeline simulation
ci: clean install test-fast test-integration test-all
	@echo "✅ CI pipeline completed successfully!"

# Quick development check
check: test-smoke test-fast
	@echo "✅ Quick development check completed!"

# Full validation
validate: clean install test-all
	@echo "✅ Full validation completed!"

# Alternative commands for convenience
unit: test-fast
integration: test-integration
coverage: test-all
smoke: test-smoke
debug: test-debug
specific: test-specific

# Help for specific test patterns
test-help:
	@echo "Test pattern examples:"
	@echo ""
	@echo "Run all tests in a directory:"
	@echo "  TEST_PATTERN=tests/unit/ make test-specific"
	@echo "  TEST_PATTERN=tests/integration/ make test-specific"
	@echo ""
	@echo "Run a specific test file:"
	@echo "  TEST_PATTERN=tests/integration/test_cli_fallback.py make test-specific"
	@echo ""
	@echo "Run a specific test class:"
	@echo "  TEST_PATTERN=tests/unit/test_gemini_helper.py::TestPromptSanitization make test-specific"
	@echo ""
	@echo "Run a specific test method:"
	@echo "  TEST_PATTERN=tests/unit/test_gemini_helper.py::TestPromptSanitization::test_basic_sanitization make test-specific"
	@echo ""
	@echo "Run tests with keyword matching:"
	@echo "  TEST_PATTERN='-k sanitization' make test-specific"
	@echo ""
	@echo "Run tests with markers:"
	@echo "  TEST_PATTERN='-m \"not slow\"' make test-specific"
	@echo "  TEST_PATTERN='-m integration' make test-specific"
