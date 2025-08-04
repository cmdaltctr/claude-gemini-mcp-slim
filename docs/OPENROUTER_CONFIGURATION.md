# OpenRouter Model Configuration Guide

This guide shows you how to configure custom OpenRouter models for different routing scenarios.

## Overview

The router uses **scenario-based routing** to automatically select the best model for each task:

- **Default**: General-purpose tasks
- **Background**: Simple, fast tasks (documentation, basic queries)
- **Think**: Complex reasoning tasks requiring advanced models
- **LongContext**: Large context window requirements (>60K tokens)
- **WebSearch**: Tasks involving web search or real-time information
- **Coding**: Code generation and programming tasks
- **Analysis**: Data analysis and detailed evaluation
- **Multimodal**: Image/vision + text processing
- **Reasoning**: Advanced reasoning and problem-solving

## Configuration Methods

### 1. Environment Variables (Recommended)

Add these to your MCP JSON configuration:

```json
{
  "mcpServers": {
    "claude-gemini-mcp": {
      "command": "uv",
      "args": ["run", "claude-gemini-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-key",
        "OPENROUTER_API_KEY": "your-openrouter-key",
        
        "ENABLE_ROUTING": "true",
        "ENABLE_OPENROUTER": "true",
        
        "OPENROUTER_DEFAULT_MODEL": "openrouter,openai/gpt-4o-mini",
        "OPENROUTER_BACKGROUND_MODEL": "openrouter,openai/gpt-4o-mini",
        "OPENROUTER_THINK_MODEL": "openrouter,deepseek/deepseek-r1-0528",
        "OPENROUTER_LONGCONTEXT_MODEL": "openrouter,moonshot/moonshot-kimi-k2-instruct",
        "OPENROUTER_WEBSEARCH_MODEL": "openrouter,perplexity/llama-3.1-sonar-large-128k-online",
        "OPENROUTER_CODING_MODEL": "openrouter,qwen/qwen3-coder-30b-instruct",
        "OPENROUTER_ANALYSIS_MODEL": "openrouter,zai/glm-4.5",
        "OPENROUTER_MULTIMODAL_MODEL": "openrouter,moonshot/moonshot-kimi-k2-instruct",
        "OPENROUTER_REASONING_MODEL": "openrouter,deepseek/deepseek-r1-0528"
      }
    }
  }
}
```

### 2. Available OpenRouter Models

You can choose from **thousands of models** on OpenRouter. Here are some popular options:

#### **Coding Models:**
- `qwen/qwen3-coder-30b-instruct` - Agentic coding capabilities
- `qwen/qwen3-coder-480b-a35b-instruct` - Most advanced coding model
- `deepseek/deepseek-coder-v2-instruct` - Excellent for code generation
- `meta-llama/codellama-70b-instruct` - Meta's coding specialist

#### **Reasoning Models:**
- `deepseek/deepseek-r1-0528` - Latest reasoning model
- `openai/o1-preview` - OpenAI's reasoning model
- `anthropic/claude-3.5-sonnet` - Strong reasoning capabilities
- `google/gemini-2.5-pro-preview` - Google's advanced model

#### **Long Context Models:**
- `moonshot/moonshot-kimi-k2-instruct` - 200K context window
- `anthropic/claude-3-haiku` - 200K context, fast
- `google/gemini-flash-1.5` - 1M+ context window
- `qwen/qwen3-coder-480b-a35b-instruct` - 65K context

#### **Analysis Models:**
- `zai/glm-4.5` - State-of-the-art Chinese model, competitive with Claude/GPT
- `zai/glm-4.5-air` - Lighter version with efficient performance
- `anthropic/claude-3.5-sonnet` - Excellent for analysis
- `openai/gpt-4o` - Strong analytical capabilities

#### **Multimodal Models:**
- `moonshot/moonshot-kimi-k2-instruct` - Vision + text
- `anthropic/claude-3.5-sonnet` - Vision capabilities
- `openai/gpt-4o` - Vision + text processing
- `google/gemini-2.5-pro-preview` - Multimodal capabilities

#### **Fast/Cheap Models:**
- `openai/gpt-4o-mini` - Fast and cost-effective
- `anthropic/claude-3-haiku` - Quick responses
- `google/gemini-flash-1.5` - Fast with large context
- `deepseek/deepseek-chat` - Cost-effective conversational AI

### 3. How Routing Works

The router analyzes each request and automatically determines the scenario:

```
User Request: "Analyze this complex data structure and suggest optimizations"
↓
Router Analysis:
- Complexity Score: 8/10 (high)
- Content Type: Analysis
- Keywords: "analyze", "complex", "optimizations"
↓
Scenario Selection: "analysis"
↓
Model Selection: "zai/glm-4.5" (via OPENROUTER_ANALYSIS_MODEL)
```

### 4. Manual Scenario Override

You can also manually specify scenarios in your requests:

```python
# In tools that support it
result = await router.route_request(RouteRequest(
    prompt="Your prompt here",
    scenario="coding",  # Forces coding scenario
    tool_name="analyze_code"
))
```

### 5. Performance and Cost Optimization

The router also considers:

- **Response Time**: Automatically switches to faster models for simple tasks
- **Cost**: Balances quality vs. cost based on task complexity
- **Context Window**: Selects models with sufficient context for large prompts
- **Fallback**: Gracefully falls back if primary model fails

### 6. Monitoring

Enable telemetry to track routing decisions:

```json
{
  "env": {
    "ENABLE_TELEMETRY": "true",
    "ENABLE_PERFORMANCE_MONITORING": "true",
    "ENABLE_COST_TRACKING": "true"
  }
}
```

## Complete Example MCP Configuration

```json
{
  "mcpServers": {
    "claude-gemini-mcp": {
      "command": "uv",
      "args": ["run", "claude-gemini-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here",
        "OPENROUTER_API_KEY": "your-openrouter-api-key-here",
        
        "ENABLE_ROUTING": "true",
        "ENABLE_OPENROUTER": "true",
        "ENABLE_PERFORMANCE_MONITORING": "true",
        "ENABLE_COST_TRACKING": "true",
        "ENABLE_TELEMETRY": "true",
        
        "OPENROUTER_DEFAULT_MODEL": "openrouter,openai/gpt-4o-mini",
        "OPENROUTER_BACKGROUND_MODEL": "openrouter,openai/gpt-4o-mini", 
        "OPENROUTER_THINK_MODEL": "openrouter,anthropic/claude-3.5-sonnet",
        "OPENROUTER_LONGCONTEXT_MODEL": "openrouter,moonshot/moonshot-kimi-k2-instruct",
        "OPENROUTER_WEBSEARCH_MODEL": "openrouter,perplexity/llama-3.1-sonar-large-128k-online",
        "OPENROUTER_CODING_MODEL": "openrouter,qwen/qwen3-coder-30b-instruct",
        "OPENROUTER_ANALYSIS_MODEL": "openrouter,zai/glm-4.5",
        "OPENROUTER_MULTIMODAL_MODEL": "openrouter,openai/gpt-4o",
        "OPENROUTER_REASONING_MODEL": "openrouter,deepseek/deepseek-r1-0528"
      }
    }
  }
}
```

## Finding More Models

Visit [OpenRouter.ai](https://openrouter.ai/models) to browse their full model catalog. You can filter by:

- **Context Length**: For long documents
- **Price**: For cost optimization  
- **Modality**: Text-only vs. multimodal
- **Provider**: OpenAI, Anthropic, Google, etc.
- **Performance**: Speed vs. quality tradeoffs

Simply copy the model ID (e.g., `anthropic/claude-3.5-sonnet`) and use it in your environment variables.