Title: 001-Restructuring Helpers Into Tool-Specific Folders
Date: 2025-08-02
Decision Maker: Dr Muhammad Aizat Hawari

## Context
The current helper module structure is flat, leading to less organized code where tool-specific logic and shared utilities are mixed together.

## Decision
We decided to create separate folders for each MCP tool within the helpers directory:

tools
 - codebase_analyzer (folder)
   - codebase_analyzer.py
   - code_analyzer.py

 - analyze_code (folder)
   - analyze_code.py

## Consequences
- Clear separation of tool-specific logic and shared utilities.
- Better organization for scalability and maintainability.
- Aligns with domain-driven design principles.

This structure will allow for more organized testing, easier addition of future tools, and improved code readability.

## **Current Structure (Flat)**
src/claude_gemini_mcp/helpers/
├── analyze_code.py           # Single file analysis
├── codebase_analyzer.py      # Complex codebase analysis
├── code_analyzer.py          # Facade for codebase analysis
├── security.py               # Security utilities
├── markdown_utils.py         # Markdown processing
├── execution_orchestrator.py # AI execution
├── api_key_manager.py        # API key management
├── gemini_api_client.py      # API client
├── gemini_cli_client.py      # CLI client
└── __init__.py

## **Proposed Structure (Organized by Tools)**
src/claude_gemini_mcp/helpers/
├── tools/
│   ├── codebase_analyzer/
│   │   ├── __init__.py
│   │   ├── codebase_analyzer.py    # Complex implementation
│   │   └── code_analyzer.py        # Clean facade
│   └── analyze_code/
│       ├── __init__.py
│       └── analyze_code.py         # Single file analysis
├── security.py                     # Cross-tool utilities
├── markdown_utils.py               # Cross-tool utilities
├── execution_orchestrator.py       # Cross-tool utilities
├── api_key_manager.py              # Cross-tool utilities
├── gemini_api_client.py            # Cross-tool utilities
├── gemini_cli_client.py            # Cross-tool utilities
└── __init__.py

## **Why This is a Great Idea**

### **1. Clear Separation of Concerns**
- **Tool-specific logic** is grouped together
- **Shared utilities** remain at the helper level
- Each tool becomes a self-contained module

### **2. Follows Domain-Driven Design**
- Each MCP tool has its own domain/namespace
- Related files are co-located
- Easy to understand what belongs to what tool

### **3. Scalability Benefits**
- Adding new MCP tools becomes clean and organized
- Each tool can have multiple implementation files
- Testing becomes more organized

### **4. Better Import Structure**
# Clean imports in MCP server
from claude_gemini_mcp.helpers.tools.codebase_analyzer import analyze_codebase
from claude_gemini_mcp.helpers.tools.analyze_code import analyze_code

### **5. Aligns with Project Rules**
This follows your **"Creating New Files"** rule perfectly:
> "Place new files in the correct location according to their responsibility"

## **Suggested Implementation Plan**
### **Phase 1: Create the Structure**
mkdir -p src/claude_gemini_mcp/helpers/tools/codebase_analyzer
mkdir -p src/claude_gemini_mcp/helpers/tools/analyze_code

### **Phase 2: Move Files**
#### Move codebase analysis files
mv src/claude_gemini_mcp/helpers/codebase_analyzer.py src/claude_gemini_mcp/helpers/tools/codebase_analyzer/
mv src/claude_gemini_mcp/helpers/code_analyzer.py src/claude_gemini_mcp/helpers/tools/codebase_analyzer/

#### Move single file analysis
mv src/claude_gemini_mcp/helpers/analyze_code.py src/claude_gemini_mcp/helpers/tools/analyze_code/

### **Phase 3: Create __init__.py Files**
#### src/claude_gemini_mcp/helpers/tools/codebase_analyzer/__init__.py
from .code_analyzer import analyze_codebase
from .codebase_analyzer import CodebaseAnalyzer, CodebaseAnalysisResult

__all__ = ["analyze_codebase", "CodebaseAnalyzer", "CodebaseAnalysisResult"]
# src/claude_gemini_mcp/helpers/tools/analyze_code/__init__.py
from .analyze_code import analyze_code, AnalysisResult, AnalysisType

__all__ = ["analyze_code", "AnalysisResult", "AnalysisType"]
### **Phase 4: Update Imports**
# In gemini_mcp_server.py
from claude_gemini_mcp.helpers.tools.codebase_analyzer import analyze_codebase
from claude_gemini_mcp.helpers.tools.analyze_code import analyze_code
## **Future Tool Organization**
As you add more MCP tools, each gets its own folder:
src/claude_gemini_mcp/helpers/tools/
├── codebase_analyzer/
├── analyze_code/
├── refactor_code/          # Future tool
├── generate_tests/         # Future tool
└── security_audit/         # Future tool
## **Benefits for Testing**
tests/unit/tools/
├── test_codebase_analyzer/
│   ├── test_codebase_analyzer.py
│   └── test_code_analyzer.py
└── test_analyze_code/
    └── test_analyze_code.py
This structure is **much better** than the flat structure and will make the codebase significantly more maintainable as it grows. It clearly separates:
- **Tool-specific logic** (in tools/ folders)
- **Shared utilities** (in helpers/ root)
- **Cross-cutting concerns** (security, execution, etc.)
