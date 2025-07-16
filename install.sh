#!/bin/bash

# Enhanced DXT File Manager Installation Script
# Installs Gradio-based file manager with MCP server capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"
WORKSPACE_DIR="${INSTALL_DIR}/workspace"
CONFIG_DIR="${INSTALL_DIR}/.config"
LOG_FILE="${INSTALL_DIR}/install.log"
PYTHON_MIN_VERSION="3.8"
GRADIO_VERSION="4.0.0"

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to compare version numbers
version_compare() {
    printf '%s\n%s\n' "$1" "$2" | sort -V | head -n1
}

# Function to check Python version
check_python_version() {
    print_status "Checking Python version..."
    
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        print_error "Please install Python 3.${PYTHON_MIN_VERSION} or higher"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    MIN_VERSION_CHECK=$(version_compare "$PYTHON_MIN_VERSION" "$PYTHON_VERSION")
    
    if [ "$MIN_VERSION_CHECK" != "$PYTHON_MIN_VERSION" ]; then
        print_error "Python version $PYTHON_VERSION is too old"
        print_error "Minimum required version is $PYTHON_MIN_VERSION"
        exit 1
    fi
    
    print_success "Python version $PYTHON_VERSION is compatible"
}

# Function to check pip availability
check_pip() {
    print_status "Checking pip availability..."
    
    if ! command_exists pip3; then
        print_error "pip3 is required but not installed"
        print_error "Please install pip3 for Python 3"
        exit 1
    fi
    
    print_success "pip3 is available"
}

# Function to create virtual environment
create_venv() {
    print_status "Creating Python virtual environment..."
    
    if [ -d "${INSTALL_DIR}/venv" ]; then
        print_warning "Virtual environment already exists, removing..."
        rm -rf "${INSTALL_DIR}/venv"
    fi
    
    python3 -m venv "${INSTALL_DIR}/venv"
    
    # Activate virtual environment
    source "${INSTALL_DIR}/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_success "Virtual environment created and activated"
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Create requirements file
    cat > "${INSTALL_DIR}/requirements.txt" << EOF
# Enhanced DXT File Manager Dependencies
gradio>=4.0.0
mcp>=0.1.0
pathlib2
typing-extensions
dataclasses; python_version<"3.7"
asyncio; python_version<"3.7"
hashlib
shutil
mimetypes
tempfile
uuid
argparse
logging
json
os
sys
time
subprocess
pathlib
EOF
    
    # Install dependencies
    pip install -r "${INSTALL_DIR}/requirements.txt"
    
    print_success "Python dependencies installed"
}

# Function to create workspace directory
create_workspace() {
    print_status "Creating workspace directory..."
    
    mkdir -p "$WORKSPACE_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "${INSTALL_DIR}/assets"
    mkdir -p "${INSTALL_DIR}/.backups"
    
    # Create sample files
    cat > "${WORKSPACE_DIR}/README.md" << EOF
# Enhanced DXT File Manager Workspace

This is your workspace directory for the Enhanced DXT File Manager.

## Features

- File and directory management
- Search functionality
- Gradio web interface
- MCP server integration
- Real-time updates
- Backup system
- Security sandboxing

## Usage

1. Web Interface: http://localhost:7860
2. MCP Endpoint: http://localhost:7860/gradio_api/mcp/sse
3. Command Line: python server/main.py --help

## Configuration

Configuration is stored in .config/config.json and can be modified through the web interface.

Enjoy managing your files with the Enhanced DXT File Manager!
EOF
    
    print_success "Workspace directory created"
}

# Function to create configuration files
create_config() {
    print_status "Creating configuration files..."
    
    # Create default configuration
    cat > "${CONFIG_DIR}/config.json" << EOF
{
  "workspace_dir": "${WORKSPACE_DIR}",
  "debug_mode": false,
  "max_file_size": 10485760,
  "log_level": "INFO",
  "theme": "system",
  "show_hidden_files": false,
  "enable_checksums": true,
  "auto_backup": true,
  "backup_dir": ".backups",
  "ui_port": 7860,
  "mcp_enabled": true
}
EOF
    
    # Create launcher script
    cat > "${INSTALL_DIR}/start.sh" << EOF
#!/bin/bash
# Enhanced DXT File Manager Launcher

cd "${INSTALL_DIR}"
source venv/bin/activate
python server/main.py "\$@"
EOF
    
    chmod +x "${INSTALL_DIR}/start.sh"
    
    # Create systemd service file (optional)
    cat > "${INSTALL_DIR}/dxt-file-manager.service" << EOF
[Unit]
Description=Enhanced DXT File Manager
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/server/main.py
Restart=always
RestartSec=10
Environment=PATH=${INSTALL_DIR}/venv/bin

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Configuration files created"
}

# Function to create desktop integration
create_desktop_integration() {
    print_status "Creating desktop integration..."
    
    # Create desktop file
    if command_exists desktop-file-install; then
        cat > "${INSTALL_DIR}/dxt-file-manager.desktop" << EOF
[Desktop Entry]
Name=Enhanced DXT File Manager
Comment=Advanced file management with Gradio UI and MCP server
Exec=${INSTALL_DIR}/start.sh
Icon=${INSTALL_DIR}/assets/icon.png
Terminal=false
Type=Application
Categories=System;FileManager;Utility;
StartupNotify=true
EOF
        
        # Install desktop file
        desktop-file-install --dir="$HOME/.local/share/applications" "${INSTALL_DIR}/dxt-file-manager.desktop" 2>/dev/null || true
    fi
    
    print_success "Desktop integration created"
}

