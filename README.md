# Claude Gemini MCP Slim v3.2 - Complete Feature Guide

> **Intelligent AI Orchestrator with Advanced Routing & Multi-Provider Support**

A sophisticated Model Context Protocol (MCP) server that provides intelligent orchestration between Claude Code and Google's Gemini AI models, featuring advanced routing capabilities, structured response handling, and comprehensive development tools.

---

## 🌟 Core Philosophy: Intelligent Orchestration

This MCP server operates as an **Intelligent Orchestrator**, not a simple bridge. It adds significant value through:

- **Agentic Process**: Perception → Reasoning → Orchestration → Transformation → Action
- **Multi-Contextual Platform Integration**: Leveraging specialized MCP servers for enhanced capabilities
- **Structured Data Exchange**: Evolution from plain text to validated, structured responses using Pydantic
- **Decoupled Architecture**: Specialized components working in harmony

---

## 🏗️ Architecture Overview

### **Decoupled Module Pattern**

- **`gemini_mcp_server.py`** - *The Communicator*: MCP request/response handling
- **`gemini_helper.py`** - *The AI Specialist*: Gemini backend interactions
- **`helpers/`** - *Pre/Post-Processing Engines*: Specialized task handlers
- **`config/`** - *Configuration Registry*: Intelligent orchestrator for settings
- **`middleware/`** - *Advanced Routing Engine*: Multi-provider orchestration

### **Key Technologies & Frameworks**

- **MCP (Model Context Protocol)**: Core communication framework
- **Pydantic v2**: Structured data validation and serialization
- **Google Generative AI**: Primary AI backend integration
- **Instructor**: Enhanced structured LLM responses
- **Advanced Router**: Intelligent model selection and provider routing
- **Comprehensive Testing**: pytest with multiple test categories

---

## 🚀 Available MCP Tools

### **1. gemini_quick_query**
Quick development questions and simple tasks.

```json
{
  "query": "How do I implement a Python decorator?",
  "context": "Working on a Flask application"
}
```

**Features:**
- Context-aware responses
- Markdown conversion
- Security sanitization
- Configurable limits

### **2. gemini_analyze_code**
Detailed code analysis with multiple focus areas.

```json
{
  "code_content": "def process_data(data): return data.upper()",
  "analysis_type": "comprehensive" // or "security", "performance", "architecture"
}
```

**Analysis Types:**
- **Comprehensive**: Full code review
- **Security**: Vulnerability assessment
- **Performance**: Optimization opportunities
- **Architecture**: Design patterns and structure

### **3. gemini_codebase_analysis**
Large-scale codebase analysis using Gemini's 1M token context.

```json
{
  "directory_path": "/path/to/project",
  "analysis_scope": "all" // or "structure", "security", "performance", "patterns"
}
```

**Capabilities:**
- Technology stack detection
- Directory structure analysis
- Security scanning
- Performance pattern identification
- Project health assessment

---

## ⚙️ Configuration System

### **Intelligent Configuration Registry**

The system uses a sophisticated configuration architecture with specialized components:

#### **Core Configuration Components:**

1. **CoreConfigManager**: Foundation settings and limits
2. **RoutingConfigManager**: Advanced routing with 26+ methods
3. **ModelConfigManager**: Model resolution and assignments
4. **EnvironmentConfigLoader**: Environment variable processing

#### **Configuration File Structure (`config.json`)**

```json
{
  "models": {
    "nicknames": {
      "flash": "gemini-2.5-flash",
      "pro": "gemini-2.5-pro",
      "flash-8b": "gemini-2.5-flash-8b"
    },
    "assignments": {
      "quick_query": "flash",
      "analyze_code": "pro",
      "analyze_codebase": "pro"
    }
  },
  "limits": {
    "max_file_size": 81920,
    "max_lines": 800,
    "max_prompt_size": 50000
  },
  "routing": {
    "enabled": false,
    "providers": {
      "gemini": {
        "enabled": true,
        "models": ["gemini-2.5-flash", "gemini-2.5-pro"],
        "api_key_env": "GEMINI_API_KEY"
      }
    }
  }
}
```

### **Environment Variables**

- `GEMINI_API_KEY`: Required for Gemini access
- `GEMINI_FORCE_MODEL`: Override model selection
- `MCP_DEBUG`: Enable debug logging
- `OPENROUTER_API_KEY`: For OpenRouter provider (when enabled)

---

## 🧠 Advanced Routing Engine

### **Router Architecture**

The routing system provides intelligent model selection and provider orchestration:

#### **Routing Strategies:**

