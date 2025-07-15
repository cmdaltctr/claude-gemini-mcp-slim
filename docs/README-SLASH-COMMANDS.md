# Slash Commands Reference

This document provides comprehensive documentation for all available slash commands in the Claude Gemini MCP integration. These commands provide quick access to Gemini's AI capabilities directly within Claude Code.

## Overview

Slash commands are shortcuts that allow you to interact with Gemini AI without manually calling MCP tools. They automatically route your requests to the appropriate Gemini functionality and handle parameter mapping for seamless integration.

## Command Categories

### Core Commands

#### `/gemini [question]`
**Purpose:** Ask Gemini any development question
**Alias:** `/g`
**Uses:** `gemini_quick_query`

Query Gemini for instant answers to coding questions, explanations, and general development guidance.

**Examples:**
```
/gemini How do I implement JWT authentication in Node.js?
/gemini What's the difference between React hooks and class components?
/gemini Best practices for error handling in Python async functions?
```

**When to use:**
- Quick coding questions
- Language syntax clarification
- Best practices inquiries
- General development guidance

#### `/analyze [file_path] [analysis_type]`
**Purpose:** Analyze code files with comprehensive insights
**Alias:** `/a`
**Uses:** `gemini_analyze_code`

Perform deep analysis of specific code files, functions, or modules with focus on security, performance, and architecture.

**Parameters:**
- `file_path` (required): Path to the file to analyze
- `analysis_type` (optional): Focus area - `security`, `performance`, `architecture`, or `comprehensive`

**Examples:**
```
/analyze src/auth.py security
/analyze components/UserForm.vue
/analyze ./utils/database.js performance
/analyze models/user.js comprehensive
```

**When to use:**
- Before making significant changes to a file
- Code review and quality assessment
- Security vulnerability scanning
- Performance optimization planning

#### `/codebase [directory_path] [scope]`
**Purpose:** Analyze entire directories using Gemini's large context window
**Alias:** `/c`
**Uses:** `gemini_codebase_analysis`

Leverage Gemini's 1M+ token context to analyze complete codebases, multiple files, and project architecture.

**Parameters:**
- `directory_path` (required): Path to directory to analyze
- `scope` (optional): Analysis scope - `security`, `performance`, `architecture`, `structure`, or `all`

**Examples:**
```
/codebase ./src
/codebase ./components security
/codebase . all
/codebase ./api architecture
```

**When to use:**
- Project architecture review
- Large-scale refactoring planning
- Security audit of entire modules
- Understanding unfamiliar codebases

### Developer Assistance Commands

#### `/explain [code_or_concept]`
**Purpose:** Get detailed explanations of code concepts or functions
**Alias:** `/e`
**Uses:** `gemini_quick_query`

Receive comprehensive explanations of programming concepts, code snippets, error messages, or technical terms.

**Examples:**
```
/explain async/await in JavaScript
/explain const handleSubmit = async (data) => {...}
/explain TypeError: Cannot read property 'map' of undefined
/explain dependency injection pattern
```

**When to use:**
- Learning new concepts
- Understanding complex code patterns
- Deciphering error messages
- Code documentation and comments

#### `/debug [code_or_error]`
**Purpose:** Get debugging assistance for code issues
**Alias:** `/d`
**Uses:** `gemini_quick_query`

Receive specific debugging help, error analysis, and solution suggestions for code problems.

**Examples:**
```
/debug ReferenceError: fetch is not defined
/debug Why is my React component not re-rendering?
/debug Memory leak in my Python application
/debug SQL query returning incorrect results
```

**When to use:**
- Troubleshooting runtime errors
- Investigating unexpected behavior
- Performance issues
- Logic errors and bugs

## Command Structure

### Syntax Pattern
All commands follow a consistent pattern:
```
/[command] [required_parameter] [optional_parameter]
```

### Parameter Types
- **File paths:** Relative or absolute paths to files
- **Directory paths:** Paths to directories for codebase analysis
- **Analysis types:** Specific focus areas for targeted analysis
- **Free text:** Questions, code snippets, or descriptions