# Function to create placeholder assets
create_assets() {
    print_status "Creating placeholder assets..."
    
    # Create placeholder icon (SVG)
    cat > "${INSTALL_DIR}/assets/icon.svg" << EOF
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" fill="#4A90E2" rx="8"/>
  <rect x="12" y="16" width="40" height="32" fill="#FFFFFF" rx="4"/>
  <rect x="16" y="20" width="32" height="4" fill="#4A90E2" rx="2"/>
  <rect x="16" y="28" width="24" height="2" fill="#4A90E2" rx="1"/>
  <rect x="16" y="32" width="20" height="2" fill="#4A90E2" rx="1"/>
  <rect x="16" y="36" width="28" height="2" fill="#4A90E2" rx="1"/>
  <rect x="16" y="40" width="16" height="2" fill="#4A90E2" rx="1"/>
</svg>
EOF
    
    # Create placeholder banner
    cat > "${INSTALL_DIR}/assets/banner.svg" << EOF
<svg width="800" height="200" viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="200" fill="#2C3E50"/>
  <text x="400" y="100" text-anchor="middle" font-family="Arial, sans-serif" font-size="36" fill="#FFFFFF">Enhanced DXT File Manager</text>
  <text x="400" y="130" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#BDC3C7">Gradio UI + MCP Server</text>
</svg>
EOF
    
    print_success "Placeholder assets created"
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check if main.py exists
    if [ ! -f "${INSTALL_DIR}/server/main.py" ]; then
        print_error "main.py not found in server/ directory"
        return 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "${INSTALL_DIR}/venv" ]; then
        print_error "Virtual environment not found"
        return 1
    fi
    
    # Check if dependencies are installed
    source "${INSTALL_DIR}/venv/bin/activate"
    
    if ! python -c "import gradio; print(f'Gradio version: {gradio.__version__}')" 2>/dev/null; then
        print_error "Gradio not properly installed"
        return 1
    fi
    
    # Test basic functionality
    if python -c "import sys; sys.path.insert(0, '${INSTALL_DIR}/server'); from main import ConfigManager; print('Configuration system working')" 2>/dev/null; then
        print_success "Basic functionality verified"
    else
        print_warning "Basic functionality test failed, but installation may still work"
    fi
    
    print_success "Installation verification completed"
}

# Function to show usage information
show_usage() {
    echo
    print_success "Enhanced DXT File Manager Installation Complete!"
    echo
    echo "Usage:"
    echo "  Web Interface:  http://localhost:7860"
    echo "  MCP Endpoint:   http://localhost:7860/gradio_api/mcp/sse"
    echo "  Start Command:  ${INSTALL_DIR}/start.sh"
    echo "  Manual Start:   cd ${INSTALL_DIR} && source venv/bin/activate && python server/main.py"
    echo
    echo "Configuration:"
    echo "  Config File:    ${CONFIG_DIR}/config.json"
    echo "  Workspace:      ${WORKSPACE_DIR}"
    echo "  Logs:           ${INSTALL_DIR}/file_manager.log"
    echo
    echo "Options:"
    echo "  --help          Show help"
    echo "  --debug         Enable debug mode"
    echo "  --port 8080     Use custom port"
    echo "  --workspace /path  Use custom workspace"
    echo "  --share         Enable Gradio sharing"
    echo
    echo "Examples:"
    echo "  ${INSTALL_DIR}/start.sh --debug --port 8080"
    echo "  ${INSTALL_DIR}/start.sh --workspace /home/user/projects"
    echo "  ${INSTALL_DIR}/start.sh --share"
    echo
    echo "For more information, see README.md"
}

# Function to cleanup on failure
cleanup() {
    print_warning "Installation interrupted. Cleaning up..."
    if [ -d "${INSTALL_DIR}/venv" ]; then
        rm -rf "${INSTALL_DIR}/venv"
    fi
    exit 1
}

# Main installation function
main() {
    echo "Enhanced DXT File Manager Installation"
    echo "======================================"
    echo
    
    # Set up error handling
    trap cleanup INT TERM
    
    # Start logging
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
    
    print_status "Starting installation at $(date)"
    print_status "Install directory: $INSTALL_DIR"
    
    # Run installation steps
    check_python_version
    check_pip
    create_venv
    install_dependencies
    create_workspace
    create_config
    create_desktop_integration
    create_assets
    verify_installation
    
    print_success "Installation completed successfully!"
    show_usage
    
    # Deactivate virtual environment
    deactivate 2>/dev/null || true
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Enhanced DXT File Manager Installation Script"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h      Show this help message"
        echo "  --force, -f     Force reinstallation"
        echo "  --quiet, -q     Quiet installation"
        echo
        exit 0
        ;;
    --force|-f)
        print_warning "Force reinstallation enabled"
        rm -rf "${INSTALL_DIR}/venv" 2>/dev/null || true
        ;;
    --quiet|-q)
        exec 1>/dev/null
        ;;
esac

# Run main installation
main "$@" 