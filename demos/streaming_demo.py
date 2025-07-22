#!/usr/bin/env python3
"""
Demo script to test the streaming progress functionality
"""

from claude_gemini_mcp.gemini_helper import execute_gemini_smart_with_progress


def test_streaming_demo():
    """Test the streaming progress functionality with a simple query"""
    print("Testing streaming progress functionality...")
    print("=" * 60)

    # Test with a simple query that will generate a response
    test_prompt = "Explain what Python is in exactly 50 words"

    result = execute_gemini_smart_with_progress(test_prompt, "quick_query")

    print("\n" + "=" * 60)
    print("Demo completed!")

    if result["success"]:
        print(f"✅ Success! Response length: {len(result['output'])} characters")
    else:
        print(f"❌ Failed: {result['error']}")


if __name__ == "__main__":
    test_streaming_demo()
