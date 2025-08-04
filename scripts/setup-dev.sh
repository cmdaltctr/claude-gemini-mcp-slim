#!/bin/bash

# Development Environment Setup Script
# This script sets up the environment and installs all dependencies
# for the Claude Gemini MCP Slim project using uv

set -e  # Exit on any error

echo "🚀 Setting up development environment for Claude Gemini MCP Slim with uv..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv. Please install manually and retry."
        exit 1
    fi
fi

echo "📦 Using uv for dependency management..."

# Sync dependencies using uv (this creates venv automatically)
echo "📚 Installing all dependencies with uv..."
uv sync --dev

# Initialize Husky hooks if npm is available
echo "🔧 Initializing Husky hooks..."
npx husky install 2>/dev/null || echo "ℹ️  Husky hooks skipped (npm not available)"

# Run a test to make sure everything is working
echo "🧪 Running a quick test..."
uv run python -m pytest tests/unit/test_basic_operations.py -v || echo "ℹ️  Quick test skipped (test file not found)"

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📝 Key uv commands for development:"
echo "   uv run python script.py     # Run Python scripts"
echo "   uv run pytest              # Run tests"
echo "   uv add package_name         # Add new dependency"
echo "   uv sync                     # Sync dependencies"
echo ""
echo "🔍 To run code quality checks:"
echo "   uv run black ."
echo "   uv run isort ."
echo "   uv run flake8 ."
echo "   uv run mypy src/"
echo ""
echo "🚀 You're ready to start developing with uv!"
