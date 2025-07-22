# Claude <-> Gemini MCP: Product Requirements Document v3

**Document Version:** 3.0
**Status:** Active
**Owner:** Development Team

---

## 1. Overview

### 1.1. Mission & Vision

*   **Mission:** To democratize access to multiple AI models within development workflows, enabling developers to leverage the best capabilities of both Claude and Gemini AI systems seamlessly.
*   **Vision:** To be the de facto standard for multi-AI integration in development environments, providing a secure, reliable, and token-efficient protocol for true collaboration between AI agents.

### 1.2. Core Concept: An Intelligent Agent, Not a Simple Bridge

This project is a Model Context Protocol (MCP) server that acts as an **intelligent agent**, not just a simple bridge. While a basic bridge would merely pass requests and raw text between a client and the AI, this server adds significant value by orchestrating the entire interaction.

Think of the MCP server as a skilled project manager:
1.  **Perception:** It receives a high-level task from a client (e.g., `gemini_analyze_code`).
2.  **Reasoning:** It uses its configuration to select the best AI model for the job (`flash` vs. `pro`).
3.  **Orchestration:** It constructs a detailed, specific prompt for the Gemini backend, requesting a structured JSON response (`AgenticCodePatch`).
4.  **Transformation:** It processes the structured JSON from Gemini and transforms it into a human-readable, actionable suggestion (e.g., a `diff` view).
5.  **Action:** It sends this final, polished message back to the client using the MCP standard.

This agentic approach is a powerful and modern architectural pattern. The project is currently evolving from a simple text-based agent to a more advanced one that leverages structured data via the **Agentic Collaboration Protocol (ACP)**.

## 2. System Architecture & Technology

### 2.1. High-Level Architecture

The system is composed of a central Python-based MCP server that communicates with a Claude client and orchestrates calls to the Google Gemini backend.

```
    Claude Client (e.g., Claude Code)      
                    │
                    ▼
      ┌─────────────────────────┐
      │     MCP Protocol        │
      │   (Tool Requests)       │
      └─────────────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │  Gemini MCP     │
          │    Server       │
          │ (Python/AsyncIO)│
          └─────────────────┘
                    │
      ┌─────────────┴─────────────┐
      ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│  Gemini API     │         │  Gemini CLI     │
│  (Primary)      │         │  (Fallback)     │
└─────────────────┘         └─────────────────┘
```

### 2.2. Data Flow Evolution

*   **Phase 1 (Completed):** A simple request-response cycle where the server receives a natural language prompt and returns a plain text response from the Gemini CLI/API.
*   **Phase 2 (Next Steps):** An agentic flow where the server receives a prompt, asks the Gemini API for a structured `AgenticCodePatch` JSON object, and then formats that object into a clear, actionable suggestion for the user.

### 2.3. Integration & Compatibility

*   **Protocol-Centric Design:** The server is fundamentally client-agnostic. Any tool or application capable of communicating via the Model Context Protocol (MCP) can connect to and utilize this server.
*   **Architectural Gist:** The client's role is simple: send a standard MCP tool request. The MCP server does the heavy lifting: it orchestrates the call to the Gemini backend, gets a structured JSON response, and formats it into a human-readable markdown message that any client can display.
*   **Broad Applicability:** This includes, but is not limited to:
    *   **Full-Featured IDEs:** Claude Code, Cursor, VS Code extensions.
    *   **Modern Terminals:** Warp and other terminals that can render markdown.
    *   **Standard CLIs:** Any command-line tool can interact with the server, receiving well-formatted, human-readable text responses.

### 2.4. User Stories