### Smart Parameter Handling
Commands automatically handle different input types:
- **File references:** Automatically reads file content when file paths are provided
- **Code snippets:** Processes inline code blocks and functions
- **Error messages:** Formats error text for optimal analysis
- **Mixed content:** Handles combinations of text and code

## Usage Patterns

### Quick Development Workflow
```
/g How do I handle form validation in Vue 3?
/a ./components/ContactForm.vue
/explain this.$emit('submit', formData)
```

### Code Review Workflow
```
/a src/authentication.py security
/c ./api security
/debug Authentication failing for certain users
```

### Learning Workflow
```
/explain React useEffect hook
/g What are the differences between useState and useReducer?
/debug useEffect running infinitely
```

### Architecture Planning
```
/c ./src architecture
/g How should I structure a microservices project?
/analyze ./config/database.js performance
```

## Advanced Features

### Analysis Type Optimization
Different analysis types trigger optimized prompts:
- **Security:** Focuses on vulnerabilities, injection attacks, authentication flaws
- **Performance:** Emphasizes bottlenecks, optimization opportunities, resource usage
- **Architecture:** Reviews design patterns, modularity, maintainability
- **Comprehensive:** Balanced analysis covering all aspects

### Smart Model Selection
Commands automatically choose the optimal Gemini model:
- **Quick queries:** Use Gemini Flash for fast responses
- **Code analysis:** Use Gemini Pro for detailed insights
- **Codebase analysis:** Use Gemini Pro for complex context handling

### Error Handling
Commands provide helpful error messages and suggestions:
- Invalid file paths show directory contents
- Missing parameters display usage examples
- Tool failures provide alternative approaches

## Integration Benefits

### Developer Experience
- **Immediate access:** No need to remember MCP tool names
- **Consistent syntax:** All commands follow similar patterns
- **Smart defaults:** Parameters automatically optimized for common use cases
- **Fast execution:** Streamlined requests reduce latency

### Code Quality
- **Proactive analysis:** Easy to analyze code before making changes
- **Comprehensive coverage:** Full project analysis with single commands
- **Expert insights:** Gemini's advanced AI provides professional-grade analysis
- **Learning integration:** Commands double as learning tools

### Workflow Integration
- **Claude Code native:** Works seamlessly within Claude Code environment
- **Project-agnostic:** Commands work in any codebase without configuration
- **Scalable usage:** From single files to entire projects
- **Documentation support:** Self-documenting through examples and help text

## Best Practices

### Effective Command Usage
1. **Start specific:** Use `/analyze` for targeted file analysis before broader `/codebase` review
2. **Use aliases:** Leverage short aliases (`/g`, `/a`, `/c`) for faster typing
3. **Specify focus:** Include analysis types (`security`, `performance`) for targeted insights
4. **Combine approaches:** Use multiple commands for comprehensive understanding

### Optimal Analysis Strategy
1. **File-level analysis first:** Understand individual components with `/analyze`
2. **Module-level review:** Analyze related files in directories with `/codebase`
3. **Project-level assessment:** Review entire architecture with `/codebase . all`
4. **Iterative refinement:** Use insights to guide deeper analysis

### Learning Integration
1. **Question-driven exploration:** Use `/g` to understand concepts before implementation
2. **Code-driven learning:** Use `/explain` on unfamiliar code patterns
3. **Problem-driven debugging:** Use `/debug` to learn from errors and issues
4. **Review-driven improvement:** Use `/analyze` to learn better coding practices

## Technical Implementation

### Command Processing
1. **Input parsing:** Commands extract parameters and validate syntax
2. **Tool routing:** Parameters determine appropriate MCP tool selection
3. **Parameter mapping:** Arguments are formatted for MCP tool requirements
4. **Response handling:** Results are formatted for optimal readability

### Integration Architecture
- **Native Claude Code support:** Commands are processed by Claude Code's slash command system
- **MCP tool abstraction:** Commands hide MCP complexity behind simple interfaces
- **File system integration:** Automatic file reading and path resolution
- **Error recovery:** Graceful handling of tool failures and invalid inputs

This slash command system transforms complex MCP tool interactions into intuitive, developer-friendly shortcuts that enhance productivity and code quality within the Claude Code environment.
