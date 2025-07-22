#!/usr/bin/env python3
"""
Configuration Matrix Test Suite

Comprehensive testing of configuration loading behavior with different
environments and file presence scenarios using pytest parametrisation.

This test suite validates:
- Default configuration behavior without config files
- Configuration loading with config.json files present
- Environment variable override behavior
- Configuration validation and error handling
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from unittest.mock import patch

import pytest

from claude_gemini_mcp.config import GeminiConfig, reload_config, get_config


class TestConfigurationMatrix:
    """
    Test configuration matrix with missing and existing config.json files.
    
    This test class uses pytest parametrisation to test various configuration
    scenarios systematically.
    """

    @pytest.fixture(autouse=True)
    def setup_clean_environment(self) -> Generator[None, None, None]:
        """
        Ensure clean environment for each test.
        
        This fixture automatically runs before each test to reset the
        environment and configuration state.
        """
        # Store original environment
        original_env = dict(os.environ)
        
        # Clear relevant environment variables
        config_vars = [
            'GEMINI_FLASH_MODEL', 'GEMINI_PRO_MODEL', 'FORCE_MODEL',
            'CLI_TIMEOUT', 'API_TIMEOUT', 'MAX_FILE_SIZE', 'MAX_LINES'
        ]
        for var in config_vars:
            os.environ.pop(var, None)
        
        yield
        
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
        reload_config()

    def test_default_configuration_loading(self) -> None:
        """
        Test default behavior without any config.json and no environment variables.
        
        Validates that the configuration system properly loads hard-coded defaults
        when no external configuration sources are available.
        """
        # Clear any existing configuration and reload
        reload_config()
        config = get_config()

        # Test default configuration values
        assert config.get_model('quick_query') == 'gemini-2.5-flash'
        assert config.get_model('analyze_code') == 'gemini-2.5-pro'
        assert config.get_limit('max_file_size') == 81920  # 80KB
        assert config.get_timeout('cli_timeout') == 60

    @pytest.mark.parametrize(
        "config_data,tool_name,expected_model",
        [
            # Test case 1: Custom model nicknames
            (
                {
                    "models": {
                        "nicknames": {
                            "flash": "gemini-2.5-flash-custom",
                            "pro": "gemini-2.5-pro-custom"
                        }
                    }
                },
                "quick_query",
                "gemini-2.5-flash-custom"
            ),
            # Test case 2: Custom tool assignments
            (
                {
                    "models": {
                        "assignments": {
                            "quick_query": "pro"
                        }
                    }
                },
                "quick_query",
                "gemini-2.5-pro"
            ),
            # Test case 3: Both custom nicknames and assignments
            (
                {
                    "models": {
                        "nicknames": {
                            "flash": "gemini-2.5-flash-experimental",
                            "pro": "gemini-2.5-pro-experimental"
                        },
                        "assignments": {
                            "analyze_code": "flash"
                        }
                    }
                },
                "analyze_code",
                "gemini-2.5-flash-experimental"
            ),
        ]
    )
    def test_configuration_with_config_file(
        self,
        config_data: Dict[str, Any],
        tool_name: str,
        expected_model: str
    ) -> None:
        """
        Test configuration loading with config.json file present.
        
        Tests various configuration file scenarios using parametrisation
        to validate proper configuration parsing and model resolution.
        
        Args:
            config_data: The configuration data to write to the config file
            tool_name: The tool name to test model resolution for
            expected_model: The expected resolved model name
        """
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config_data, f)
            config_file = Path(f.name)

        try:
            with patch('claude_gemini_mcp.config.GeminiConfig._find_config_file', return_value=config_file):
                reload_config()
                config = get_config()
                
                # Test configuration file loading
                actual_model = config.get_model(tool_name)
                assert actual_model == expected_model
        finally:
            config_file.unlink()

    @pytest.mark.parametrize(
        "env_vars,expected_values",
        [
            # Test case 1: Model environment variables
            (
                {
                    'GEMINI_FLASH_MODEL': 'gemini-2.5-flash-env',
                    'GEMINI_PRO_MODEL': 'gemini-2.5-pro-env'
                },
                {
                    'flash_model': 'gemini-2.5-flash-env',
                    'pro_model': 'gemini-2.5-pro-env'
                }
            ),
            # Test case 2: Timeout environment variables
            (
                {
                    'CLI_TIMEOUT': '120',
                    'API_TIMEOUT': '45'
                },
                {
                    'cli_timeout': 120,
                    'api_timeout': 45
                }
            ),
            # Test case 3: Size limit environment variables
            (
                {
                    'MAX_FILE_SIZE': '102400',
                    'MAX_LINES': '1000'
                },
                {
                    'max_file_size': 102400,
                    'max_lines': 1000
                }
            ),
        ]
    )
    def test_environment_variable_overrides(
        self,
        env_vars: Dict[str, str],
        expected_values: Dict[str, Any]
    ) -> None:
        """
        Test environment variable override behavior.
        
        Validates that environment variables properly override default
        configuration values and config file values.
        
        Args:
            env_vars: Environment variables to set
            expected_values: Expected configuration values after applying env vars
        """
        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value

        # Reload configuration to pick up environment changes
        reload_config()
        config = get_config()

        # Verify environment variable effects
        for key, expected_value in expected_values.items():
            if key.endswith('_model'):
                # Test model resolution
                nickname = key.replace('_model', '')
                if nickname == 'flash':
                    actual = config.get_model('quick_query')
                elif nickname == 'pro':
                    actual = config.get_model('analyze_code')
                assert actual == expected_value
            elif key.endswith('_timeout'):
                # Test timeout configuration
                timeout_name = key
                actual = config.get_timeout(timeout_name)
                assert actual == expected_value
            else:
                # Test limit configuration
                limit_name = key
                actual = config.get_limit(limit_name)
                assert actual == expected_value

    def test_force_model_override(self) -> None:
        """
        Test FORCE_MODEL environment variable behavior.
        
        Validates that FORCE_MODEL properly overrides all tool assignments
        regardless of other configuration sources.
        """
        # Set FORCE_MODEL environment variable
        os.environ['FORCE_MODEL'] = 'pro'
        
        reload_config()
        config = get_config()
        
        # All tools should use the forced model
        tools_to_test = ['quick_query', 'analyze_code', 'gemini_quick_query']
        for tool in tools_to_test:
            actual_model = config.get_model(tool)
            assert actual_model == 'gemini-2.5-pro'

    def test_invalid_configuration_handling(self) -> None:
        """
        Test handling of invalid configuration values.
        
        Validates that the configuration system gracefully handles
        invalid values and falls back to defaults with appropriate warnings.
        """
        invalid_config = {
            "models": {
                "nicknames": {
                    "flash": "",  # Invalid empty model name
                    "pro": 123   # Invalid non-string model name
                }
            },
            "limits": {
                "max_file_size": -1,  # Invalid negative limit
                "max_lines": "invalid"  # Invalid non-numeric limit
            },
            "timeouts": {
                "cli_timeout": 0,  # Invalid zero timeout
                "api_timeout": "bad"  # Invalid non-numeric timeout
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(invalid_config, f)
            config_file = Path(f.name)

        try:
            with patch('claude_gemini_mcp.config.GeminiConfig._find_config_file', return_value=config_file):
                reload_config()
                config = get_config()
                
                # Should fall back to defaults for invalid values
                assert config.get_model('quick_query') == 'gemini-2.5-flash'
                assert config.get_limit('max_file_size') == 81920
                assert config.get_timeout('cli_timeout') == 60
        finally:
            config_file.unlink()

    @pytest.mark.parametrize(
        "explicit_override,expected_result",
        [
            # Test case 1: Valid explicit model override
            ('pro', 'gemini-2.5-pro'),
            # Test case 2: Valid explicit nickname override
            ('flash', 'gemini-2.5-flash'),
            # Test case 3: Valid explicit direct model name
            ('gemini-2.5-flash-8b', 'gemini-2.5-flash-8b'),
            # Test case 4: None should use default
            (None, 'gemini-2.5-flash'),
        ]
    )
    def test_explicit_parameter_precedence(
        self,
        explicit_override: Optional[str],
        expected_result: str
    ) -> None:
        """
        Test that explicit function parameters have highest precedence.
        
        Validates that when explicit parameters are provided to configuration
        methods, they take precedence over all other configuration sources.
        
        Args:
            explicit_override: The explicit parameter value to test
            expected_result: The expected result from the configuration call
        """
        # For None parameter, don't set FORCE_MODEL to test default behavior
        if explicit_override is None:
            reload_config()
        else:
            # Set up conflicting environment variable for non-None cases
            os.environ['FORCE_MODEL'] = 'pro'
            reload_config()
        
        config = get_config()
        
        # Explicit parameter should override everything (when not None)
        actual = config.get_model('quick_query', explicit_model=explicit_override)
        assert actual == expected_result

    async def test_async_configuration_access(self) -> None:
        """
        Test configuration access in async contexts.
        
        Ensures that configuration loading and access works correctly
        in asynchronous code contexts.
        """
        reload_config()
        config = get_config()
        
        # Should work in async context
        model = config.get_model('quick_query')
        assert model == 'gemini-2.5-flash'
        
        limit = config.get_limit('max_file_size')
        assert limit == 81920
        
        timeout = config.get_timeout('cli_timeout')
        assert timeout == 60