1. **Scenario-Based**: Predefined scenarios (background, think, longContext, webSearch)
2. **Token-Aware**: Context window optimization
3. **Performance-Optimized**: Speed and reliability focus
4. **Cost-Optimized**: Economic efficiency
5. **Balanced**: Combines multiple factors

#### **Multi-Provider Support:**

- **Gemini Provider**: Primary Google AI integration
- **OpenRouter Provider**: Access to multiple model providers
- **Extensible Architecture**: Easy addition of new providers

#### **Advanced Features:**

```json
{
  "routing": {
    "preferences": {
      "routing_strategy": "balanced",
      "speed_priority": 0.7,
      "cost_sensitivity": 0.5,
      "quality_threshold": 6.0,
      "enable_adaptive_routing": true
    },
    "performance": {
      "max_response_time": 30.0,
      "min_success_rate": 0.85,
      "enable_performance_monitoring": true
    },
    "cost_optimization": {
      "enable_cost_tracking": true,
      "cost_models": {
        "gemini/gemini-2.5-flash": {"input": 0.075, "output": 0.3},
        "gemini/gemini-2.5-pro": {"input": 1.25, "output": 5.0}
      }
    },
    "telemetry": {
      "enabled": true,
      "max_records": 10000,
      "enable_detailed_logging": true
    }
  }
}
```

---

## 🔄 Agentic Collaboration Protocol (ACP)

### **Structured Response Models**

The system implements structured data exchange using Pydantic models:

#### **AgenticCodePatch**
For code generation and modification:

```python
class AgenticCodePatch(BaseModel):
    filename: str
    steps: List[CodePatchStep]
    summary: str
    motivation: str
    approach: str
    test_strategy: Optional[TestStrategy]
    security: Optional[SecurityConsideration]
    confidence: Confidence
```

#### **CodeAnalysisResult**
For code analysis responses:

```python
class CodeAnalysisResult(BaseModel):
    filename: str
    analysis_type: str
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    metrics: Dict[str, Union[int, float, str]]
    overall_score: Optional[float]
```

---

## 🛠️ Development Tools & Helpers

### **Execution Orchestrator**

Intelligent request routing and execution:

- **Smart Execution**: `execute_gemini_smart()` with fallback strategies
- **Progress Tracking**: Real-time execution feedback
- **Error Handling**: Comprehensive error recovery
- **Performance Monitoring**: Response time and success tracking

### **Security Features**

Comprehensive security implementation:

- **Input Sanitization**: `sanitize_for_prompt()`
- **Path Validation**: `validate_path_security()`
- **Content Filtering**: Malicious content detection
- **API Key Management**: Secure credential handling

### **Hybrid Progress System**

Advanced progress reporting:

- **Streaming Updates**: Real-time progress indicators
- **Multi-stage Tracking**: Complex operation monitoring
- **Error Recovery**: Graceful failure handling
- **MCP Integration**: Progress events via MCP protocol

---

## 📊 Testing Infrastructure

### **Comprehensive Test Suite**

The project includes extensive testing across multiple categories:

#### **Test Categories:**

- **Unit Tests**: `tests/unit/` - Component-level testing
- **Integration Tests**: `tests/integration/` - System integration
- **End-to-End Tests**: `tests/e2e/` - Full workflow validation
- **Security Tests**: Security-focused validation
- **Performance Tests**: Response time and throughput
- **Matrix Tests**: Configuration combination testing

#### **Test Tools & Commands**

```bash
# Fast unit tests
make test-fast

# Integration tests
make test-integration

# All tests with coverage
make test-all

# Specific test patterns
make test-specific TEST_PATTERN="tests/unit/test_config.py"

# Debug mode
make test-debug TEST_PATTERN="tests/integration/test_gemini_api_mocked.py"
```

#### **Quality Assurance Tools**

- **pytest**: Test framework with async support
- **pytest-cov**: Code coverage reporting
- **black**: Code formatting
- **flake8**: Linting and style checking
- **mypy**: Type checking
- **bandit**: Security vulnerability scanning
- **pip-audit**: Dependency vulnerability scanning

---

## 📦 Installation & Setup

### **Prerequisites**

- Python 3.10 or higher
- Google AI API key
- Virtual environment (recommended)

### **Installation Steps**

1. **Clone and Setup**:
```bash
git clone <repository-url>
cd claude-gemini-mcp-slim
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
```

2. **Install Dependencies**:
```bash
pip install -e .
# or for development
pip install -e ".[dev]"
```

