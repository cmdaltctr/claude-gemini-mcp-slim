#!/bin/bash

# Development Environment Setup Script
# This script sets up the virtual environment and installs all dependencies
# for the Claude Gemini MCP Slim project

set -e  # Exit on any error

echo "🚀 Setting up development environment for Claude Gemini MCP Slim..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install production dependencies
echo "📚 Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "🛠️ Installing development dependencies..."
pip install -r requirements-dev.txt

# Initialize Husky hooks
echo "🔧 Initializing Husky hooks..."
npx husky install || echo "ℹ️  Husky hooks already initialized or npm not available"

# Run a test to make sure everything is working
echo "🧪 Running a quick test..."
python -m pytest tests/unit/test_basic_operations.py -v

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📝 To activate the virtual environment in the future, run:"
echo "   source .venv/bin/activate"
echo ""
echo "🧪 To run all tests:"
echo "   python -m pytest"
echo ""
echo "🔍 To run code quality checks manually:"
echo "   npm run lint" 
echo "   npm run format"
echo "   npm run test"
echo ""
echo "🚀 You're ready to start developing!"
