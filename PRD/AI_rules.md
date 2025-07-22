# AI Agent Golden Rules for the Claude-Gemini MCP Project

This document provides essential rules and guidelines for any AI agent interacting with or modifying this codebase. Adherence to these rules is mandatory to ensure consistency, security, and maintainability.

---

## 1. Core Philosophy: You are an Intelligent Orchestrator

**DO:** Act as an intelligent agent, not a simple bridge. Your primary role is to add value by orchestrating complex workflows.
**DO:** Understand the five steps of your agentic process: Perception (receiving a task), Reasoning (choosing a model/tool), Orchestration (constructing a detailed prompt), Transformation (formatting the result), and Action (responding to the client).

### 1.1. Leveraging Multi-Contextual Platforms (MCPs)

**DO:** Utilize various MCP servers to enhance agentic AI capabilities and workflow orchestration. These platforms provide specialized contexts and functionalities that allow our AI tools to operate effectively and intelligently.

- **Context7 (e.g., `resolve-library-id`, `get-library-docs`):** Used for comprehensive documentation and knowledge retrieval, enabling the agent to access and understand vast amounts of technical information.
- **Perplexity (e.g., `perplexity-ask`, `perplexity-research`, `perplexity-reason`):** Leveraged for advanced reasoning, deep research, and conversational AI, providing the agent with sophisticated analytical capabilities.
- **Git and GitHub MCP (e.g., `git-status`, `github-create-pull-request`, `github-list-issues`):** Essential for version control, code management, and collaborative development, allowing the agent to interact seamlessly with Git repositories and GitHub workflows.
- **JetBrains MCP (e.g., `execute-action-by-id`, `get-file-text-by-path`, `replace-current-file-text`):** Provides direct interaction with the JetBrains IDE environment, enabling the agent to perform in-editor code modifications, run commands, and access project context.
- **Pieces MCP (e.g., `create-pieces-memory`, `ask-pieces-ltm`):** Used for long-term memory management and contextual recall, allowing the agent to store and retrieve critical information and past experiences.
- **Sequential Thinking MCP (e.g., `sequentialthinking`):** Facilitates complex problem-solving through structured, iterative thought processes, enabling the agent to break down tasks, revise approaches, and verify hypotheses.

These MCPs collectively empower the agent to perform a wide range of software engineering tasks with enhanced intelligence, context awareness, and operational efficiency.
**DON'T:** Merely pass raw text between the client and the AI backend.

---

## 2. Architectural Integrity

### 2.1. The Decoupled Module Pattern

**DO:** Strictly adhere to the project's decoupled architecture.

- **`gemini_mcp_server.py`:** This is **The Communicator**. Its sole responsibility is handling MCP requests and responses. It orchestrates the workflow by calling other modules. **It must not contain direct AI API call logic.**
- **`gemini_helper.py`:** This is **The AI Specialist**. Its sole responsibility is to manage all interactions with the Gemini backend (API or CLI).
- **`helpers/` directory:** This contains specialized **Pre-Processing and Post-Processing Engines**. Use these helpers for their specific tasks (e.g., `codebase_analyzer`, `markdown_utils`).

**DON'T:** Add AI interaction logic to the server module. Don't add MCP communication logic to the helper module.

### 2.2. Configuration Management

**DO:** Use the central configuration system for all settings.

- Read all configuration values (model names, timeouts, limits, feature flags) by calling the accessor functions in `config.py` (e.g., `cfg.get_model()`, `cfg.get_limit()`).
  **DON'T:** Ever use `os.getenv()` or hard-code any configuration values outside of `config.py`.

---

## 3. Code Modification and Generation

### 3.1. Agentic Data Flow (ACP)

**DO:** Prioritize the Agentic Collaboration Protocol. When modifying or implementing features like `analyze_code`, your primary goal is to use the `instructor` library to request a structured JSON object (e.g., `AgenticCodePatch`) from the Gemini API.
**DON'T:** Default to requesting plain text from the AI. The evolution of this project depends on moving towards structured data exchange.

### 3.2. Documentation and Clarity

**DO:** Generate code that is well-documented.

- **Docstrings:** All new public functions, methods, and classes must include a docstring explaining their purpose, arguments (`Args:`), and return values (`Returns:`).
- **Type Hinting:** Use Python type hints for all function signatures.
- **Comments:** Add comments to explain the **"why"** of complex logic, not the "what".

### 3.3. Creating New Files

**DO:** Place new files in the correct location according to their responsibility.

- If you create a new, reusable utility (e.g., for security, data transformation, etc.), create a new file for it inside the `src/claude_gemini_mcp/helpers/` directory.
- Update the `helpers/__init__.py` file to expose any new public functions.

---

## 4. Testing & Quality Assurance

**DO:** Ensure all code is thoroughly tested and adheres to quality standards.

- **Testing:** Write comprehensive tests using `pytest` (unit, integration, e2e, security, performance, configuration matrix, stress tests).
- **Code Coverage:** Strive for high code coverage, measured by `pytest-cov`.
- **Linting & Formatting:** Run `black`, `flake8`, `isort`, and `mypy` checks. Ensure code is formatted correctly and passes all linting rules.
- **Security Scanning:** Use `bandit`, `pip-audit`, and `safety` to scan for vulnerabilities.

**DON'T:** Introduce code that reduces test coverage or fails any linting/security checks.

---

## 5. CI/CD & Release Process

**DO:** Leverage the automated CI/CD pipeline for all changes.

- **CI:** Ensure your changes pass all checks in the GitHub Actions `test.yml` workflow (including all test types and quality gates).
- **Release:** Understand that releases are automated via `release-please` based on conventional commits.
- **Dependency Management:** Use `pip` for now, but be aware of `uv` as a faster, more reliable alternative for future consideration.

**DON'T:** Bypass CI checks or manually manage releases.

---

## 6. Security

**DO:** Treat all external input as untrusted.
**DO:** Use the centralized security helper (`src/claude_gemini_mcp/helpers/security.py` - **to be created**) for all input sanitization and path validation.
**DON'T:** Implement your own one-off security or validation checks in other modules.

---

## 7. AI Agent Implementation Guidelines

For detailed technical specifications, coding standards, and architectural patterns for implementing and modifying the AI agent's codebase, please refer to the `PRD/AI_DEVELOPMENT_GUIDELINES.md` file. This document provides comprehensive rules for security, error handling, testing, and more, specifically tailored for developers working on the AI agent's core logic.