3. **Configuration**:
```bash
# Copy example configuration
cp config.json.example config.json

# Set environment variables
export GEMINI_API_KEY="your-api-key-here"
```

4. **Verify Installation**:
```bash
python -m pytest tests/test_basic_operations.py -v
```

### **MCP Server Registration**

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "claude-gemini-mcp": {
      "command": "python",
      "args": ["/path/to/claude-gemini-mcp-slim/src/claude_gemini_mcp/gemini_mcp_server.py"],
      "env": {
        "GEMINI_API_KEY": "your-api-key",
        "OPENROUTER_API_KEY": "your-openrouter-api-key"
      }
    }
  }
}
```

#### **🔑 Complete Environment Variable Reference**

Based on the code analysis, here are all supported environment variables:

```json
{
  "mcpServers": {
    "claude-gemini-mcp": {
      "command": "python",
      "args": ["/path/to/claude-gemini-mcp-slim/src/claude_gemini_mcp/gemini_mcp_server.py"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key",
        "OPENROUTER_API_KEY": "your-openrouter-api-key",
        "GEMINI_FORCE_MODEL": "gemini-2.5-pro",
        "MCP_DEBUG": "true",
        "GEMINI_DEBUG": "true"
      }
    }
  }
}
```

**Environment Variable Descriptions:**
- `GEMINI_API_KEY`: **Required** - Your Google AI API key
- `OPENROUTER_API_KEY`: **Optional** - Your OpenRouter API key (needed for multi-provider routing)
- `GEMINI_FORCE_MODEL`: **Optional** - Override model selection (e.g., "gemini-2.5-pro")
- `MCP_DEBUG`: **Optional** - Enable MCP debug logging ("true"/"false")
- `GEMINI_DEBUG`: **Optional** - Enable Gemini-specific debug logging ("true"/"false")

#### **⚙️ Enable OpenRouter Multi-Provider Routing**

To use OpenRouter alongside Gemini, update your `config.json`:

```json
{
  "routing": {
    "enabled": true,
    "providers": {
      "gemini": {
        "enabled": true,
        "api_key_env": "GEMINI_API_KEY",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-8b"]
      },
      "openrouter": {
        "enabled": true,
        "api_key_env": "OPENROUTER_API_KEY",
        "models": ["google/gemini-2.5-pro-preview", "anthropic/claude-3.5-sonnet"],
        "api_base_url": "https://openrouter.ai/api/v1/chat/completions"
      }
    },
    "scenarios": {
      "default": "gemini,gemini-2.5-flash",
      "background": "gemini,gemini-2.5-flash-8b", 
      "think": "gemini,gemini-2.5-pro",
      "longContext": "openrouter,anthropic/claude-3.5-sonnet"
    },
    "fallback_strategy": "provider_cascade",
    "retry_attempts": 2
  }
}
```

**Note**: When routing is enabled, the system will intelligently select between providers based on the configured scenarios and performance metrics.

---

## 🔧 Advanced Configuration

### **Model Management**

The system supports sophisticated model selection:

```python
# Get model for specific tool
model = config.get_model("analyze_code")  # Returns "gemini-2.5-pro"

# Force model override
export GEMINI_FORCE_MODEL="gemini-2.5-flash"

# Register new tool assignments
config.register_tool_if_missing("custom_tool", "pro")
```

### **Routing Configuration**

Enable advanced routing for multi-provider support:

```json
{
  "routing": {
    "enabled": true,
    "scenarios": {
      "background": "gemini,gemini-2.5-flash-8b",
      "think": "gemini,gemini-2.5-pro",
      "longContext": "gemini,gemini-2.5-pro"
    },
    "fallback_strategy": "provider_cascade",
    "retry_attempts": 2
  }
}
```

### **Performance Tuning**

Optimize for your use case:

```json
{
  "limits": {
    "max_file_size": 81920,
    "max_lines": 800,
    "max_prompt_size": 50000,
    "timeout_api": 60,
    "timeout_cli": 120
  },
  "execution": {
    "enable_streaming": true,
    "enable_progress": true,
    "enable_fallback": true
  }
}
```

---

## 🎯 Usage Examples

### **Quick Development Query**

```javascript
// Claude Code usage
await mcp.callTool("gemini_quick_query", {
  query: "How do I implement JWT authentication in FastAPI?",
  context: "Building a REST API with user authentication"
});
```

### **Code Analysis**

```javascript
// Analyze security issues
await mcp.callTool("gemini_analyze_code", {
  code_content: readFileSync("auth.py", "utf8"),
  analysis_type: "security"
});
```

### **Codebase Analysis**

```javascript
// Full project analysis
await mcp.callTool("gemini_codebase_analysis", {
  directory_path: "./src",
  analysis_scope: "all"
});
```

---

## 🚨 Error Handling & Debugging

### **Built-in Error Recovery**

- **Fallback Strategies**: Automatic CLI fallback when API fails
- **Retry Logic**: Configurable retry attempts with exponential backoff
- **Provider Cascade**: Fallback through available providers
- **Graceful Degradation**: Partial functionality when components fail

### **Debug Mode**

Enable comprehensive debugging:

```bash
export MCP_DEBUG=true
export GEMINI_DEBUG=true
python src/claude_gemini_mcp/gemini_mcp_server.py
```

### **Health Monitoring**

```python
# Check router health
health = await router.health_check()
print(health)

