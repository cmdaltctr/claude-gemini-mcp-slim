#!/usr/bin/env python3
"""
Slim Gemini CLI Hook System - Token-Efficient Automation
Optimized for Claude Code token savings with essential analysis only
"""

import os
import subprocess
import sys
from pathlib import Path

# Model configuration with environment variable support
GEMINI_MODELS = {
    "flash": os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash"),
    "pro": os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro"),
}

# Model assignment for hook tasks
HOOK_MODEL_ASSIGNMENTS = {
    "pre-edit": "flash",  # Quick context analysis
    "pre-commit": "pro",  # Thorough review
    "session-summary": "flash",  # Lightweight overview
}

# Configuration

# File analysis configuration optimized for token efficiency
SLIM_CONFIG = {
    "max_file_size": 81920,  # 80 KB
    "max_lines": 800,  # Maximum lines per file
    "response_word_limit": 800,  # Maximum words in response
    "supported_extensions": [
        ".py",
        ".js",
        ".ts",
        ".java",
        ".cpp",
        ".c",
        ".rs",  # Programming languages
        ".vue",
        ".html",
        ".css",
        ".scss",
        ".sass",
        ".jsx",
        ".tsx",  # Frontend files
    ],
}

# File validation


def should_analyze_file(file_path: str) -> tuple[bool, str]:
    """Determine if file should be analyzed based on slim configuration"""

    try:
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            return False, "File not found"

        # Check file extension
        if path.suffix.lower() not in SLIM_CONFIG["supported_extensions"]:
            return False, "File type not supported"

        # Check file size (80KB limit)
        file_size = path.stat().st_size
        if file_size > SLIM_CONFIG["max_file_size"]:
            return False, f"File too large ({file_size} bytes)"

        # Check line count (800 line limit)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                line_count = sum(1 for _ in f)

            if line_count > SLIM_CONFIG["max_lines"]:
                return False, f"Too many lines ({line_count})"
        except Exception:
            # If can't read file, skip analysis
            return False, "Cannot read file"

        return True, "Ready for analysis"

    except Exception as e:
        return False, f"Error: {str(e)}"


# Gemini CLI execution


