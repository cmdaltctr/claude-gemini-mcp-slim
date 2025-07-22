#!/usr/bin/env python3
"""
Comprehensive unit tests for config.py

Tests cover:
- Load precedence: explicit args › env vars › config.json › hard-coded defaults  
- Typed accessors: get_model(), get_limit(), get_timeout()
- Nickname support and environment overrides
- Force-model logic
- Validation with fallbacks
- Edge cases and error handling
"""

import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from claude_gemini_mcp.config import get_config, reload_config


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """
    Ensure a clean environment for each test.
    Automatically runs before each test to reset environment and configuration state.
    """
    # Store original environment
    original_env = dict(os.environ)

    # Clear relevant environment variables
    config_vars = [
        'GEMINI_FLASH_MODEL', 'GEMINI_PRO_MODEL', 'FORCE_MODEL',
        'CLI_TIMEOUT', 'API_TIMEOUT', 'MAX_FILE_SIZE', 'MAX_LINES',
        'MAX_PROMPT_SIZE', 'MAX_CODEBASE_SIZE', 'MAX_CONTEXT_WINDOW',
        'SANITIZATION_MAX_LENGTH', 'ENABLE_MARKDOWN_CONVERSION', 'ENABLE_SANITIZATION'
    ]
    for var in config_vars:
        monkeypatch.delenv(var, raising=False)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

    reload_config()


def test_default_configuration():
    """Test default configuration is loaded correctly"""
    config = get_config()

    # Test default values
    assert config.get_model('quick_query') == 'gemini-2.5-flash'
    assert config.get_model('analyze_code') == 'gemini-2.5-pro'
    assert config.get_limit('max_file_size') == 81920
    assert config.get_limit('max_lines') == 800
    assert config.get_timeout('cli_timeout') == 60
    assert config.get_timeout('api_timeout') == 30
    assert config.get_security_setting('enable_sanitization')
    assert config.get_execution_setting('enable_progress_indicators')


def test_load_precedence_explicit_args():
    """Test explicit function arguments have the highest priority"""
    config = get_config()

    # Test explicit model override
    assert config.get_model('quick_query', 'pro') == 'gemini-2.5-pro'
    assert config.get_model('quick_query', 'gemini-1.5-flash') == 'gemini-1.5-flash'

    # Test explicit limit and timeout
    assert config.get_limit('max_file_size', 123456) == 123456
    assert config.get_timeout('cli_timeout', 120) == 120

    # Test invalid explicit args fallbacks
    assert config.get_limit('max_file_size', -100) == config.DEFAULT_CONFIG['limits']['max_file_size']
    assert config.get_timeout('api_timeout', 0) == config.DEFAULT_CONFIG['timeouts']['api_timeout']


def test_environment_variable_precedence(monkeypatch):
    """Test environment variable overrides for limits are applied correctly"""
    # Set environment variables for new limits
    monkeypatch.setenv('MAX_LINES', '256')
    monkeypatch.setenv('MAX_PROMPT_SIZE', '512')

    reload_config()
    config = get_config()

    # Test numeric environment overrides for new limits
    assert config.get_limit('max_lines') == 256
    assert config.get_limit('max_prompt_size') == 512

    # Test model and boolean environment overrides
    monkeypatch.setenv('GEMINI_FLASH_MODEL', 'gemini-2.0-flash-custom')
    monkeypatch.setenv('GEMINI_PRO_MODEL', 'gemini-2.0-pro-custom')
    monkeypatch.setenv('CLI_TIMEOUT', '90')
    monkeypatch.setenv('API_TIMEOUT', '45')
    monkeypatch.setenv('MAX_FILE_SIZE', '65536')
    monkeypatch.setenv('MAX_CODEBASE_SIZE', '1000000')
    monkeypatch.setenv('ENABLE_MARKDOWN_CONVERSION', 'false')
    monkeypatch.setenv('ENABLE_SANITIZATION', 'true')

    reload_config()
    config = get_config()

    # Verify environment variable effects
    assert config.get_model('quick_query') == 'gemini-2.0-flash-custom'
    assert config.get_model('analyze_code') == 'gemini-2.0-pro-custom'
    assert config.get_timeout('cli_timeout') == 90
    assert config.get_timeout('api_timeout') == 45
    assert config.get_limit('max_file_size') == 65536
    assert config.get_limit('max_codebase_size') == 1000000
    assert not config.get_execution_setting('enable_markdown_conversion')
    assert config.get_security_setting('enable_sanitization')


def test_invalid_environment_variables(monkeypatch):
    """Test handling of invalid environment variable values"""
    monkeypatch.setenv('CLI_TIMEOUT', 'invalid')
    monkeypatch.setenv('MAX_FILE_SIZE', 'not-a-number')
    monkeypatch.setenv('ENABLE_SANITIZATION', 'maybe')

    reload_config()
    config = get_config()

    # Verify fallbacks for invalid values
    assert config.get_timeout('cli_timeout') == config.DEFAULT_CONFIG['timeouts']['cli_timeout']
    assert config.get_limit('max_file_size') == config.DEFAULT_CONFIG['limits']['max_file_size']
    assert config.get_security_setting('enable_sanitization') == config.DEFAULT_CONFIG['security']['enable_sanitization']


def test_force_model_override(monkeypatch):
    """Test FORCE_MODEL environment variable functionality"""
    # Set FORCE_MODEL to 'pro' and verify
    monkeypatch.setenv('FORCE_MODEL', 'pro')
    reload_config()
    config = get_config()

    # Verify FORCE_MODEL impact
    assert config.get_model('quick_query') == 'gemini-2.5-pro'
    assert config.get_model('analyze_code') == 'gemini-2.5-pro'
    assert config.get_model('session_summary') == 'gemini-2.5-pro'

    # Set FORCE_MODEL to 'flash' and verify
    monkeypatch.setenv('GEMINI_FLASH_MODEL', 'gemini-2.5-flash-custom')
    monkeypatch.setenv('GEMINI_PRO_MODEL', 'gemini-2.5-pro-custom')
    monkeypatch.setenv('FORCE_MODEL', 'flash')
    reload_config()
    config = get_config()

    assert config.get_model('quick_query') == 'gemini-2.5-flash-custom'
    assert config.get_model('analyze_code') == 'gemini-2.5-flash-custom'

    # Set direct model name for FORCE_MODEL and verify
    monkeypatch.setenv('FORCE_MODEL', 'gemini-1.5-pro-experimental')
    reload_config()
    config = get_config()
    assert config.get_model('quick_query') == 'gemini-1.5-pro-experimental'

    # Test with invalid force model - first clear previous env vars
    monkeypatch.delenv('GEMINI_FLASH_MODEL', raising=False)
    monkeypatch.delenv('GEMINI_PRO_MODEL', raising=False)
    monkeypatch.setenv('FORCE_MODEL', 'invalid-model')
    reload_config()
    config = get_config()
    
    # Should ignore invalid force model and use defaults  
    assert config.get_model('quick_query') == 'gemini-2.5-flash'