| User Persona | Goal / "I want to..." | Motivation / "So that I can..." |
| :--- | :--- | :--- |
| **Developer (IDE)** | ...ask for a security review of my current file... | ...get immediate, actionable feedback on vulnerabilities without leaving my editor. |
| **Developer (Terminal)** | ...pipe a file into the `gemini_analyze_code` tool... | ...quickly assess code quality from the command line in my Warp terminal. |
| **DevOps Engineer** | ...integrate `gemini_codebase_analysis` into a CI/CD pipeline... | ...automatically fail a build if the code introduces critical security risks or architectural debt. |
| **AI Agent Developer** | ...programmatically send code snippets to the server... | ...use the structured JSON response to make automated refactoring decisions in my own agent. |
| **Security Engineer** | ...run a full `security` scope analysis on an entire repository... | ...generate a comprehensive audit report of all potential vulnerabilities in the codebase. |
| **Technical Lead** | ...use the `architecture` analysis on a pull request... | ...ensure that new contributions adhere to our established design patterns. |

### 2.5. Technology Stack

*   **Language:** Python 3.10+
*   **Core Libraries:**
    *   `mcp.py`: For MCP server implementation.
    *   `google-generativeai`: For primary interaction with the Gemini API.
    *   `instructor`: **(To be added)** For enforcing structured JSON responses from Gemini.
    *   `pydantic`: For defining the structured data schemas (e.g., `AgenticCodePatch`).
*   **Protocol:** Model Context Protocol (MCP)

### 2.4. User-Driven Configuration

*   **Principle:** The system's core behavior must be configurable by the end-user without requiring code changes. This ensures flexibility and adaptability to different user needs and environments.
*   **Implementation:** The `config.py` module provides a hierarchical configuration system with a clear load precedence:
    1.  Explicit function arguments (highest priority)
    2.  Environment variables
    3.  User-defined `config.json` file
    4.  Hard-coded defaults (lowest priority)
*   **Application:** This pattern allows users to customize model assignments, API keys, timeouts, and feature flags by placing a `config.json` file in their project root. This avoids hard-coded values and empowers users to tailor the MCP's operation to their specific needs.

## 3. Coding Standards & Architectural Patterns

To ensure the codebase remains modular, maintainable, and easy to understand, all contributions should adhere to the following principles.

### 3.1. Modularity and The Role of Helpers

*   **Principle:** Each module has one clear responsibility, creating a decoupled and maintainable system.
*   **Core Modules:**
    *   `gemini_mcp_server.py`: **The Communicator.** Responsible only for handling MCP communication (requests/responses) and managing the overall workflow.
    *   `gemini_helper.py`: **The AI Specialist.** Responsible only for interacting with the Gemini backend. It constructs prompts, parses the AI's response, and handles the API/CLI fallback logic.
    *   `config.py`: **The Rulebook.** The single source of truth for all configuration.
*   **Orchestration Helpers (`src/claude_gemini_mcp/helpers/`):** The server's "Orchestration" is powered by this dedicated directory of utilities. These helpers are not simple functions; they are specialized engines for pre-processing data and post-processing results.
    *   `codebase_analyzer.py` / `analyze_code.py`: **Pre-Processing Engines.** These perform static analysis on the user's code *before* it is sent to the AI, structuring it for optimal results.
    *   `markdown_utils.py`: **Post-Processing Formatter.** This cleans and standardizes the AI's markdown response for consistent display across any client.
    *   `hybrid_progress.py`: **UX Utility.** This provides real-time progress indicators to the user during long-running tasks.
*   **Suggestion for Improvement:**
    *   **New Helper (`security.py`):** To adhere to the Single Responsibility Principle, the `sanitize_for_prompt` and `validate_path_security` functions should be extracted from the server and helper modules into a dedicated `src/claude_gemini_mcp/helpers/security.py` module.

### 3.2. Project Structure Diagram

This diagram illustrates the flow of control and separation of concerns:

```
[MCP Client] <--+--> [gemini_mcp_server.py] --(manages)--> [gemini_helper.py] <--+--> [Gemini Backend]
     ^           (MCP Comms)       |                      (AI Comms)        (API/CLI)
     |
     +--(formats & displays)---- [AgenticCodePatch] <----(parses)----+
                                       ^
                                       |
     +---------------------------------+
     |
     +---(calls helpers for)--> [src/claude_gemini_mcp/helpers/]
                                     |--> codebase_analyzer.py (Pre-Processing)
                                     |--> markdown_utils.py (Post-Processing)
                                     |--> security.py (Validation - To Be Created)
                                     |--> hybrid_progress.py (UX)
```

