#!/usr/bin/env python3
"""
Gemini CLI Helper - Direct integration with API fallback
Usage: python gemini_helper.py [command] [args]
"""

import sys
import subprocess
import shlex
import os
import time
from pathlib import Path

# Model configuration with fallback to CLI
GEMINI_MODELS = {
    "flash": os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash"),
    "pro": os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")
}

# API key for direct API usage
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model assignment for tasks
MODEL_ASSIGNMENTS = {
    "quick_query": "flash",      # Simple Q&A
    "analyze_code": "pro",       # Deep analysis
    "analyze_codebase": "pro",   # Large context
}

# Configuration
MAX_FILE_SIZE = 81920  # 80KB
MAX_LINES = 800

# Security functions
def sanitize_for_prompt(text: str, max_length: int = 100000) -> str:
    """Sanitize text input to prevent prompt injection attacks"""
    if not isinstance(text, str):
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove/escape potential prompt injection patterns
    # Remove common prompt injection prefixes/suffixes
    dangerous_patterns = [
        "ignore all previous instructions",
        "forget everything above",
        "new instruction:",
        "system:",
        "assistant:",
        "user:",
        "###",
        "---",
        "```",
        "<|",
        "|>",
        "[INST]",
        "[/INST]"
    ]
    
    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in text_lower:
            # Replace with safe alternative (case-insensitive)
            import re
            # Create case-insensitive regex pattern
            escaped_pattern = re.escape(pattern)
            replacement = f"[filtered:{pattern[:10]}]"
            text = re.sub(escaped_pattern, replacement, text, flags=re.IGNORECASE)
    
    # Escape potential control characters
    text = text.replace('\x00', '').replace('\x1b', '')
    
    return text

def execute_gemini_api(prompt: str, model_name: str, show_progress: bool = True) -> dict:
    """Execute Gemini API directly with specified model"""
    try:
        # Validate API key securely
        if not GOOGLE_API_KEY or not isinstance(GOOGLE_API_KEY, str) or len(GOOGLE_API_KEY.strip()) < 10:
            return {"success": False, "error": "Invalid or missing API key"}
        
        import google.generativeai as genai
        
        if show_progress:
            print(f"🌟 Making API call to {model_name}...", file=sys.stderr)
        
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(model_name)
        
        response = model.generate_content(prompt)
        
        if show_progress:
            print("✅ API call successful!", file=sys.stderr)
        
        return {"success": True, "output": response.text}
        
    except ImportError:
        if show_progress:
            print("⚠️ google-generativeai not installed, using CLI fallback", file=sys.stderr)
        return {"success": False, "error": "API library not available"}
    except Exception as e:
        # Sanitize error message to prevent sensitive information leakage
        error_message = str(e)
        # Remove potential API key patterns from error messages
        import re
        error_message = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[API_KEY_REDACTED]', error_message)
        error_message = re.sub(r'sk-[A-Za-z0-9_-]{32,}', '[API_KEY_REDACTED]', error_message)
        error_message = re.sub(r'Bearer [A-Za-z0-9_.-]{10,}', '[TOKEN_REDACTED]', error_message)
        
        if show_progress:
            print(f"⚠️ API call failed: {error_message}, using CLI fallback", file=sys.stderr)
        return {"success": False, "error": error_message}

