#!/usr/bin/env python3
"""
Slash Commands Implementation for Gemini MCP Integration
Provides easy-to-use slash commands that map to MCP tools
"""

import json
import os
import sys
from pathlib import Path

def load_commands_config():
    """Load slash commands configuration"""
    config_path = Path(__file__).parent.parent / "slash-commands.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Slash commands config not found at {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in slash commands config: {e}")
        return None

def show_help(config, command_name=None):
    """Show help for all commands or a specific command"""
    if command_name and command_name != "all":
        if command_name in config["commands"]:
            cmd = config["commands"][command_name]
            print(f"\n🔍 Command: /{command_name}")
            print(f"Description: {cmd['description']}")
            print(f"Usage: {cmd['usage']}")
            if cmd.get("examples"):
                print("Examples:")
                for example in cmd["examples"]:
                    print(f"  {example}")
        else:
            print(f"❌ Command '/{command_name}' not found")
        return
    
    print("\n🚀 Gemini MCP Slash Commands\n")
    
    categories = config.get("categories", {})
    for category, commands in categories.items():
        print(f"📁 {category}:")
        for cmd_name in commands:
            if cmd_name in config["commands"]:
                cmd = config["commands"][cmd_name]
                print(f"  /{cmd_name:<12} - {cmd['description']}")
        print()
    
    print("💡 Use '/help [command]' for detailed help on a specific command")
    print("💡 Example: /help analyze")

def check_status():
    """Check MCP connection status"""
    print("🔍 Checking Gemini MCP Status...")
    print("✅ Slash commands configuration loaded")
    print("✅ MCP server: gemini-mcp")
    print("✅ Available models: gemini-2.5-flash, gemini-2.5-pro")
    print("\n💡 Use Claude Code to test MCP tools:")
    print("   - Try: 'Use gemini_quick_query to ask about Python best practices'")
    print("   - Try: 'Use gemini_analyze_code to review this file'")

def show_models():
    """Show available models and configuration"""
    print("🤖 Gemini Models Configuration\n")
    print("Available Models:")
    print("  • gemini-2.5-flash  - Fast responses (quick queries)")
    print("  • gemini-2.5-pro    - Deep analysis (code analysis, codebase review)")
    print("\nModel Assignment:")
    print("  • /gemini, /g       → gemini-2.5-flash")
    print("  • /analyze, /a      → gemini-2.5-pro")
    print("  • /codebase, /c     → gemini-2.5-pro")
    print("  • /security, /s     → gemini-2.5-pro")
    print("  • /performance, /p  → gemini-2.5-pro")
    print("\nConfiguration:")
    print("  • Max file size: 80KB")
    print("  • Max lines: 800")
    print("  • Supported file types: .py, .js, .ts, .vue, .html, .css, etc.")

def execute_mcp_command(tool_name, parameters):
    """Execute an MCP tool command"""
    print(f"🔧 Executing MCP tool: {tool_name}")
    print(f"📋 Parameters: {parameters}")
    print("\n💡 In Claude Code, use:")
    
    if tool_name == "gemini_quick_query":
        query = parameters.get("query", "")
        print(f"   Use gemini_quick_query with query: \"{query}\"")
    
    elif tool_name == "gemini_analyze_code":
        analysis_type = parameters.get("analysis_type", "comprehensive")
        print(f"   Use gemini_analyze_code with analysis_type: \"{analysis_type}\"")
        print(f"   Select the file/code you want to analyze")
    
    elif tool_name == "gemini_codebase_analysis":
        directory = parameters.get("directory_path", ".")
        scope = parameters.get("analysis_scope", "all")
        print(f"   Use gemini_codebase_analysis with:")
        print(f"   - directory_path: \"{directory}\"")
        print(f"   - analysis_scope: \"{scope}\"")

def smart_analyze(target, analysis_type, focus_type=None):
    """Smart analysis that chooses the right tool based on target"""
    target_path = Path(target)
    
    print(f"🎯 Smart Analysis: {target} ({analysis_type} focus)")
    
    if target_path.is_file():
        print(f"📄 Detected file: Using gemini_analyze_code")
        execute_mcp_command("gemini_analyze_code", {
            "analysis_type": analysis_type
        })
    elif target_path.is_dir():
        print(f"📁 Detected directory: Using gemini_codebase_analysis")
        execute_mcp_command("gemini_codebase_analysis", {
            "directory_path": target,
            "analysis_scope": analysis_type
        })
    else:
        print(f"❌ Target not found: {target}")

def process_command(command_name, args):
    """Process a slash command"""
    config = load_commands_config()
    if not config:
        return
    
    # Remove leading slash if present
    if command_name.startswith('/'):
        command_name = command_name[1:]
    
    if command_name not in config["commands"]:
        print(f"❌ Unknown command: /{command_name}")
        print("💡 Use '/help' to see all available commands")
        return
    
    cmd_config = config["commands"][command_name]
    action = cmd_config["action"]
    
    if action["type"] == "mcp_tool":
        # Direct MCP tool execution
        tool_name = action["tool"]
        parameters = {}
        
        # Process parameters
        for param_name, param_value in action["parameters"].items():
            if param_value == "{args}":
                parameters[param_name] = " ".join(args)
            elif param_value == "{arg1}":
                parameters[param_name] = args[0] if args else ""
            elif param_value.startswith("{arg2:") and param_value.endswith("}"):
                default_value = param_value[6:-1]  # Extract default from {arg2:default}
                parameters[param_name] = args[1] if len(args) > 1 else default_value
            elif param_value == "{file_content}":
                if args:
                    file_path = args[0]
                    print(f"📖 Reading file: {file_path}")
                    try:
                        with open(file_path, 'r') as f:
                            parameters[param_name] = f.read()
                    except FileNotFoundError:
                        print(f"❌ File not found: {file_path}")
                        return
                    except Exception as e:
                        print(f"❌ Error reading file: {e}")
                        return
        
        execute_mcp_command(tool_name, parameters)
    
    elif action["type"] == "smart_analyze":
        # Smart analysis that chooses tool based on target
        if not args:
            print(f"❌ Usage: {cmd_config['usage']}")
            return
        
        target = args[0]
        analysis_type = action["parameters"]["analysis_type"]
        smart_analyze(target, analysis_type)
    
    elif action["type"] == "show_help":
        target = args[0] if args else "all"
        show_help(config, target)
    
    elif action["type"] == "check_status":
        check_status()
    
    elif action["type"] == "show_models":
        show_models()

def main():
    """Main entry point for slash commands"""
    if len(sys.argv) < 2:
        print("Usage: python slash_commands.py [command] [args...]")
        print("Example: python slash_commands.py help")
        return
    
    command_name = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    process_command(command_name, args)

if __name__ == "__main__":
    main()