### 3.3. Clarity Over Complexity

*   **Principle:** Avoid deep nesting and overly complex functions. Favor readability and simplicity.
*   **Application:**
    *   Functions should ideally be less than 50 lines.
    *   Complex logic within a function (e.g., the streaming and process handling in `execute_gemini_cli_streaming`) should be broken down into smaller, private helper functions with clear names (e.g., `_stream_process_output`, `_validate_prompt_input`).
    *   Avoid more than 2-3 levels of nested `if/try/for` blocks within a single function.

### 3.3. Configuration Management

*   **Pattern:** The existing `config.py` uses a robust singleton pattern with clear load precedence. This is the standard and should be used for all new configuration needs.
*   **Application:** Never access `os.getenv` or read config files outside of `config.py`. Use the provided accessor functions like `cfg.get_model()` and `cfg.get_limit()`.

### 3.4. Docstrings & Type Hinting

*   **Standard:** All public functions, methods, and classes **must** have a docstring explaining their purpose, arguments, and return values, following a format similar to Google's Python Style Guide.
*   **Application:**
    *   Use type hints for all function arguments and return values (`def my_function(name: str) -> bool:`).
    *   Docstrings should be clear enough to serve as a reference for other developers and AI agents.

### 3.5. Code Comments

*   **Principle:** Write comments to explain the *why*, not the *what*. Code should be self-documenting where possible.
*   **Application:**
    *   Add comments for complex logic, business rules, or workarounds for external system quirks.
    *   Avoid obvious comments (e.g., `# increment counter`).
    *   Use `# TODO:` or `# FIXME:` prefixes to mark areas that require future attention.

### 3.6. Testing & Quality Assurance

*   **Testing Frameworks:** `pytest` is the primary testing framework, augmented by:
    *   `pytest-asyncio`: For asynchronous code testing.
    *   `pytest-cov`: For code coverage reporting.
    *   `pytest-mock`: For mocking objects in tests.
    *   `pytest-xdist`: For parallel test execution.
    *   `pytest-timeout`: For enforcing test timeouts.
    *   `pytest-benchmark`: For performance testing.
*   **Test Types:** The project employs a comprehensive testing strategy, including:
    *   **Unit Tests:** Isolated testing of individual components.
    *   **Integration Tests:** Verification of interactions between components.
    *   **End-to-End (E2E) Tests:** Full system flow validation.
    *   **Security Tests:** Focused tests for common vulnerabilities.
    *   **Performance Tests:** Benchmarking and performance regression detection.
    *   **Configuration Matrix Tests:** Ensuring robust behavior across various configurations.
    *   **Stress Tests:** Validating system stability under load.
*   **Code Coverage:** Code coverage is measured using `pytest-cov` and reported to Codecov. A minimum of 70% coverage is required.
*   **Linting & Formatting:**
    *   `black`: Automated code formatter to ensure consistent style.
    *   `flake8`: Linter for enforcing PEP 8 and detecting common code issues.
    *   `isort`: For consistent import sorting.
    *   `mypy`: Static type checker for Python code.
*   **Security Scanning:**
    *   `bandit`: Static analysis security linter.
    *   `pip-audit`: For auditing Python dependencies for known vulnerabilities.
    *   `safety`: Another tool for checking installed dependencies for security vulnerabilities.

### 3.7. CI/CD & Release Process

*   **Continuous Integration (CI):** All code changes are validated via GitHub Actions (`.github/workflows/test.yml`). This workflow runs all defined test suites (unit, integration, e2e, security, performance, quality) across multiple Python versions (3.10, 3.11, 3.12).
*   **Continuous Delivery (CD) & Release Automation:**
    *   `release-please`: Automates versioning, generates changelogs, and creates GitHub Releases based on conventional commits (`.github/workflows/release.yml`).
    *   `twine` & `build`: Used for building and publishing Python packages to PyPI.