def execute_gemini_cli(prompt: str, model_name: str = None, show_progress: bool = True) -> dict:
    """Execute Gemini CLI with real-time streaming output"""
    import time
    
    try:
        # Input validation
        if not isinstance(prompt, str) or len(prompt.strip()) == 0:
            return {"success": False, "error": "Invalid prompt: must be non-empty string"}
        
        if len(prompt) > 1000000:  # 1MB limit
            return {"success": False, "error": "Prompt too large (max 1MB)"}
        
        # Validate model name if provided
        if model_name is not None:
            if not isinstance(model_name, str) or not model_name.strip():
                return {"success": False, "error": "Invalid model name"}
            # Basic sanitization: only allow alphanumeric, dots, hyphens
            if not all(c.isalnum() or c in '.-' for c in model_name):
                return {"success": False, "error": "Invalid model name characters"}
        
        # Build command args safely (no shell=True)
        cmd_args = ["gemini"]
        if model_name:
            cmd_args.extend(["-m", model_name])
        cmd_args.extend(["-p", prompt])
        
        if show_progress:
            print("🔍 Starting Gemini CLI analysis...", file=sys.stderr)
            print(f"📝 Prompt length: {len(prompt)} characters", file=sys.stderr)
            print("⏳ Streaming output:", file=sys.stderr)
            print("-" * 50, file=sys.stderr)
        
        # Use Popen for real-time streaming - SECURE VERSION (no shell=True)
        # Include GOOGLE_CLOUD_PROJECT if it's set
        env = {"PATH": os.environ.get("PATH", "")}
        if "GOOGLE_CLOUD_PROJECT" in os.environ:
            env["GOOGLE_CLOUD_PROJECT"] = os.environ["GOOGLE_CLOUD_PROJECT"]
        
        process = subprocess.Popen(
            cmd_args,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            env=env,  # Include necessary environment variables
            cwd=None  # Use current working directory
        )
        
        output_lines = []
        start_time = time.time()
        last_progress = time.time()
        
        # Stream output in real-time
        while True:
            line = process.stdout.readline()
            if line:
                output_lines.append(line)
                if show_progress:
                    # Show real-time output
                    print(line.rstrip(), flush=True)
                last_progress = time.time()  # Reset timer when we get output
            elif process.poll() is not None:
                break
            
            # Show progress every 15 seconds when no output
            if show_progress and time.time() - last_progress > 15:
                elapsed = int(time.time() - start_time)
                print(f"\n⏱️  Analysis in progress... {elapsed}s elapsed", file=sys.stderr)
                last_progress = time.time()  # Reset timer
        
        # Get any remaining output
        remaining_stdout, stderr = process.communicate()
        if remaining_stdout:
            output_lines.append(remaining_stdout)
            if show_progress:
                print(remaining_stdout.rstrip(), flush=True)
        
        full_output = ''.join(output_lines)
        
        if show_progress:
            print("-" * 50, file=sys.stderr)
            print("✅ Analysis complete!", file=sys.stderr)
        
        if process.returncode == 0:
            return {"success": True, "output": full_output}
        else:
            return {"success": False, "error": stderr}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_gemini_smart(prompt: str, task_type: str = "quick_query", show_progress: bool = True) -> dict:
    """Smart execution: try API first, fall back to CLI if needed"""
    
    # Select appropriate model
    model_type = MODEL_ASSIGNMENTS.get(task_type, "flash")
    model_name = GEMINI_MODELS[model_type]
    
    if show_progress:
        print(f"📝 Task: {task_type}", file=sys.stderr)
        print(f"🤖 Selected model: {model_name} ({model_type})", file=sys.stderr)
    
    # Try API first if key is available
    if GOOGLE_API_KEY:
        if show_progress:
            print("🚀 Attempting direct API call...", file=sys.stderr)
        result = execute_gemini_api(prompt, model_name, show_progress)
        if result["success"]:
            return result
        if show_progress:
            print("🔄 API failed, falling back to CLI...", file=sys.stderr)
    else:
        if show_progress:
            print("📝 No API key found, using CLI directly", file=sys.stderr)
    
    # Fallback to CLI
    return execute_gemini_cli(prompt, model_name, show_progress)

def quick_query(query: str, context: str = ""):
    """Ask Gemini CLI a quick question"""
    # Sanitize inputs to prevent prompt injection
    sanitized_query = sanitize_for_prompt(query, max_length=10000)
    sanitized_context = sanitize_for_prompt(context, max_length=50000)
    
    if sanitized_context:
        prompt = f"Context: {sanitized_context}\n\nQuestion: {sanitized_query}\n\nProvide a concise answer."
    else:
        prompt = f"Question: {sanitized_query}\n\nProvide a concise answer."
    
    result = execute_gemini_smart(prompt, "quick_query")
    
    if result["success"]:
        print(f"Query: {query}")
        print("=" * 50)
        print(result["output"])
    else:
        print(f"Error: {result['error']}")

