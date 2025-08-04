#!/bin/bash

# Gemini MCP Server Installation Script
# Works on macOS, Linux, and Windows (via WSL/Git Bash)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Get Python version
get_python_version() {
    if command_exists python3; then
        python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    elif command_exists python; then
        python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    else
        echo ""
    fi
}

# Main installation function
main() {
    echo "🚀 Gemini MCP Server Installation"
    echo "=================================="
    
    # Detect OS
    OS=$(detect_os)
    print_status "Detected OS: $OS"
    
    # Check for uv
    if ! command_exists uv; then
        print_error "uv is not installed. Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    # Check Python (uv will handle Python installation if needed)
    if ! command_exists python3 && ! command_exists python; then
        print_warning "Python not found. uv will handle Python installation."
    fi
    
    # Validate Python version
    PYTHON_VERSION=$(get_python_version)
    if [ -n "$PYTHON_VERSION" ]; then
        MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
            print_error "Python 3.10+ required. Found: $PYTHON_VERSION"
            exit 1
        fi
    fi
    
    PYTHON_VERSION=$(get_python_version)
    print_status "Python version: $PYTHON_VERSION"
    
    # Set Python command
    PYTHON_CMD="python3"
    if ! command_exists python3; then
        PYTHON_CMD="python"
    fi
    
    # Create shared MCP directory
    print_status "Creating shared MCP directory..."
    MCP_DIR="$HOME/mcp-servers"
    SHARED_ENV_DIR="$MCP_DIR/shared-mcp-env"
    
    mkdir -p "$MCP_DIR"
    cd "$MCP_DIR"
    
    # Create uv virtual environment for all MCP servers
    if [ -d "$SHARED_ENV_DIR" ]; then
        print_warning "Shared MCP environment already exists. Updating..."
        cd "$MCP_DIR"
        uv sync --project=shared-mcp-env
    else
        print_status "Creating uv virtual environment..."
        cd "$MCP_DIR"
        uv venv shared-mcp-env --python 3.10
    fi
    
    # Create a minimal pyproject.toml for the shared environment
    cat > "$MCP_DIR/pyproject.toml" << 'EOF'
[project]
name = "shared-mcp-env"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "google-generativeai>=0.8.0",
    "instructor[google-generativeai]>=0.6.0",
    "pydantic>=2.0.0",
    "requests",
    "aiohttp",
    "python-dotenv",
]
EOF
    
    # Install dependencies using uv
    print_status "Installing dependencies with uv..."
    uv sync
    
    print_success "Shared MCP environment created at: $SHARED_ENV_DIR"
    
    # Detect site-packages path using uv
    SITE_PACKAGES_PATH=$(uv run python -c "import site; print(site.getsitepackages()[0])")
    print_success "Site-packages located at: $SITE_PACKAGES_PATH"
    
    # Create environment info file
    ENV_INFO_FILE="$MCP_DIR/env-info.json"
    cat > "$ENV_INFO_FILE" << EOF
{
    "created_at": "$(date -Iseconds)",
    "os": "$OS",
    "python_version": "$PYTHON_VERSION",
    "shared_env_path": "$SHARED_ENV_DIR",
    "site_packages_path": "$SITE_PACKAGES_PATH",
    "python_command": "$PYTHON_CMD"
}
EOF
    
    print_success "Environment info saved to: $ENV_INFO_FILE"
    
    # Create activation script
    ACTIVATE_SCRIPT="$MCP_DIR/activate-shared-env.sh"
    if [[ "$OS" == "windows" ]]; then
        cat > "$ACTIVATE_SCRIPT" << 'EOF'
#!/bin/bash
# Activate shared MCP environment (Windows)
source ~/mcp-servers/shared-mcp-env/Scripts/activate
echo "✅ Shared MCP environment activated"
EOF
    else
        cat > "$ACTIVATE_SCRIPT" << 'EOF'
#!/bin/bash
# Activate shared MCP environment (macOS/Linux)
source ~/mcp-servers/shared-mcp-env/bin/activate
echo "✅ Shared MCP environment activated"
EOF
    fi
    
    chmod +x "$ACTIVATE_SCRIPT"
    print_success "Activation script created at: $ACTIVATE_SCRIPT"
    
    # Test the installation
    print_status "Testing installation..."
    
    # Test MCP import
    if uv run python -c "import mcp" 2>/dev/null; then
        print_success "MCP library installed correctly"
    else
        print_error "Failed to import MCP library"
        exit 1
    fi
    
    # Test Google GenerativeAI import
    if uv run python -c "import google.generativeai" 2>/dev/null; then
        print_success "Google GenerativeAI library installed correctly"
    else
        print_error "Failed to import Google GenerativeAI library"
        exit 1
    fi
    
    # Test instructor import
    if uv run python -c "import instructor" 2>/dev/null; then
        print_success "Instructor library installed correctly"
    else
        print_error "Failed to import Instructor library"
        exit 1
    fi
    
    # Test pydantic import
    if uv run python -c "import pydantic" 2>/dev/null; then
        print_success "Pydantic library installed correctly"
    else
        print_error "Failed to import Pydantic library"
        exit 1
    fi
    
    echo ""
    echo "🎉 Installation Complete!"
    echo "========================"
    echo ""
    echo "📁 Shared MCP Environment: $SHARED_ENV_DIR"
    echo "📄 Environment Info: $ENV_INFO_FILE"
    echo ""
    print_success "✅ Ready to use! No activation required."
    echo ""
    echo "🚀 Try it now:"
    echo "  # Test with your MCP client (Claude Desktop, Continue, etc.)"
    echo "  # The MCP server will automatically use the shared environment"
    echo ""
    echo "📝 The MCP server automatically detects and uses the shared environment!"
    echo ""
    echo "🔧 Manual environment usage (for development):"
    echo "  cd ~/mcp-servers"
    echo "  uv run python your_script.py  # Run Python scripts with uv"
    echo "  uv add package_name          # Add new packages"
    echo "  uv sync                      # Sync dependencies"
    echo ""
    echo "📦 uv manages the virtual environment automatically!"
}

# Run main function
main "$@"
