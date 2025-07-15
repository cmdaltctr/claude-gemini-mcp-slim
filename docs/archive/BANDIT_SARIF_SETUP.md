# Bandit SARIF Generation Setup

## Overview
This document describes the implementation of Bandit SARIF generation for the CI/CD pipeline and local development.

## Changes Made

### 1. Created `.bandit` Configuration File
- **Location**: `.bandit` (project root)
- **Purpose**: Configure Bandit to skip test directories and virtual environments
- **Key settings**:
  - Skip tests: `B101` (assert_used), `B601` (paramiko_calls)
  - Exclude directories: `/tests/`, `/venv/`, `/.venv/`, `/.test-env/`, `/htmlcov/`, `/.pytest_cache/`, `/.mypy_cache/`, `/.benchmarks/`, `/__pycache__/`, `/.git/`, `/node_modules/`, `/.github/`
  - Exclude file types: `*.pyc`, `*.pyo`, `*.swp`, `*.bak`, `*~`, `*.log`

### 2. Updated CI Workflow (`.github/workflows/security.yml`)
- **Install dependencies**: Added `bandit-sarif-formatter` to enable SARIF output
- **Targeted scanning**: Use `find . -maxdepth 1 -name "*.py" -type f` to scan only root-level Python files
- **Generate multiple formats**:
  - JSON: `bandit-report.json`
  - SARIF: `bandit-results.sarif`
- **Upload artifacts**: Both JSON and SARIF files are now included in the artifact upload
- **Upload to GitHub Security**: SARIF file is uploaded to GitHub Security dashboard

### 3. Updated Development Dependencies
- **File**: `requirements-dev.txt`
- **Added**: `bandit-sarif-formatter>=1.1.1` for SARIF output support

## Usage

### Local Development
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run bandit with SARIF output (specific files to avoid hanging)
bandit -r ./gemini_helper.py ./test_security.py ./gemini_mcp_server.py --format sarif --output bandit-results.sarif

# Or use find command to auto-detect files
PYTHON_FILES=$(find . -maxdepth 1 -name "*.py" -type f)
bandit -r $PYTHON_FILES --format sarif --output bandit-results.sarif

# Generate both JSON and SARIF reports
bandit -r ./gemini_helper.py ./test_security.py ./gemini_mcp_server.py -f json -o bandit-report.json
bandit -r ./gemini_helper.py ./test_security.py ./gemini_mcp_server.py --format sarif --output bandit-results.sarif
```

### CI/CD Pipeline
The CI workflow automatically:
1. Installs `bandit[toml]` and `bandit-sarif-formatter`
2. Runs bandit on root-level Python files
3. Generates both JSON and SARIF reports
4. Uploads SARIF to GitHub Security
5. Uploads both reports as artifacts

## Files Generated
- `bandit-results.sarif` - SARIF format for GitHub Security integration
- `bandit-report.json` - JSON format for custom processing

## Benefits
1. **GitHub Security Integration**: SARIF files are automatically uploaded to GitHub Security dashboard
2. **Artifact Storage**: Both report formats are stored as CI artifacts
3. **Local Development**: Same command works locally with proper configuration
4. **Performance**: Targeted scanning avoids hanging on large directories
5. **Flexibility**: Multiple output formats available

## Configuration Details
The `.bandit` file is configured to:
- Skip common false positives (assert statements, paramiko calls)
- Exclude virtual environments and cache directories
- Focus on actual source code files
- Provide efficient scanning without timeouts

## Troubleshooting
- If bandit hangs, use targeted file scanning instead of directory scanning
- Ensure `bandit-sarif-formatter` is installed for SARIF output
- Check `.bandit` configuration for proper exclusions
