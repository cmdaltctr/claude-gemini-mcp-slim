# ADR 006: Structured Response Dependencies Implementation

## Status
**Accepted** - Implemented in Task 4

## Context

The claude-gemini-mcp system has been operating with plain text responses from LLMs, processed through markdown utilities for cleanup. To enable the Agentic Collaboration Protocol (ACP) outlined in CLAUDE.md, we need to evolve toward structured data exchange using validated Pydantic models and the instructor library for enforcing structured JSON responses from Gemini.

### Current State
- Plain text responses from Gemini API/CLI
- Markdown-to-text conversion via `markdown_utils.py`
- Manual parsing and interpretation of LLM outputs
- Limited ability to validate or structure AI responses

### Required Evolution
- Structured JSON responses using Pydantic models
- Automatic validation and error handling
- Intelligent fallback mechanisms
- Foundation for complex agentic workflows

## Decision

We will implement structured response support by:

1. **Adding Core Dependencies**:
   - `instructor[google-generativeai]>=0.6.0` for LLM response structuring
   - `pydantic>=2.0.0` for robust data modeling and validation

2. **Creating Agentic Models** (`agentric_models.py`):
   - `AgenticCodePatch`: Primary model for AI-generated code modifications
   - `CodePatchStep`: Atomic code change representation
   - `AgenticResponse`: Generic wrapper for all agentic operations
   - Supporting models for testing, security, and quality assurance

3. **Maintaining Backward Compatibility**:
   - Existing `markdown_utils.py` functionality preserved
   - Smart processing pipeline with structured-first, markdown-fallback approach
   - No breaking changes to existing MCP server interfaces

## Implementation Details

### Dependency Management
```toml
# pyproject.toml
dependencies = [
    "mcp>=1.0.0",
    "google-generativeai>=0.8.0",
    "instructor[google-generativeai]>=0.6.0",
    "pydantic>=2.0.0",
]
```

### Core Agentic Models

#### AgenticCodePatch
The primary model for structured code generation responses:

```python
class AgenticCodePatch(BaseModel):
    filename: str                           # Target file path
    steps: List[CodePatchStep]             # Atomic modification steps
    summary: str                           # High-level change summary
    motivation: str                        # Why changes are needed
    approach: str                          # Implementation approach
    test_strategy: Optional[TestStrategy]   # Testing considerations
    security: Optional[SecurityConsideration] # Security implications
    confidence: Confidence                 # AI confidence level
    rollback_plan: Optional[str]           # Rollback strategy
```

#### Smart Processing Pipeline
```python
def _process_result_output(result: Dict, convert_markdown: bool, show_progress: bool) -> Dict:
    # Check if result is already structured (from instructor)
    if isinstance(result.get("structured_data"), BaseModel):
        return result  # Already structured - no markdown processing needed
    
    # Fallback to existing markdown processing
    if convert_markdown and MARKDOWN_UTILS_AVAILABLE:
        converted_output = markdown_to_text(result["output"])
        result["output"] = converted_output
    
    return result
```

### Integration Architecture

#### Current Flow
```
gemini_mcp_server.py → gemini_helper.py → markdown_utils.py → plain text
```

#### Enhanced Flow
```
gemini_mcp_server.py → gemini_helper.py (with instructor) → structured objects
                                                         ↓ (fallback)
                                                    markdown_utils.py → plain text
```

### Quality Assurance Features

1. **Validation Rules**:
   - Empty fields validation
   - Diff format validation
   - Filename format validation
   - Step dependency validation

2. **Security Considerations**:
   - Explicit security risk assessment
   - Mitigation tracking
   - Risk level classification

3. **Testing Strategy**:
   - Test type specification
   - Test file requirements
   - Command definitions
   - Assertion requirements

## Consequences

### Positive
- **Structured Data Exchange**: Enables reliable parsing and processing of AI responses
- **Enhanced Validation**: Automatic validation prevents malformed responses
- **Better Error Handling**: Clear error messages and fallback mechanisms
- **ACP Foundation**: Provides infrastructure for advanced agentic workflows
- **Quality Assurance**: Built-in security and testing considerations
- **Backward Compatibility**: Existing functionality remains intact
- **Incremental Adoption**: Can be implemented gradually across different tools

### Potential Challenges
- **Dependency Complexity**: Additional dependencies increase maintenance overhead
- **Learning Curve**: Developers need to understand Pydantic model definitions
- **Performance**: Additional validation may introduce minor performance overhead
- **Fallback Management**: Need to ensure graceful degradation when structured parsing fails

### Mitigation Strategies
- **Comprehensive Testing**: Extensive test coverage for all models and validation rules
- **Documentation**: Clear examples and usage patterns for developers
- **Gradual Rollout**: Implement in stages, starting with high-value use cases
- **Monitoring**: Track success/failure rates of structured vs. fallback responses

## Technical Specifications

### Model Hierarchy
```
AgenticResponse (generic wrapper)
├── AgenticCodePatch (code generation)
│   ├── CodePatchStep[] (atomic changes)
│   ├── TestStrategy (testing approach)
│   └── SecurityConsideration (security aspects)
└── CodeAnalysisResult (analysis results)
```

### Validation Framework
- **Field-level validation**: Using Pydantic validators
- **Cross-field validation**: Custom model validators
- **Type safety**: Full typing support with Union types for flexibility
- **Error reporting**: Detailed validation error messages

### Integration Points
- **gemini_helper.py**: Primary integration point for instructor library
- **execution_orchestrator.py**: Smart processing pipeline implementation
- **helpers/__init__.py**: Export all agentic models for easy access

## Migration Path

### Phase 1: Foundation (Completed in Task 4)
- ✅ Add dependencies (instructor, pydantic)
- ✅ Create core agentic models
- ✅ Implement validation rules
- ✅ Update helper module exports

### Phase 2: Integration (Future Tasks)
- Integrate instructor with gemini_helper.py
- Update execution_orchestrator.py for smart processing
- Add configuration flags for ACP mode
- Implement fallback mechanisms

### Phase 3: Adoption (Future Tasks)
- Convert existing tools to use structured responses
- Add monitoring and metrics
- Performance optimization
- Advanced agentic workflow implementation

## Success Metrics

1. **Technical Metrics**:
   - Structured response success rate > 90%
   - Validation error rate < 5%
   - Fallback usage rate < 20%
   - No regression in existing functionality

2. **Quality Metrics**:
   - Code coverage > 95% for agentic models
   - All validation rules tested
   - Security considerations documented
   - Performance impact < 10% latency increase

3. **Developer Experience**:
   - Clear error messages for validation failures
   - Comprehensive documentation and examples
   - Smooth migration path for existing tools

## References

- **CLAUDE.md**: Golden Rules for Agentic Collaboration Protocol
- **instructor library documentation**: https://python.useinstructor.com/
- **Pydantic v2 documentation**: https://docs.pydantic.dev/latest/
- **ADR 003**: Markdown Utilities Implementation (backward compatibility)
- **Task 4**: Add Required Dependencies for Structured Response Support

## Implementation Artifacts

- `src/claude_gemini_mcp/helpers/agentric_models.py`: Core model definitions
- `pyproject.toml`: Updated dependency specifications
- `requirements.txt`: Updated runtime dependencies
- `src/claude_gemini_mcp/helpers/__init__.py`: Updated exports

---

**Date**: 2025-01-04  
**Author**: Claude Code Assistant  
**Reviewers**: Project Team  
**Related Tasks**: Task 4 - Add Required Dependencies for Structured Response Support