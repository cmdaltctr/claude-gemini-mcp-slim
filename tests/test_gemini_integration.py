#!/usr/bin/env python3
"""Simple test script to verify Gemini CLI integration works."""

import subprocess
import sys
import json
import shlex

def run_gemini_query(query: str, timeout: int = 30) -> dict:
    """Run a Gemini CLI query and return the result."""
    try:
        # Use shlex.quote to properly escape the query
        escaped_query = shlex.quote(query)
        
        # Run the Gemini CLI command
        result = subprocess.run(
            f"gemini -p {escaped_query}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else None,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": None,
            "error": f"Query timed out after {timeout} seconds",
            "return_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": f"Error running query: {str(e)}",
            "return_code": -1
        }

def test_basic_query():
    """Test basic Gemini CLI functionality."""
    print("Testing basic Gemini CLI query...")
    
    result = run_gemini_query("What is 2+2? Please respond with just the number.")
    
    if result["success"]:
        print(f"✓ Query successful: {result['output']}")
        return True
    else:
        print(f"✗ Query failed: {result['error']}")
        return False

def test_code_analysis():
    """Test code analysis capability."""
    print("\nTesting code analysis...")
    
    test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    query = f"Analyze this Python code for potential improvements. Keep response under 100 words:\n\n{test_code}"
    
    result = run_gemini_query(query)
    
    if result["success"]:
        print(f"✓ Code analysis successful:")
        print(f"  {result['output']}")
        return True
    else:
        print(f"✗ Code analysis failed: {result['error']}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("Gemini CLI Integration Test")
    print("=" * 50)
    
    tests = [
        test_basic_query,
        test_code_analysis
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)