def analyze_code(file_path: str, analysis_type: str = "comprehensive"):
    """Analyze a code file"""
    try:
        # Input validation
        if not isinstance(file_path, str) or not file_path.strip():
            print("Error: Invalid file path")
            return
        
        if not isinstance(analysis_type, str) or analysis_type not in ["comprehensive", "security", "performance", "architecture"]:
            print("Error: Invalid analysis type")
            return
        
        # Path security validation
        try:
            # Resolve the path and ensure it's within allowed boundaries
            resolved_path = Path(file_path).resolve()
            current_dir = Path.cwd().resolve()
            
            # Check if the resolved path is within current directory tree (prevent path traversal)
            try:
                resolved_path.relative_to(current_dir)
            except ValueError:
                print(f"Error: File access denied - path outside allowed directory: {file_path}")
                return
            
            # Additional security checks
            if not resolved_path.exists():
                print(f"Error: File not found: {file_path}")
                return
            
            if not resolved_path.is_file():
                print(f"Error: Path is not a file: {file_path}")
                return
            
            # Check file extension for allowed types
            allowed_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.rs', '.vue', '.html', '.css', '.scss', '.sass', '.jsx', '.tsx', '.json', '.yaml', '.toml', '.md', '.txt'}
            if resolved_path.suffix.lower() not in allowed_extensions:
                print(f"Error: File type not supported: {resolved_path.suffix}")
                return
            
            file_path = str(resolved_path)  # Use the resolved, validated path
            
        except Exception as e:
            print(f"Error: Path validation failed: {str(e)}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) > MAX_FILE_SIZE:
            print(f"Warning: File too large ({len(content)} bytes). Truncating to {MAX_FILE_SIZE} bytes...")
            content = content[:MAX_FILE_SIZE]
        
        line_count = len(content.splitlines())
        if line_count > MAX_LINES:
            print(f"Warning: Too many lines ({line_count}). Truncating to {MAX_LINES} lines...")
            lines = content.splitlines()[:MAX_LINES]
            content = '\n'.join(lines)
        
        # Sanitize inputs to prevent prompt injection
        sanitized_content = sanitize_for_prompt(content, max_length=MAX_FILE_SIZE)
        # analysis_type is already validated above
        
        prompt = f"""Perform a {analysis_type} analysis of this code:

{sanitized_content}

Provide comprehensive analysis including:
1. Code structure and organization
2. Logic flow and algorithm efficiency
3. Security considerations and vulnerabilities
4. Performance implications and optimizations
5. Error handling and edge cases
6. Code quality and maintainability
7. Best practices compliance
8. Specific recommendations for improvements

Be thorough and provide actionable insights."""
        
        result = execute_gemini_smart(prompt, "analyze_code")
        
        if result["success"]:
            print(f"Code Analysis: {file_path}")
            print(f"Type: {analysis_type}")
            print(f"Lines: {line_count}")
            print("=" * 50)
            print(result["output"])
        else:
            print(f"Error: {result['error']}")
            
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

def analyze_codebase(directory_path: str, analysis_scope: str = "all"):
    """Analyze entire codebase"""
    # Input validation
    if not isinstance(directory_path, str) or not directory_path.strip():
        print("Error: Invalid directory path")
        return
    
    if not isinstance(analysis_scope, str) or analysis_scope not in ["structure", "security", "performance", "patterns", "all"]:
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
            print(f"Error: Directory access denied - path outside allowed directory: {directory_path}")
            return
        
        if not resolved_path.exists():
            print(f"Error: Directory not found: {directory_path}")
            return
        
        if not resolved_path.is_dir():
            print(f"Error: Path is not a directory: {directory_path}")
            return
        
        # Use sanitized directory name for prompt (just the name, not full path)
        safe_dir_name = sanitize_for_prompt(resolved_path.name, max_length=100)
        
    except Exception as e:
        print(f"Error: Path validation failed: {str(e)}")
        return
    
    prompt = f"""Analyze this codebase in directory '{safe_dir_name}' (scope: {analysis_scope}):

Provide comprehensive analysis including:
1. Overall architecture and design patterns
2. Code quality and maintainability assessment  
3. Security considerations and potential vulnerabilities
4. Performance implications and bottlenecks
5. Best practices adherence and improvement suggestions
6. Dependencies and integration points
7. Testing coverage and quality assurance
8. Documentation and code clarity

Be thorough and detailed in your analysis. Focus on actionable insights and recommendations."""
    
    result = execute_gemini_smart(prompt, "analyze_codebase")
    
    if result["success"]:
        print(f"Codebase Analysis: {directory_path}")
        print(f"Scope: {analysis_scope}")
        print("=" * 50)
        print(result["output"])
    else:
        print(f"Error: {result['error']}")

def main():
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