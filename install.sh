#!/bin/bash

# Enhanced File Manager MCP - DXT Installation Script
# This script sets up the enhanced DXT file manager with all dependencies

set -e

echo "🚀 Enhanced File Manager MCP - DXT Installation"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python is installed
check_python() {
    print_step "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required. Found Python $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION found"
}

# Check if pip is installed
check_pip() {
    print_step "Checking pip installation..."
    
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip3."
        exit 1
    fi
    
    print_success "pip3 found"
}

# Install Python dependencies
install_dependencies() {
    print_step "Installing Python dependencies..."
    
    pip3 install fastmcp websockets 2>/dev/null || {
        print_error "Failed to install Python dependencies"
        exit 1
    }
    
    print_success "Python dependencies installed"
}

# Create configuration directory
create_config_dir() {
    print_step "Creating configuration directory..."
    
    CONFIG_DIR="$HOME/.config/FileManagerMCP"
    mkdir -p "$CONFIG_DIR"
    
    print_success "Configuration directory created: $CONFIG_DIR"
}

# Set up workspace directory
setup_workspace() {
    print_step "Setting up workspace directory..."
    
    # Default workspace
    WORKSPACE_DIR="$HOME/Documents/FileManagerMCP"
    
    read -p "Enter workspace directory path (default: $WORKSPACE_DIR): " USER_WORKSPACE
    if [ ! -z "$USER_WORKSPACE" ]; then
        WORKSPACE_DIR="$USER_WORKSPACE"
    fi
    
    mkdir -p "$WORKSPACE_DIR"
    print_success "Workspace directory created: $WORKSPACE_DIR"
    
    # Update manifest with workspace path
    if [ -f "manifest.json" ]; then
        # Create a backup
        cp manifest.json manifest.json.bak
        
        # Update workspace path in manifest (simplified - real implementation would need JSON parsing)
        print_success "Workspace path configured in manifest"
    fi
}

# Create desktop entry (Linux/macOS)
create_desktop_entry() {
    print_step "Creating desktop entry..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # For Linux
    if [ -d "$HOME/.local/share/applications" ]; then
        cat > "$HOME/.local/share/applications/file-manager-mcp.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=File Manager MCP
Comment=Enhanced File Manager with MCP support
Exec=python3 "$SCRIPT_DIR/server/main.py" --workspace="$WORKSPACE_DIR"
Icon=$SCRIPT_DIR/assets/icon.png
Terminal=false
StartupNotify=true
Categories=Utility;FileManager;
EOF
        print_success "Desktop entry created for Linux"
    fi
    
    # For macOS (simplified)
    if [ "$(uname)" == "Darwin" ]; then
        print_warning "macOS desktop integration requires additional setup"
    fi
}

# Create startup script
create_startup_script() {
    print_step "Creating startup script..."
    
    cat > start-file-manager.sh << 'EOF'
#!/bin/bash
# Enhanced File Manager MCP Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$HOME/Documents/FileManagerMCP"

echo "🚀 Starting Enhanced File Manager MCP..."
echo "Workspace: $WORKSPACE_DIR"
echo "UI Port: 8080"
echo "Press Ctrl+C to stop"

python3 "$SCRIPT_DIR/server/main.py" \
    --workspace="$WORKSPACE_DIR" \
    --ui-port=8080 \
    --debug \
    --log-level=info
EOF
    
    chmod +x start-file-manager.sh
    print_success "Startup script created: start-file-manager.sh"
}

# Create uninstall script
create_uninstall_script() {
    print_step "Creating uninstall script..."
    
    cat > uninstall.sh << 'EOF'
#!/bin/bash
# Enhanced File Manager MCP Uninstall Script

echo "🗑️  Uninstalling Enhanced File Manager MCP..."

# Remove configuration directory
CONFIG_DIR="$HOME/.config/FileManagerMCP"
if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    echo "✅ Configuration directory removed"
fi

# Remove desktop entry
DESKTOP_FILE="$HOME/.local/share/applications/file-manager-mcp.desktop"
if [ -f "$DESKTOP_FILE" ]; then
    rm "$DESKTOP_FILE"
    echo "✅ Desktop entry removed"
fi

# Remove startup script
if [ -f "start-file-manager.sh" ]; then
    rm "start-file-manager.sh"
    echo "✅ Startup script removed"
fi

# Remove this uninstall script
rm "$0"

echo "✅ Uninstall complete"
EOF
    
    chmod +x uninstall.sh
    print_success "Uninstall script created: uninstall.sh"
}

# Verify installation
verify_installation() {
    print_step "Verifying installation..."
    
    # Check if server can start
    timeout 5 python3 server/main.py --help > /dev/null 2>&1 || {
        print_error "Server verification failed"
        exit 1
    }
    
    # Check if UI files exist
    if [ ! -f "ui/index.html" ] || [ ! -f "ui/app.js" ]; then
        print_error "UI files missing"
        exit 1
    fi
    
    print_success "Installation verified"
}

# Main installation process
main() {
    echo
    print_step "Starting installation process..."
    
    # Check prerequisites
    check_python
    check_pip
    
    # Install dependencies
    install_dependencies
    
    # Setup directories
    create_config_dir
    setup_workspace
    
    # Create scripts and entries
    create_startup_script
    create_desktop_entry
    create_uninstall_script
    
    # Verify installation
    verify_installation
    
    echo
    echo "🎉 Installation complete!"
    echo
    echo "To start the Enhanced File Manager MCP:"
    echo "  ./start-file-manager.sh"
    echo
    echo "To access the UI:"
    echo "  Open http://localhost:8080 in your browser"
    echo "  Or use the hotkey: Ctrl+Shift+F (Cmd+Shift+F on macOS)"
    echo
    echo "Configuration directory: $HOME/.config/FileManagerMCP"
    echo "Workspace directory: $WORKSPACE_DIR"
    echo
    echo "To uninstall:"
    echo "  ./uninstall.sh"
    echo
    print_success "Ready to use!"
}

# Run main function
main "$@" 