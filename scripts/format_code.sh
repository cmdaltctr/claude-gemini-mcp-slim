#!/bin/bash

# Script to format code before committing
# This ensures your code passes the CI formatting checks

echo "🔧 Running code formatters with uv..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Run formatters using uv
echo "📝 Running Black formatter..."
uv run black .

echo "📚 Running isort import sorter..."
uv run isort .

echo "🔍 Running flake8 linter..."
uv run flake8 . --max-line-length=88 --extend-ignore=E203,W503,E501,F401,F811,F841,E402,F541

echo "✅ Code formatting complete!"
echo "💡 You can now commit your changes with 'git add . && git commit -m \"your message\"'"
