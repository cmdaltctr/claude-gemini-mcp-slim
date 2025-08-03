#!/usr/bin/env python3
"""
Gemini CLI Helper - Main public interface
Usage: python gemini_helper.py [command] [args]
"""

import asyncio
import json
import sys
import time
from pathlib import Path

from claude_gemini_mcp.config import get_config
from claude_gemini_mcp.helpers.execution_orchestrator import execute_gemini_smart
from claude_gemini_mcp.helpers.security import (
    sanitize_for_prompt,
    validate_file_security,
)

# Import availability flags for codebase analysis
try:
    from claude_gemini_mcp.helpers.tools.codebase_analyzer import (
        analyze_codebase as real_analyze_codebase,
    )

    CODEBASE_ANALYZER_AVAILABLE = True
except ImportError:
    CODEBASE_ANALYZER_AVAILABLE = False

# Configuration
cfg = get_config()
MAX_FILE_SIZE = cfg.get_limit("max_file_size", 81920)  # 80KB default
MAX_LINES = cfg.get_limit("max_lines", 800)  # 800 lines default
CLI_TIMEOUT = cfg.get_timeout("cli_timeout", 60)  # 60 seconds default


def quick_query(query: str, context: str = "") -> None:
    """Ask Gemini CLI a quick question"""
    start_time = time.time()

    # Sanitize inputs to prevent prompt injection
    sanitized_query = sanitize_for_prompt(
        query, max_length=cfg.get_limit("max_prompt_size", 10000) // cfg.get_limit("sanitization_query_divisor", 100)
    )
    sanitized_context = sanitize_for_prompt(
        context, max_length=cfg.get_limit("max_prompt_size", 50000) // cfg.get_limit("sanitization_context_divisor", 20)
    )

    if sanitized_context:
        prompt = f"Context: {sanitized_context}\n\nQuestion: {sanitized_query}\n\nProvide a concise answer."
    else:
        prompt = f"Question: {sanitized_query}\n\nProvide a concise answer."

    result = asyncio.run(execute_gemini_smart(prompt, "quick_query"))

    elapsed_time = time.time() - start_time

    if result["success"]:
        print(f"\nQuery: {query}")
        print("=" * 50)
        print()
        print(result["output"])
        print()
        print("=" * 50)
        print(f"✅ Request completed ({elapsed_time:.1f}s)")
    else:
        print(f"Error: {result['error']}")


def analyze_code(file_path: str, analysis_type: str = "comprehensive") -> None:
    """Analyze a code file"""
    try:
        # Input validation
        if not isinstance(file_path, str) or not file_path.strip():
            print("Error: Invalid file path")
            return
        if not isinstance(analysis_type, str) or analysis_type not in [
            "comprehensive",
            "security",
            "performance",
            "architecture",
        ]:
            print("Error: Invalid analysis type")
            return

        # Enhanced security validation using new function
        is_valid, error_message, resolved_path = validate_file_security(file_path)
        if not is_valid or resolved_path is None:
            print(f"Error: {error_message}")
            return
        file_path = str(resolved_path)  # Use the resolved, validated path

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if len(content) > MAX_FILE_SIZE:
            print(
                f"Warning: File too large ({len(content)} bytes). Truncating to {MAX_FILE_SIZE} bytes..."
            )
            content = content[:MAX_FILE_SIZE]

        line_count = len(content.splitlines())
        if line_count > MAX_LINES:
            print(
                f"Warning: Too many lines ({line_count}). Truncating to {MAX_LINES} lines..."
            )
            lines = content.splitlines()[:MAX_LINES]
            content = "\n".join(lines)

        # Sanitize inputs to prevent prompt injection
        sanitized_content = sanitize_for_prompt(content, max_length=MAX_FILE_SIZE)
        # analysis_type is already validated above

        prompt = f"""Perform a {analysis_type} analysis of this code:\n\n{sanitized_content}\n\nProvide comprehensive analysis including:\n1. Code structure and organization\n2. Logic flow and algorithm efficiency\n3. Security considerations and vulnerabilities\n4. Performance implications and optimizations\n5. Error handling and edge cases\n6. Code quality and maintainability\n7. Best practices compliance\n8. Specific recommendations for improvements\n\nBe thorough and provide actionable insights."""

        result = asyncio.run(execute_gemini_smart(prompt, "analyze_code"))

        if result["success"]:
            print(f"\nCode Analysis: {file_path}")
            print(f"Type: {analysis_type}")
            print(f"Lines: {line_count}")
            print("=" * 50)
            print()
            print(result["output"])
            print()
            print("=" * 50)
            print("✅ Request completed")
        else:
            print(f"Error: {result['error']}")

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"Error: {str(e)}")


