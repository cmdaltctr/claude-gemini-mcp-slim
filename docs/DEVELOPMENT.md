# Development Workflow

This document outlines the development workflow for the Claude Gemini MCP Slim project to ensure code quality and consistency.

## Prerequisites

1. **Virtual Environment**: Make sure you have a virtual environment activated
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Install Pre-commit Hooks**:
   ```bash
   pre-commit install
   ```

## Code Formatting

### Automatic Formatting Before Commits

We use pre-commit hooks to automatically format code before commits. The hooks will:

- Remove trailing whitespace
- Fix end-of-file issues
- Format code with Black
- Sort imports with isort
- Check for basic linting issues with flake8
- Scan for security issues with bandit
- Run type checking with mypy
- Run basic pytest tests

### Manual Formatting

If you want to format code manually before committing:

```bash
# Easy way - use the provided script
./scripts/format_code.sh

# Or manually run each tool
black .
isort .
flake8 . --max-line-length=88 --extend-ignore=E203,W503,E501,F401,F811,F841,E402,F541
```

## Development Workflow

### 1. Before Making Changes

```bash
# Make sure you're on the latest main branch
git checkout main
git pull origin main

# Create a new feature branch
git checkout -b feature/your-feature-name
```

### 2. During Development

- Write your code
- Add tests for new functionality
- Run tests locally: `pytest`
- Format your code: `./scripts/format_code.sh`

### 3. Before Committing

The pre-commit hooks will automatically run when you commit, but you can also run them manually:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Or just run specific hooks
pre-commit run black --all-files
pre-commit run isort --all-files
```

### 4. Committing Changes

```bash
git add .
git commit -m "Your descriptive commit message"

# The pre-commit hooks will run automatically
# If they fail, fix the issues and commit again
```

### 5. Pushing Changes

```bash
git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Go to GitHub and create a pull request
- The CI will run all tests and checks
- Address any CI failures before merging

## CI/CD Pipeline

Our GitHub Actions workflow includes:

1. **Code Quality**: Black formatting, flake8 linting, isort import sorting, mypy type checking, bandit security scanning
2. **Unit Tests**: Python 3.10, 3.11, 3.12 compatibility
3. **Integration Tests**: MCP server integration tests
4. **Security Tests**: Security-focused tests and vulnerability scanning
5. **E2E Tests**: End-to-end workflow tests
6. **Performance Tests**: Benchmarking (on main branch only)
7. **Coverage Reports**: Code coverage analysis

## Common Issues and Solutions

### "pre-commit command not found"

```bash
# Make sure you're in the virtual environment
source venv/bin/activate
pip install pre-commit
pre-commit install
```

### "black/isort/flake8 command not found"

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

### Commit blocked by formatting issues

```bash
# Run the formatter script
./scripts/format_code.sh

# Or run individual tools
black .
isort .

# Then commit again
git add .
git commit -m "Your message"
```

### CI fails due to formatting

This means code wasn't formatted before pushing. To fix:

```bash
# Format locally
./scripts/format_code.sh

# Commit and push the fixes
git add .
git commit -m "Fix code formatting"
git push origin your-branch-name
```

## Best Practices

1. **Always run formatters before committing**: Use `./scripts/format_code.sh`
2. **Write tests**: Add tests for new functionality
3. **Keep commits small**: Make focused, atomic commits
4. **Write descriptive commit messages**: Explain what and why, not just what
5. **Run tests locally**: Don't rely solely on CI
6. **Use feature branches**: Don't commit directly to main
7. **Review your changes**: Use `git diff` before committing

## Tools Used

- **Black**: Code formatter
- **isort**: Import sorter
- **flake8**: Linter
- **mypy**: Type checker
- **bandit**: Security scanner
- **pytest**: Testing framework
- **pre-commit**: Git hooks manager

## Configuration Files

- `.pre-commit-config.yaml`: Pre-commit hook configuration
- `pyproject.toml`: Black and isort configuration
- `.github/workflows/test.yml`: CI/CD pipeline configuration
- `requirements-dev.txt`: Development dependencies