# Get performance metrics
performance = router.get_performance_summary()
analytics = router.get_routing_analytics(hours_back=24)
```

---

## 📈 Performance Metrics

### **Built-in Telemetry**

The system provides comprehensive performance tracking:

- **Request Tracking**: Success rates, response times, error patterns
- **Provider Performance**: Model-specific metrics and health monitoring
- **Cost Tracking**: Token usage and cost optimization
- **Routing Analytics**: Decision patterns and strategy effectiveness

### **Monitoring Dashboard Data**

```python
# Get routing statistics
stats = router.get_stats()
# {
#   "total_requests": 1250,
#   "successful_routes": 1198,
#   "fallback_attempts": 12,
#   "average_execution_time": 2.3
# }

# Export telemetry data
data = router.export_telemetry_data("json")
```

---

## 🤝 Contributing & Development

### **Development Workflow**

1. **Setup Development Environment**:
```bash
pip install -e ".[dev]"
```

2. **Run Quality Checks**:
```bash
make check          # Quick development check
make validate       # Full validation
make ci            # CI pipeline simulation
```

3. **Code Standards**:
- Follow the Agentic Collaboration Protocol (ACP)
- Use Pydantic models for structured responses
- Maintain decoupled architecture
- Include comprehensive tests
- Follow security best practices

### **Testing Standards**

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **Security Tests**: Validate security measures
- **Performance Tests**: Verify response times
- **End-to-End Tests**: Complete workflow validation

---

## 🔐 Security Features

### **Comprehensive Security Implementation**

- **Input Sanitization**: All user inputs are sanitized
- **Path Validation**: Secure file system access
- **API Key Protection**: Secure credential management
- **Content Filtering**: Malicious content detection
- **Dependency Scanning**: Regular vulnerability checks

### **Security Tools**

- **bandit**: Security vulnerability scanning
- **pip-audit**: Dependency vulnerability checking
- **safety**: Known security issue detection

---

## 📚 Documentation & Resources

### **Architecture Documentation**

- `PRD/AI_DEVELOPMENT_GUIDELINES.md`: Comprehensive development guidelines
- `docs/DEVELOPMENT.md`: Development setup and practices
- `docs/TESTING.md`: Testing methodology and practices
- `docs/SECURITY.md`: Security implementation details

### **API Reference**

- **Configuration API**: `config/` module documentation
- **Routing API**: `middleware/router.py` comprehensive interface
- **Helper APIs**: `helpers/` module utilities
- **Structured Models**: `helpers/agentric_models.py` Pydantic schemas

---

## 🎉 Getting Started Checklist

- [ ] Install Python 3.10+
- [ ] Clone repository and setup virtual environment
- [ ] Install dependencies: `pip install -e ".[dev]"`
- [ ] Set `GEMINI_API_KEY` environment variable
- [ ] Copy `config.json.example` to `config.json`
- [ ] Run smoke test: `make test-smoke`
- [ ] Register MCP server in Claude Code
- [ ] Test with a simple query
- [ ] Explore advanced routing features
- [ ] Set up monitoring and telemetry

---

## 💡 What Makes This MCP Special

1. **Intelligent Orchestration**: Not just a bridge, but an intelligent agent
2. **Advanced Routing**: Multi-provider support with intelligent selection
3. **Structured Responses**: Pydantic-based data validation and serialization
4. **Comprehensive Testing**: Multiple test categories with 85%+ coverage
5. **Security First**: Built-in security measures and validation
6. **Performance Monitoring**: Real-time telemetry and analytics
7. **Extensible Architecture**: Easy to add new providers and capabilities
8. **Production Ready**: Comprehensive error handling and fallback strategies

---

**Ready to enhance your AI development workflow with intelligent orchestration?**

Start with `make test-smoke` and explore the capabilities of your new AI-powered development assistant!