def analyze_codebase(directory_path: str, analysis_scope: str = "all") -> None:
    """Analyze entire codebase - thin wrapper that calls real analyzer and feeds to Gemini"""
    start_time = time.time()

    # Input validation
    if not isinstance(directory_path, str) or not directory_path.strip():
        print("Error: Invalid directory path")
        return
    if not isinstance(analysis_scope, str) or analysis_scope not in [
        "structure",
        "security",
        "performance",
        "patterns",
        "all",
    ]:
        print("Error: Invalid analysis scope")
        return

    # Path security validation
    try:
        resolved_path = Path(directory_path).resolve()
        current_dir = Path.cwd().resolve()
        # Check if the resolved path is within current directory tree (prevent path traversal)
        try:
            resolved_path.relative_to(current_dir)
        except ValueError:
            print(
                f"Error: Directory access denied - path outside allowed directory: {directory_path}"
            )
            return
        if not resolved_path.exists():
            print(f"Error: Directory not found: {directory_path}")
            return
        if not resolved_path.is_dir():
            print(f"Error: Path is not a directory: {directory_path}")
            return
    except Exception as e:
        print(f"Error: Path validation failed: {str(e)}")
        return

    # Check if codebase analyzer is available
    if not CODEBASE_ANALYZER_AVAILABLE:
        print(
            "Error: Codebase analyzer not available. Please ensure helpers/codebase_analyzer.py is accessible."
        )
        return

    try:
        print(
            f"🔍 Starting comprehensive codebase analysis for: {directory_path}",
            file=sys.stderr,
        )
        print(f"📋 Analysis scope: {analysis_scope}", file=sys.stderr)
        print(
            "⏳ Step 1/3: Analyzing project structure and content...", file=sys.stderr
        )

        # Step 1: Call the real analyze_codebase function
        analysis_result = real_analyze_codebase(
            str(resolved_path), max_total_size=cfg.get_limit("max_codebase_analysis_size", 300000)
        )

        if analysis_result.error:
            print(f"Error during codebase analysis: {analysis_result.error}")
            return

        # Extract key information
        prompt_payload = analysis_result.prompt_payload
        project_report = analysis_result.project_report

        if not prompt_payload:
            print("Error: No content generated from codebase analysis")
            return

        print(
            f"✅ Step 1 complete: Analyzed {analysis_result.stats.files_analyzed} files",
            file=sys.stderr,
        )
        print(
            f"📊 Generated {len(prompt_payload):,} characters of structured content",
            file=sys.stderr,
        )
        print(
            f"⏱️ Analysis took {analysis_result.stats.total_time:.2f}s", file=sys.stderr
        )
        print("⏳ Step 2/3: Feeding to Gemini for AI analysis...", file=sys.stderr)

        # Step 2: Create analysis prompt based on scope
        analysis_prompt = f"""You are a senior software architect and code reviewer. Analyze this codebase comprehensively.\n\n{prompt_payload}\n\n## Analysis Requirements\n\nBased on the scope '{analysis_scope}', provide detailed analysis covering:\n\n1. **Architecture & Design Patterns**: Overall system design, patterns used, architectural decisions\n2. **Code Quality & Maintainability**: Code organization, readability, documentation quality\n3. **Security Analysis**: Potential vulnerabilities, security best practices, risk assessment\n4. **Performance Considerations**: Bottlenecks, optimization opportunities, scalability issues\n5. **Best Practices Compliance**: Following language/framework conventions, industry standards\n6. **Dependencies & Integration**: External dependencies, integration points, potential risks\n7. **Testing & Quality Assurance**: Test coverage, testing strategies, quality metrics\n8. **Documentation & Developer Experience**: Code clarity, documentation completeness, onboarding ease\n\n## Output Format\n\nProvide a comprehensive report with:\n- **Executive Summary**: Key findings and overall assessment\n- **Detailed Analysis**: In-depth analysis for each area above\n- **Actionable Recommendations**: Specific, prioritized improvement suggestions\n- **Risk Assessment**: Potential issues and their impact levels\n- **Implementation Roadmap**: Step-by-step improvement plan\n\nBe thorough, specific, and provide actionable insights."""

        # Step 3: Feed to Gemini and stream results
        result = asyncio.run(execute_gemini_smart(analysis_prompt, "analyze_codebase"))

        elapsed_time = time.time() - start_time

        if result["success"]:
            print("\n" + "=" * 80)
            print(f"🏗️ CODEBASE ANALYSIS REPORT: {resolved_path.name}")
            print(f"📋 Scope: {analysis_scope.upper()}")
            print(f"📊 Files Analyzed: {analysis_result.stats.files_analyzed}")
            print(f"📈 Total Lines: {analysis_result.structure.total_lines:,}")
            if analysis_result.structure.languages:
                primary_lang = max(
                    analysis_result.structure.languages.items(), key=lambda x: x[1]
                )[0]
                print(f"🔤 Primary Language: {primary_lang.title()}")
            print(f"⏱️ Analysis Time: {elapsed_time:.1f}s")
            print("=" * 80)
            print()

            # Step 3: Stream the Gemini analysis result
            print("✅ Step 3/3: AI Analysis Complete!\n", file=sys.stderr)
            print(result["output"])
            print()
            print("=" * 80)
            print(f"✅ Comprehensive analysis completed in {elapsed_time:.1f}s")
            print(
                f"📋 Report generated from {len(prompt_payload):,} characters of codebase content"
            )
            print("=" * 80)
        else:
            print(f"\nError during AI analysis: {result['error']}")
            print("\n" + "=" * 50)
            print("📋 RAW CODEBASE ANALYSIS (Fallback)")
            print("=" * 50)
            print()
            # Fallback: show the project report if Gemini fails
            if project_report:
                print(json.dumps(project_report, indent=2))
            print()
            print("=" * 50)

    except Exception as e:
        print(f"Error during codebase analysis: {str(e)}")
        print(f"Details: {type(e).__name__}: {str(e)}", file=sys.stderr)


def main() -> None:
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python gemini_helper.py query 'your question here' [context]")
        print("  python gemini_helper.py analyze file_path [analysis_type]")
        print("  python gemini_helper.py codebase directory_path [scope]")
        return

    command = sys.argv[1].lower()

    if command == "query":
        if len(sys.argv) < 3:
            print("Error: Query text required")
            return
        query_text = sys.argv[2]
        context = sys.argv[3] if len(sys.argv) > 3 else ""
        quick_query(query_text, context)

    elif command == "analyze":
        if len(sys.argv) < 3:
            print("Error: File path required")
            return
        file_path = sys.argv[2]
        analysis_type = sys.argv[3] if len(sys.argv) > 3 else "comprehensive"
        analyze_code(file_path, analysis_type)

    elif command == "codebase":
        if len(sys.argv) < 3:
            print("Error: Directory path required")
            return
        directory_path = sys.argv[2]
        scope = sys.argv[3] if len(sys.argv) > 3 else "all"
        analyze_codebase(directory_path, scope)

    else:
        print(f"Unknown command: {command}")
        print("Available commands: query, analyze, codebase")


if __name__ == "__main__":
    main()