def execute_gemini_analysis(analysis_type: str, file_paths: str):
    """Execute Gemini CLI analysis with model selection and token-efficient prompts"""

    # Validate and filter file paths
    valid_files = []
    for file_path in file_paths.split():
        should_analyze, reason = should_analyze_file(file_path)
        if should_analyze:
            valid_files.append(file_path)
        else:
            print(f"⚠️ Skipping {file_path}: {reason}", file=sys.stderr)

    if not valid_files:
        print("📝 No valid files to analyze", file=sys.stderr)
        return

    # Select appropriate model
    model_type = HOOK_MODEL_ASSIGNMENTS.get(analysis_type, "flash")
    model_name = GEMINI_MODELS[model_type]
    print(f"🤖 Using {model_name} for {analysis_type}", file=sys.stderr)

    # Create analysis prompt based on type
    if analysis_type == "pre-edit":
        prompt = create_pre_edit_prompt(valid_files)
    elif analysis_type == "pre-commit":
        prompt = create_pre_commit_prompt(valid_files)
    else:
        print(f"❌ Unknown analysis type: {analysis_type}", file=sys.stderr)
        return

    # Execute Gemini CLI with model selection
    try:
        # Use streaming subprocess for real-time output
        process = subprocess.Popen(
            ["gemini", "-m", model_name, "-p", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Stream output and show progress
        output_lines = []
        print(f"🔍 {analysis_type} analysis in progress...", file=sys.stderr)

        while True:
            line = process.stdout.readline()
            if line:
                output_lines.append(line)
                # Show progress to stderr
                print(
                    f"📝 {line.strip()[:80]}{'...' if len(line.strip()) > 80 else ''}",
                    file=sys.stderr,
                )
            elif process.poll() is not None:
                break

        # Get remaining output
        remaining_stdout, stderr = process.communicate()
        if remaining_stdout:
            output_lines.append(remaining_stdout)

        # Create result object to match original interface
        result = subprocess.CompletedProcess(
            args=["gemini", "-p", prompt],
            returncode=process.returncode,
            stdout="".join(output_lines),
            stderr=stderr,
        )

        if result.returncode == 0:
            print(f"✅ {analysis_type} analysis complete", file=sys.stderr)
            print(result.stdout)
        else:
            print(f"⚠️ Analysis failed: {result.stderr}", file=sys.stderr)

    # No timeout handling needed with streaming
    except FileNotFoundError:
        print(
            "❌ Gemini CLI not found. Run 'npm install -g @google/gemini-cli'",
            file=sys.stderr,
        )
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)


def execute_session_summary(directory_path: str):
    """Execute lightweight session summary analysis"""

    print("📋 Generating session summary...", file=sys.stderr)

    # Select model for session summary
    model_type = HOOK_MODEL_ASSIGNMENTS.get("session-summary", "flash")
    model_name = GEMINI_MODELS[model_type]
    print(f"🤖 Using {model_name} for session summary", file=sys.stderr)

    prompt = create_session_summary_prompt(directory_path)

    try:
        # Use streaming subprocess for session summary
        process = subprocess.Popen(
            ["gemini", "-m", model_name, "-p", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Stream output
        output_lines = []

        while True:
            line = process.stdout.readline()
            if line:
                output_lines.append(line)
            elif process.poll() is not None:
                break

        # Get remaining output
        remaining_stdout, stderr = process.communicate()
        if remaining_stdout:
            output_lines.append(remaining_stdout)

        # Create result object
        result = subprocess.CompletedProcess(
            args=["gemini", "-p", prompt],
            returncode=process.returncode,
            stdout="".join(output_lines),
            stderr=stderr,
        )

        if result.returncode == 0:
            print("✅ Session summary complete", file=sys.stderr)
            print("\n" + "=" * 50, file=sys.stderr)
            print("📋 SESSION SUMMARY", file=sys.stderr)
            print("=" * 50, file=sys.stderr)
            print(result.stdout)
            print("=" * 50, file=sys.stderr)
        else:
            print("⚠️ Session summary failed", file=sys.stderr)

    # No timeout handling needed
    except Exception as e:
        print(f"❌ Session summary error: {e}", file=sys.stderr)


# Prompt generation


def create_pre_edit_prompt(file_paths: list) -> str:
    """Create token-efficient pre-edit analysis prompt"""
    files_list = ", ".join(file_paths)

    return f"""Perform comprehensive pre-edit analysis of these files: {files_list}

Provide detailed analysis including:
1. Critical bugs or security vulnerabilities
2. Performance bottlenecks and optimization opportunities
3. Architecture concerns and design patterns
4. Code quality and maintainability issues
5. Error handling and edge cases
6. Best practices compliance
7. Specific improvement recommendations

Focus on actionable insights that will help make better edits on first attempt."""


def create_pre_commit_prompt(file_paths: list) -> str:
    """Create focused pre-commit review prompt"""
    files_list = ", ".join(file_paths)

    return f"""Comprehensive pre-commit review of these files: {files_list}

Perform thorough analysis including:
1. Critical bugs that would break functionality
2. Security vulnerabilities and potential exploits
3. Breaking changes or API compatibility issues
4. Code quality and maintainability concerns
5. Performance regressions or inefficiencies
6. Test coverage and validation gaps
7. Documentation and code clarity issues

Focus on issues that should block this commit. Be thorough and detailed."""


def create_session_summary_prompt(directory_path: str) -> str:
    """Create lightweight session summary prompt"""
    return "What can you see in this current directory? List the main files and give a brief project overview in under 200 words in plain text format."


# Main execution


def main():
    """Main entry point for hook execution"""
    if len(sys.argv) != 3:
        print(
            "Usage: slim_gemini_hook.py <analysis_type> <file_paths>", file=sys.stderr
        )
        sys.exit(1)

    analysis_type = sys.argv[1]
    file_paths = sys.argv[2]

    # Execute analysis based on type
    if analysis_type == "session-summary":
        execute_session_summary(file_paths)
    else:
        execute_gemini_analysis(analysis_type, file_paths)


if __name__ == "__main__":
    main()
