#!/usr/bin/env python3
"""
Slim Gemini CLI Hook System - Token-Efficient Automation
Optimized for Claude Code token savings with essential analysis only
"""

import os
import sys
import subprocess
from pathlib import Path

##################################################################
#################### CONFIGURATION ##############################
##################################################################

# File analysis configuration optimized for token efficiency
SLIM_CONFIG = {
    "max_file_size": 81920,     # 80 KB
    "max_lines": 800,           # Maximum lines per file
    "response_word_limit": 800, # Maximum words in response
    "supported_extensions": [
        ".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs",  # Programming languages
        ".vue", ".html", ".css", ".scss", ".sass", ".jsx", ".tsx"  # Frontend files
    ]
}

##################################################################
#################### FILE VALIDATION ############################
##################################################################

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
            with open(file_path, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)

            if line_count > SLIM_CONFIG["max_lines"]:
                return False, f"Too many lines ({line_count})"
        except:
            # If can't read file, skip analysis
            return False, "Cannot read file"

        return True, "Ready for analysis"

    except Exception as e:
        return False, f"Error: {str(e)}"

##################################################################
#################### GEMINI CLI EXECUTION #######################
##################################################################

def execute_gemini_analysis(analysis_type: str, file_paths: str):
    """Execute Gemini CLI analysis with token-efficient prompts"""

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

    # Create analysis prompt based on type
    if analysis_type == "pre-edit":
        prompt = create_pre_edit_prompt(valid_files)
    elif analysis_type == "pre-commit":
        prompt = create_pre_commit_prompt(valid_files)
    else:
        print(f"❌ Unknown analysis type: {analysis_type}", file=sys.stderr)
        return

    # Execute Gemini CLI
    try:
        result = subprocess.run(
            ["gemini", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"✅ {analysis_type} analysis complete", file=sys.stderr)
            print(result.stdout)
        else:
            print(f"⚠️ Analysis failed: {result.stderr}", file=sys.stderr)

    except subprocess.TimeoutExpired:
        print("⏰ Analysis timed out", file=sys.stderr)
    except FileNotFoundError:
        print("❌ Gemini CLI not found. Run 'npm install -g @google/gemini-cli'", file=sys.stderr)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)

def execute_session_summary(directory_path: str):
    """Execute lightweight session summary analysis"""

    print("📋 Generating session summary...", file=sys.stderr)

    prompt = create_session_summary_prompt(directory_path)

    try:
        result = subprocess.run(
            ["gemini", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=30  # Short timeout for quick summary
        )

        if result.returncode == 0:
            print("✅ Session summary complete", file=sys.stderr)
            print("\n" + "="*50, file=sys.stderr)
            print("📋 SESSION SUMMARY", file=sys.stderr)
            print("="*50, file=sys.stderr)
            print(result.stdout)
            print("="*50, file=sys.stderr)
        else:
            print("⚠️ Session summary failed", file=sys.stderr)

    except subprocess.TimeoutExpired:
        print("⏰ Session summary timed out", file=sys.stderr)
    except Exception as e:
        print(f"❌ Session summary error: {e}", file=sys.stderr)

##################################################################
#################### PROMPT GENERATION ##########################
##################################################################

def create_pre_edit_prompt(file_paths: list) -> str:
    """Create token-efficient pre-edit analysis prompt"""
    files_ref = " ".join([f"@{fp}" for fp in file_paths])

    return f"""{files_ref}

        Quick pre-edit analysis (under {SLIM_CONFIG["response_word_limit"]} words):

1. Critical bugs or security issues
2. Performance bottlenecks
3. Architecture concerns
4. Key improvement opportunities

        Focus on actionable insights that will help make better edits on first attempt."""

def create_pre_commit_prompt(file_paths: list) -> str:
    """Create focused pre-commit review prompt"""
    files_ref = " ".join([f"@{fp}" for fp in file_paths])

    return f"""{files_ref}

        Pre-commit review (under {SLIM_CONFIG["response_word_limit"]} words):

1. Critical bugs that would break functionality
2. Security vulnerabilities
3. Breaking changes or API issues
4. Code quality concerns

        Focus on issues that should block this commit."""

def create_session_summary_prompt(directory_path: str) -> str:
    """Create lightweight session summary prompt"""
    return f"""@{directory_path}

Brief session summary (under 200 words):

1. Key files modified during this session
2. Main changes or improvements made
3. Quick health check - any obvious issues
4. Suggested next steps or follow-ups

        Focus on actionable insights and session recap only."""

##################################################################
#################### MAIN EXECUTION #############################
##################################################################

def main():
    """Main entry point for hook execution"""
    if len(sys.argv) != 3:
        print("Usage: slim_gemini_hook.py <analysis_type> <file_paths>", file=sys.stderr)
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
    