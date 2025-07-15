#!/bin/bash

# Script to format code before committing
# This ensures your code passes the CI formatting checks

echo "🔧 Running code formatters..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run formatters
echo "📝 Running Black formatter..."
black .

echo "📚 Running isort import sorter..."
isort .

echo "🔍 Running flake8 linter..."
flake8 . --max-line-length=88 --extend-ignore=E203,W503,E501,F401,F811,F841,E402,F541

echo "✅ Code formatting complete!"
echo "💡 You can now commit your changes with 'git add . && git commit -m \"your message\"'"
