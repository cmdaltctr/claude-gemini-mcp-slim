# 004-Middleware-Routing-Architecture
Date: 2025-08-03  
Decision Maker: Dr Muhammad Aizat Hawari  
Status: Accepted  

## Context
The claude-gemini-mcp-slim project required intelligent model routing and multi-provider support to enable dynamic AI model selection based on scenario, context, cost, and performance requirements. The existing architecture used a single Gemini provider with API-first, CLI-fallback pattern that needed to be extended without breaking backward compatibility.

## Decision
The decision was made to integrate claude-code-router concepts through a comprehensive middleware architecture implemented in two phases:

**Phase 1 (Task 16.1): Enhanced Model Routing**
- Implement scenario-based routing with middleware pattern
- Create provider abstraction layer with BaseProvider interface
- Integrate routing engine into execution_orchestrator.py
- Maintain backward compatibility with routing disabled by default

**Phase 2 (Task 16.2): Multi-Provider Support**  
- Implement OpenRouter as unified multi-provider hub
- Add comprehensive model catalog for global AI platforms
- Include Chinese AI models (DeepSeek, Qwen3, Kimi K2, GLM-4.5)
- Create request/response transformers for provider normalization

## Consequences

### Phase 1 Benefits
- **Intelligent Orchestration**: Dynamic model selection based on request context
- **Scenario-Based Routing**: Optimized routing for default, background, think, longContext, webSearch scenarios
- **Provider Abstraction**: Extensible architecture for future provider integrations
- **Backward Compatibility**: Existing Gemini API/CLI patterns preserved
- **Configuration Driven**: Routing can be enabled/disabled via configuration

### Phase 2 Benefits  
- **Multi-Provider Access**: 10+ models from 7 providers via unified interface
- **Global AI Platform Support**: Access to OpenAI, Anthropic, Google, Chinese AI models
- **Cost Optimization**: Per-token pricing awareness and cost-efficient routing
- **Context Window Scaling**: Support from 16K to 2M+ token context windows
- **Agentic Capabilities**: Specialized coding models with agentic workflows

### Technical Achievements
- **Architectural Integrity**: Decoupled middleware pattern following CLAUDE.md guidelines
- **Error Handling**: Comprehensive retry logic and fallback mechanisms
- **Request Transformation**: OpenAI-compatible format normalization
- **Health Monitoring**: Provider health checking and status reporting
- **Performance Optimization**: Token-aware and cost-aware routing strategies

## Architectural Components

### Core Middleware Structure
```
src/claude_gemini_mcp/middleware/
├── __init__.py                    # Public API exports
├── router.py                      # Core routing engine
├── providers/                     # Provider implementations
│   ├── base_provider.py          # Abstract provider interface  
│   ├── gemini_provider.py        # Gemini API/CLI provider
│   └── openrouter_provider.py    # Multi-provider hub
├── routing_strategies/            # Routing algorithms
│   ├── scenario_router.py        # Scenario-based routing
│   ├── token_aware_router.py     # Context window optimization
│   └── cost_optimizer.py         # Cost-efficient routing
└── transformers/                  # Request/response normalization
    ├── request_transformer.py    # Provider-specific formatting
    └── response_transformer.py   # Response standardization
```

### Integration Points
- **Configuration Extension**: Enhanced config.py with routing scenarios and provider settings
- **Execution Integration**: Router integration in execution_orchestrator.py with legacy fallback
- **Provider Selection**: Dynamic provider and model selection based on context analysis

## Model Support Matrix

### Phase 1 - Gemini Provider
- gemini-2.5-pro: Advanced reasoning and analysis
- gemini-2.5-flash: Fast responses and efficiency

### Phase 2 - OpenRouter Multi-Provider Hub
**OpenAI Models:**
- openai/gpt-4o-mini: Cost-effective multimodal capabilities

**Anthropic Models:**  
- anthropic/claude-3-haiku: Fast and efficient reasoning

**Google Models:**
- google/gemini-flash-1.5: Large context with speed

**Chinese AI Models:**
- deepseek/deepseek-chat: Cost-effective conversational AI
- deepseek/deepseek-r1-0528: Latest reasoning model
- qwen/qwen3-coder-30b-instruct: Agentic coding capabilities
- qwen/qwen3-coder-480b-a35b-instruct: Advanced agentic coding
- moonshot/moonshot-kimi-k2-instruct: Long context reasoning
- zai/glm-4.5: State-of-the-art Chinese model
- zai/glm-4.5-air: Efficient performance variant

## Routing Strategies

### Scenario-Based Routing
- **Default**: Balanced performance and cost
- **Background**: Cost-optimized for batch processing  
- **Think**: Reasoning-capable models for complex analysis
- **LongContext**: Models with large context windows
- **WebSearch**: Models optimized for information retrieval

### Context-Aware Selection
- **Token Count Analysis**: Automatic model selection based on input/output requirements
- **Content Type Detection**: Code vs text optimization
- **Cost Efficiency**: Per-token pricing optimization
- **Performance Requirements**: Speed vs accuracy trade-offs

## Backward Compatibility Strategy
- **Legacy Pattern Preservation**: Existing API-first, CLI-fallback maintained
- **Optional Routing**: Routing disabled by default, enabled via configuration
- **Graceful Degradation**: Automatic fallback to legacy patterns on routing failure
- **Configuration Compatibility**: Existing settings continue to work unchanged

## Architectural Alignment
The middleware architecture aligns with our established principles:
- **Decoupled Module Pattern**: Independent, testable components
- **Intelligent Orchestrator Philosophy**: Adding value through smart orchestration
- **Security First**: Input validation and error handling throughout
- **Configuration Driven**: Flexible behavior modification through settings
- **Extensible Design**: Easy addition of new providers and routing strategies

## Performance and Quality
- **Diagnostic Issue Resolution**: Fixed cost optimizer and token-aware router issues
- **Code Quality**: Comprehensive error handling and logging
- **Testing Integration**: All components tested and validated
- **Commit Standards**: Proper conventional commit formatting maintained

## Reference
**Phase 1 Implementation:** Task 16.1 - Enhanced Model Routing  
**Phase 2 Implementation:** Task 16.2 - Multi-Provider Support  
**Originating Commits:** 
- Phase 1: e3b367b - Enhanced model routing with middleware architecture
- Phase 2: bc9038b - Multi-provider support with OpenRouter integration

**External Reference:** https://github.com/musistudio/claude-code-router

The comprehensive integration of middleware routing architecture establishes claude-gemini-mcp-slim as an intelligent AI orchestration platform capable of dynamic model selection across global AI providers while maintaining architectural integrity and backward compatibility.