*   **Dependency Management Recommendation (`uv`):**
    *   Currently, `pip` is used for dependency installation. However, `uv` is a modern, significantly faster Python package installer and resolver written in Rust.
    *   **Recommendation:** Future evaluation and potential adoption of `uv` is highly recommended for improved development workflow speed and reliability. It can serve as a drop-in replacement for `pip` and `pip-tools`.

## 4. Functional Requirements & Roadmap

### Phase 1: Foundational MCP Server (Completed)

-   ✅ **FR-001: Core MCP Server:** A fully functional server implementing the MCP specification.
-   ✅ **FR-002: Core Tools:** Provided `gemini_quick_query`, `gemini_analyze_code`, and `gemini_codebase_analysis` tools that return plain text.
-   ✅ **FR-003: Smart Model Selection:** Intelligent model routing (`flash` vs. `pro`) with API/CLI fallback.
-   ✅ **FR-004: Security:** Robust input sanitization and path traversal protection.
-   ✅ **FR-005: Configuration:** Centralized, thread-safe configuration management.

### Phase 2: Agentic Collaboration (Next Steps)

-   🟡 **FR-006: Structured AI Data Exchange (ACP):** This is the highest priority. The goal is to upgrade the `gemini_analyze_code` tool to return structured JSON instead of text.
    *   **Acceptance Criteria:**
        1.  The `instructor` library is added to `requirements.txt`.
        2.  A Pydantic `AgenticCodePatch` model is defined in `gemini_helper.py`.
        3.  `gemini_analyze_code` is refactored to use `instructor` and return an `AgenticCodePatch` object.
        4.  The MCP server is updated to receive this object and format it into a human-readable suggestion with a `diff` view.

### Phase 3: Proactive Intelligence (Future)

-   🔄 **FR-007: Proactive Feedback Loop:** Implement a mechanism for Gemini to asynchronously analyze code changes and offer unsolicited, non-intrusive feedback to the user.

## 5. Non-Functional Requirements

*   **Performance:** 95% of quick queries should complete within 10 seconds. Complex analysis should show streaming progress and complete within 120 seconds.
*   **Reliability:** 99.9% availability. Graceful degradation from API to CLI fallback.
*   **Security:** No sensitive data logging. Adherence to OWASP secure coding practices. All inputs must be sanitized and all file paths validated.
*   **Maintainability:** A minimum of 70% unit test coverage. All new features must include corresponding tests.

## 6. Success Metrics

| Category | Metric | Target | Status |
| :--- | :--- | :--- | :--- |
| **Adoption** | Installation Success Rate | > 95% | Tracking |
| | Daily Active Users | Increase 10% QoQ | Tracking |
| **Performance** | P95 Response Time (Quick Query) | < 10s | Tracking |
| | Error Rate (All Tools) | < 2% | Tracking |
| **Quality** | User Satisfaction (NPS) | > 50 | To Be Implemented |
| | Code Coverage | > 70% | Tracking |
| **Agentic** | Structured Output Reliability | > 99.5% | To Be Implemented |
| | User Action Rate on Suggestions | > 30% | To Be Implemented |

## 7. Appendices

### Appendix A: `AgenticCodePatch` Schema

This Pydantic model will be implemented in `gemini_helper.py` to define the structure of agentic responses.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class AgenticCodePatch(BaseModel):
    action_type: Literal['REPLACE', 'INSERT', 'NOTIFY'] = Field(
        ..., description="The type of action to be performed."
    )
    file_path: str = Field(
        ..., description="The full path to the file that should be modified."
    )
    start_line: Optional[int] = Field(
        None, description="The starting line number for the code modification."
    )
    end_line: Optional[int] = Field(
        None, description="The ending line number for the code modification."
    )
    new_code: Optional[str] = Field(
        None, description="The new code to be inserted or used for replacement."
    )
    explanation: str = Field(
        ..., description="A brief, human-readable explanation of the suggested change."
    )
```
