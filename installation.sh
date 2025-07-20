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
    
    # Check Python
    if ! command_exists python3 && ! command_exists python; then
        print_error "Python is not installed. Please install Python 3.8+ first."
        exit 1
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
    
    # Create virtual environment for all MCP servers
    if [ -d "$SHARED_ENV_DIR" ]; then
        print_warning "Shared MCP environment already exists. Updating..."
    else
        print_status "Creating virtual environment..."
        $PYTHON_CMD -m venv shared-mcp-env
    fi
    
    # Activate virtual environment based on OS
    if [[ "$OS" == "windows" ]]; then
        source shared-mcp-env/Scripts/activate
    else
        source shared-mcp-env/bin/activate
    fi
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install MCP dependencies
    print_status "Installing MCP dependencies..."
    pip install mcp google-generativeai python-dotenv
    
    # Install additional useful packages
    print_status "Installing additional packages..."
    pip install requests aiohttp
    
    print_success "Shared MCP environment created at: $SHARED_ENV_DIR"
    
    # Detect site-packages path
    SITE_PACKAGES_PATH=$(python -c "import site; print(site.getsitepackages()[0])")
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
    if python -c "import mcp" 2>/dev/null; then
        print_success "MCP library installed correctly"
    else
        print_error "Failed to import MCP library"
        exit 1
    fi
    
    # Test Google GenerativeAI import
    if python -c "import google.generativeai" 2>/dev/null; then
        print_success "Google GenerativeAI library installed correctly"
    else
        print_error "Failed to import Google GenerativeAI library"
        exit 1
    fi
    
    # Deactivate environment
    deactivate
    
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
    echo "  python3 gemini_helper.py query 'What is Python?'"
    echo ""
    echo "📝 The MCP server automatically detects and uses the shared environment!"
    echo ""
    echo "🔧 Manual environment activation (only for development):"
    if [[ "$OS" == "windows" ]]; then
        echo "  source ~/mcp-servers/shared-mcp-env/Scripts/activate"
    else
        echo "  source ~/mcp-servers/shared-mcp-env/bin/activate"
    fi
    echo "  # Or: source $ACTIVATE_SCRIPT"
    echo "  # This is OPTIONAL - only needed for manual package installation"
}

# Run main function
main "$@"
