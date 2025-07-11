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

def execute_gemini_api(prompt: str, model_name: str, show_progress: bool = True) -> dict:
    """Execute Gemini API directly with specified model"""
    try:
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
        if show_progress:
            print(f"⚠️ API call failed: {str(e)}, using CLI fallback", file=sys.stderr)
        return {"success": False, "error": str(e)}

def execute_gemini_cli(prompt: str, model_name: str = None, show_progress: bool = True) -> dict:
    """Execute Gemini CLI with real-time streaming output"""
    import time
    
    try:
        escaped_prompt = shlex.quote(prompt)
        cmd = f"gemini -p {escaped_prompt}"
        if model_name:
            cmd = f"gemini -m {model_name} -p {escaped_prompt}"
        
        if show_progress:
            print("🔍 Starting Gemini CLI analysis...", file=sys.stderr)
            print(f"📝 Prompt length: {len(prompt)} characters", file=sys.stderr)
            print("⏳ Streaming output:", file=sys.stderr)
            print("-" * 50, file=sys.stderr)
        
        # Use Popen for real-time streaming
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            env=os.environ.copy()
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
    if context:
        prompt = f"Context: {context}\n\nQuestion: {query}\n\nProvide a concise answer."
    else:
        prompt = f"Question: {query}\n\nProvide a concise answer."
    
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
        
        prompt = f"""Perform a {analysis_type} analysis of this code:

{content}

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
    if not Path(directory_path).exists():
        print(f"Error: Directory not found: {directory_path}")
        return
    
    prompt = f"""Analyze this codebase in directory '{directory_path}' (scope: {analysis_scope}):

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