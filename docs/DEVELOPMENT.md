# Development Workflow

This document outlines the development workflow for the Claude Gemini MCP Slim project to ensure code quality, consistency, and automated release management.

## Automated Release and Commit Message Enforcement

This project uses automated releases and commit message enforcement to ensure consistent versioning and changelog management.

### Release Automation with Release Please

Release Please automates the versioning and release process based on conventional commits.

#### Configuration Overview

1. **Release Please Config**
   - `.release-please-config.json`: Defines the release process tailored for our setup.
   - `.release-please-manifest.json`: Tracks current version.

2. **GitHub Actions Workflow**
   - **Path**: `.github/workflows/release.yml`
   - **Triggers**: On push to `main` branch.
   - **Steps**:
     1. Validate commit messages.
     2. Run Release Please for version tagging and changelog updates.
     3. Update version badge and changelog in `README.md`.
     4. Push changes and create GitHub release.
     5. Build and optionally publish to PyPI.

### Local Commit Message Enforcement

To enforce commit message conventions locally, Husky and Commitlint are set up.

#### Setup Steps

1. **Install Dependencies**:
   ```bash
   npm install --save-dev @commitlint/config-conventional @commitlint/cli
   npm install --save-dev husky
   ```

2. **Initialize Husky**:
   ```bash
   npx husky install
   npx husky add .husky/commit-msg 'npx --no-install commitlint --edit "$1"'
   ```

3. **Commitlint Configuration**:
   - **File**: `commitlint.config.js`
   - **Rules**: Ensures conventional commits like `feat!`, `fix`, etc.

#### Usage

- **Valid Commit Example**:
  ```bash
  git commit -m "feat: add new feature"
  git commit -m "fix: resolve bug"
  ```

- **Invalid Commit**:
  - Non-conventional messages will be rejected.

### Full Workflow Summary

1. **Locally**:
   - Commit message gets validated before commit.
   - Ensures adherence to conventional commit style.

2. **On GitHub**:
   - Pushing to `main` triggers:
     - Commit message validation.
     - Release version bumping.
     - Changelog and README updates.
     - GitHub release creation.

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

3. **Set Up Git Hooks**:
   ```bash
   # Run the setup script which handles both Python and Node.js dependencies
   ./setup-dev.sh
   
   # Or manually install Node.js dependencies for commit validation
   npm install --save-dev @commitlint/config-conventional @commitlint/cli husky
   npx husky install
   ```

## Code Formatting

### Unified Husky Hook System

We use a unified Husky hook system that runs multiple code quality checks automatically:

**Pre-commit Hook (`.husky/pre-commit`):**
- Remove trailing whitespace
- Fix end-of-file issues
- Format code with Black
- Sort imports with isort
- Check for basic linting issues with flake8
- Scan for secrets with gitleaks
- Scan for security issues with bandit
- Run type checking with mypy
- Run basic pytest tests

**Commit-msg Hook (`.husky/commit-msg`):**
- Validates commit messages follow conventional commit format
- Enforces consistent commit message structure for automated releases

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

The Husky hooks will automatically run when you commit, but you can also run them manually:

```bash
# Run the pre-commit hook manually
.husky/pre-commit

# Or run specific formatting tools
black .
isort .
flake8 .
mypy .
pytest
```

### 4. Committing Changes

Commit messages must follow conventional commit format:

```bash
git add .
git commit -m "feat: add new feature"

# The Husky hooks (.husky/pre-commit and .husky/commit-msg) will run automatically
# If they fail, fix the issues and commit again
```

**Conventional Commit Types:**
- `feat:` - New features (minor version bump)
- `fix:` - Bug fixes (patch version bump)
- `feat!:` - Breaking changes (major version bump)
- `fix!:` - Breaking bug fixes (major version bump)
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `test:` - Adding or updating tests
- `build:` - Build system or dependency changes
- `ci:` - CI/CD changes
- `chore:` - Maintenance tasks
- `revert:` - Reverting changes

**Examples:**
```bash
git commit -m "feat: add OAuth2 authentication"
git commit -m "fix: resolve memory leak in parser"
git commit -m "feat!: change API response format"
git commit -m "docs: update installation guide"
git commit -m "test: add unit tests for user service"
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

### "Husky hooks not running"

```bash
# Make sure Husky is installed and hooks are set up
npm install --save-dev husky
npx husky install

# Or run the setup script which handles everything
./setup-dev.sh
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
git commit -m "feat: your message"  # Use conventional commit format
```

### Commit blocked by commitlint

```bash
# Your commit message doesn't follow conventional commits
# Fix the message format:
git commit -m "feat: add new feature"  # ✅ Valid
git commit -m "fix: resolve bug"       # ✅ Valid
git commit -m "feat!: breaking change" # ✅ Valid

# Instead of:
git commit -m "added new feature"      # ❌ Invalid
git commit -m "bug fix"               # ❌ Invalid
```

### Release automation not working

1. **Check GitHub repository permissions**:
   - Go to Settings → Actions → General
   - Ensure "Read and write permissions" is selected
   - Ensure "Allow GitHub Actions to create and approve pull requests" is checked

2. **Check workflow files**:
   - `.github/workflows/release.yml` exists
   - `.github/workflows/validate-commits.yml` exists
   - `.release-please-config.json` exists
   - `.release-please-manifest.json` exists

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
- **husky**: Git hooks manager
- **commitlint**: Commit message validation

## Configuration Files

### Code Quality
- `.husky/pre-commit`: Pre-commit hook script (formatting, linting, testing)
- `.husky/commit-msg`: Commit message validation hook
- `pyproject.toml`: Black and isort configuration
- `requirements-dev.txt`: Development dependencies

### Release Automation
- `.release-please-config.json`: Release Please configuration
- `.release-please-manifest.json`: Current version tracking
- `commitlint.config.js`: Commit message linting rules
- `package.json`: Node.js dependencies for commitlint and husky
- `.husky/commit-msg`: Git hook for commit message validation

### GitHub Actions
- `.github/workflows/release.yml`: Automated release workflow
- `.github/workflows/validate-commits.yml`: Commit message validation
- `.github/workflows/test.yml`: CI/CD pipeline configuration

### Project Structure
- `docs/DEVELOPMENT.md`: This development guide
- `CHANGELOG.md`: Automatically generated changelog
- `README.md`: Project documentation (auto-updated with version)
