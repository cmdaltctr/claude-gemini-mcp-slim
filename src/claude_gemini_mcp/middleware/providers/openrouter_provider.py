#!/usr/bin/env python3
"""
OpenRouter Provider - Multi-model AI provider implementation.

This module implements the OpenRouter provider, enabling access to multiple
AI models through the OpenRouter API platform. Supports various models from
different providers including OpenAI, Anthropic, Google, and others.

Features:
- Multiple model support through unified API
- Cost optimization across different providers
- Automatic model selection and fallback
- Rate limiting and error handling
- Response normalization and formatting

OpenRouter Integration:
- API key management and authentication
- Model capability detection and reporting
- Request/response transformation
- Error mapping and standardization
"""

import logging
import json
import requests
from typing import Dict, Any, List, Optional, Tuple
from .base_provider import BaseProvider, ProviderResult, ProviderError

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider implementation

    This provider implements access to multiple AI models through the OpenRouter
    platform, providing unified access to various AI providers with cost optimization
    and intelligent model selection capabilities.
    """

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        """Initialize OpenRouter provider

        Args:
            api_key: OpenRouter API key
            base_url: OpenRouter API base URL
        """        # Create config for BaseProvider
        config = {
            "api_key_env": "OPENROUTER_API_KEY",
            "api_base_url": base_url,
            "models": [],
            "timeout_ms": 60000,
            "max_retries": 2
        }

        super().__init__("openrouter", config)

        # Override with provided api_key if given
        if api_key:
            self.api_key = api_key

        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://claude-gemini-mcp-slim.local',
            'X-Title': 'Claude Gemini MCP Slim'
        })

        # Load model capabilities
        self._model_capabilities = self._initialize_model_capabilities()

        logger.debug(f"Initialized OpenRouter provider with {len(self._model_capabilities)} models")

    def _initialize_model_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Initialize OpenRouter model capabilities

        Returns:
            Dictionary mapping model names to their capabilities
        """
        # Fetch models dynamically from OpenRouter API or use fallback
        try:
            return self._fetch_models_from_api()
        except Exception as e:
            logger.warning(f"Failed to fetch models from API: {e}, using fallback models")
            return self._get_fallback_models()

    def _fetch_models_from_api(self) -> Dict[str, Dict[str, Any]]:
        """Fetch available models from OpenRouter API

        Returns:
            Dictionary of model capabilities
        """
        try:
            # For now, use fallback models since we can't make async call during __init__
            # In a real implementation, this would be loaded asynchronously after initialization
            logger.info("Using fallback models for OpenRouter (async model loading not implemented in __init__)")
            return self._get_fallback_models()

        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

    def _extract_capabilities(self, model: Dict[str, Any]) -> List[str]:
        """Extract capabilities from model metadata

        Args:
            model: Model information from API

        Returns:
            List of capability strings
        """
        capabilities = ["text"]  # All models support text

        # Check for multimodal support
        if model.get('multimodal'):
            capabilities.append("multimodal")

        # Infer capabilities from model name/description
        name = model.get('name', '').lower()
        model_id = model.get('id', '').lower()

        if any(keyword in f"{name} {model_id}" for keyword in ['code', 'programmer', 'dev']):
            capabilities.append("code")

        if any(keyword in f"{name} {model_id}" for keyword in ['reasoning', 'think', 'logic']):
            capabilities.append("reasoning")

        # Large context models
        context_length = model.get('context_length', 0)
        if context_length >= 100000:
            capabilities.append("longContext")

        return capabilities

    def _get_fallback_models(self) -> Dict[str, Dict[str, Any]]:
        """Get fallback model list when API is unavailable

        Returns:
            Dictionary of fallback models
        """
        return {
            # OpenAI Models via OpenRouter
            "openai/gpt-4o-mini": {
                "context_window": 128000,
                "max_tokens": 16384,
                "capabilities": ["text", "code", "reasoning", "multimodal"],
                "description": "OpenAI GPT-4o Mini - Fast and cost-effective",
                "cost_per_1k_tokens": {"input": 0.00015, "output": 0.0006},
                "provider": "openai"
            },
            # Anthropic Models via OpenRouter
            "anthropic/claude-3-haiku": {
                "context_window": 200000,
                "max_tokens": 4096,
                "capabilities": ["text", "code", "reasoning"],
                "description": "Anthropic Claude 3 Haiku - Fast and efficient",
                "cost_per_1k_tokens": {"input": 0.00025, "output": 0.00125},
                "provider": "anthropic"
            },
            # Google Models via OpenRouter
            "google/gemini-flash-1.5": {
                "context_window": 1048576,
                "max_tokens": 8192,
                "capabilities": ["text", "code", "reasoning", "multimodal", "longContext"],
                "description": "Google Gemini Flash 1.5 - Fast with large context",
                "cost_per_1k_tokens": {"input": 0.00015, "output": 0.0006},
                "provider": "google"
            },
            # DeepSeek Models via OpenRouter
            "deepseek/deepseek-chat": {
                "context_window": 32768,
                "max_tokens": 8192,
                "capabilities": ["text", "code", "reasoning"],
                "description": "DeepSeek Chat - Cost-effective conversational AI",
                "cost_per_1k_tokens": {"input": 0.00014, "output": 0.00028},
                "provider": "deepseek"
            },
            "deepseek/deepseek-r1-0528": {
                "context_window": 65536,
                "max_tokens": 8192,
                "capabilities": ["text", "code", "reasoning", "analysis"],
                "description": "DeepSeek R1 - Latest reasoning model",
                "cost_per_1k_tokens": {"input": 0.00027, "output": 0.0011},
                "provider": "deepseek"
            },

            # Qwen Models via OpenRouter
            "qwen/qwen3-coder-30b-instruct": {
                "context_window": 32768,
                "max_tokens": 8192,
                "capabilities": ["text", "code", "reasoning", "agentic"],
                "description": "Qwen3 Coder 30B - Agentic coding capabilities",
                "cost_per_1k_tokens": {"input": 0.0002, "output": 0.0008},
                "provider": "qwen"
            },
            "qwen/qwen3-coder-480b-a35b-instruct": {
                "context_window": 65536,
                "max_tokens": 8192,
                "capabilities": ["text", "code", "reasoning", "agentic", "longContext"],
                "description": "Qwen3 Coder 480B - Most advanced agentic coding model",
                "cost_per_1k_tokens": {"input": 0.001, "output": 0.004},
                "provider": "qwen"
            },

            # Moonshot Models via OpenRouter
            "moonshot/moonshot-kimi-k2-instruct": {
                "context_window": 200000,
                "max_tokens": 8192,
                "capabilities": ["text", "code", "reasoning", "longContext", "multimodal"],
                "description": "Moonshot Kimi K2 - Advanced Chinese reasoning model",
                "cost_per_1k_tokens": {"input": 0.0005, "output": 0.002},
                "provider": "moonshot"
            },

            # GLM Models via OpenRouter
            "zai/glm-4.5": {
                "context_window": 131072,
                "max_tokens": 8192,
                "capabilities": ["text", "code", "reasoning", "longContext", "analysis"],
                "description": "GLM-4.5 - State-of-the-art Chinese model competitive with Claude/GPT",
                "cost_per_1k_tokens": {"input": 0.0008, "output": 0.0032},
                "provider": "zhipuai"
            },
            "zai/glm-4.5-air": {
                "context_window": 131072,
                "max_tokens": 8192,
                "capabilities": ["text", "code", "reasoning", "longContext"],
                "description": "GLM-4.5 Air - Lighter version with efficient performance",
                "cost_per_1k_tokens": {"input": 0.0003, "output": 0.0012},
                "provider": "zhipuai"
            }
        }

    @property
    def provider_name(self) -> str:
        """Get provider name"""
        return "openrouter"

    @property
    def supported_models(self) -> Dict[str, Dict[str, Any]]:
        """Get supported models and their capabilities"""
        return self._model_capabilities

    def validate_model(self, model_name: str) -> bool:
        """Validate if model is supported

        Args:
            model_name: Model name to validate

        Returns:
            True if model is supported
        """
        return model_name in self._model_capabilities

    def get_model_capabilities(self, model_name: str) -> Dict[str, Any]:
        """Get capabilities for specific model

        Args:
            model_name: Model name

        Returns:
            Model capabilities dictionary
        """
        return self._model_capabilities.get(model_name, {})

    async def execute_request(
        self,
        prompt: str,
        model: str = "openai/gpt-4o-mini",
        **kwargs
    ) -> ProviderResult:
        """Execute request using OpenRouter API

        Args:
            prompt: Input prompt text
            model: Model name to use
            **kwargs: Additional parameters

        Returns:
            ProviderResult with response or error
        """
        try:
            # Validate model
            if not self.validate_model(model):
                available_models = ", ".join(list(self._model_capabilities.keys())[:5])
                return ProviderResult(
                    success=False,
                    error=f"Unsupported model: {model}. Available: {available_models}..."
                )

            # Build request payload
            payload = self._build_request_payload(prompt, model, **kwargs)

            # Make API request
            response = self._make_api_request(payload)

            # Process response
            return self._process_response(response, model)

        except Exception as e:
            logger.error(f"OpenRouter execution error: {str(e)}")
            return ProviderResult(
                success=False,
                error=f"OpenRouter API error: {str(e)}"
            )

    def _build_request_payload(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Build OpenRouter API request payload

        Args:
            prompt: Input prompt
            model: Model name
            **kwargs: Additional parameters

        Returns:
            API request payload
        """
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["temperature"] = float(kwargs["temperature"])

        if "max_tokens" in kwargs:
            payload["max_tokens"] = int(kwargs["max_tokens"])

        if "top_p" in kwargs:
            payload["top_p"] = float(kwargs["top_p"])

        # Add provider-specific options
        payload["provider"] = {
            "order": ["OpenAI", "Anthropic", "Google"],
            "allow_fallbacks": True
        }

        return payload

    def _make_api_request(self, payload: Dict[str, Any]) -> requests.Response:
        """Make API request to OpenRouter

        Args:
            payload: Request payload

        Returns:
            API response

        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.base_url}/v1/chat/completions"

        response = self.session.post(
            url,
            json=payload,
            timeout=60
        )

        response.raise_for_status()
        return response

    def _process_response(
        self,
        response: requests.Response,
        model: str
    ) -> ProviderResult:
        """Process OpenRouter API response

        Args:
            response: HTTP response from API
            model: Model name used

        Returns:
            Processed ProviderResult
        """
        try:
            data = response.json()

            # Extract content from response
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                content = choice.get("message", {}).get("content", "")

                # Extract usage information
                usage = data.get("usage", {})

                return ProviderResult(
                    success=True,
                    content=content,
                    metadata={
                        "model_used": model,
                        "provider": "openrouter",
                        "tokens_used": usage.get("total_tokens", 0),
                        "input_tokens": usage.get("prompt_tokens", 0),
                        "output_tokens": usage.get("completion_tokens", 0),
                        "response_id": data.get("id"),
                        "created": data.get("created"),
                        "finish_reason": choice.get("finish_reason")
                    }
                )
            else:
                return ProviderResult(
                    success=False,
                    error="Invalid response format from OpenRouter API"
                )

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return ProviderResult(
                success=False,
                error=f"Invalid JSON response: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Response processing error: {str(e)}")
            return ProviderResult(
                success=False,
                error=f"Response processing failed: {str(e)}"
            )

    def health_check(self) -> bool:
        """Check OpenRouter API health

        Returns:
            True if API is accessible
        """
        try:
            # Make a minimal request to check API availability
            test_payload = {
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }

            response = self._make_api_request(test_payload)
            return response.status_code == 200

        except Exception as e:
            logger.warning(f"OpenRouter health check failed: {str(e)}")
            return False

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Estimate cost for token usage

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name

        Returns:
            Estimated cost in USD
        """
        model_info = self._model_capabilities.get(model, {})
        cost_info = model_info.get("cost_per_1k_tokens", {"input": 0.001, "output": 0.002})

        input_cost = (input_tokens / 1000) * cost_info["input"]
        output_cost = (output_tokens / 1000) * cost_info["output"]

        return input_cost + output_cost

    def get_available_models_by_capability(self, capability: str) -> List[str]:
        """Get models that support specific capability

        Args:
            capability: Required capability (e.g., 'reasoning', 'multimodal')

        Returns:
            List of model names with the capability
        """
        matching_models = []

        for model_name, model_info in self._model_capabilities.items():
            capabilities = model_info.get("capabilities", [])
            if capability in capabilities:
                matching_models.append(model_name)

        return matching_models

    def get_cheapest_model_for_capability(self, capability: str) -> Optional[str]:
        """Get the cheapest model that supports a capability

        Args:
            capability: Required capability

        Returns:
            Model name or None if no suitable model found
        """
        suitable_models = self.get_available_models_by_capability(capability)

        if not suitable_models:
            return None

        # Find cheapest based on average of input and output costs
        cheapest = min(
            suitable_models,
            key=lambda model: (
                self._model_capabilities[model]["cost_per_1k_tokens"]["input"] +
                self._model_capabilities[model]["cost_per_1k_tokens"]["output"]
            ) / 2
        )

        return cheapest
