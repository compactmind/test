# Enhanced DXT File Manager

A powerful file management system with **Gradio UI** and **MCP server** capabilities, designed for seamless integration with overlay systems and chat agents.

## 🚀 Features

### Dual Interface System
- **Web Interface**: Modern Gradio-based UI accessible at `http://localhost:7860`
- **MCP Server**: Streaming endpoint at `http://localhost:7860/gradio_api/mcp/sse`
- **Overlay Integration**: Compatible with overlay systems via hotkeys (Ctrl+Shift+F)
- **Chat Agent Integration**: Streaming results to chat agent text UI

### File Management Capabilities
- **Comprehensive File Operations**: List, read, write, copy, move, delete
- **Directory Management**: Create, navigate, and manage directories
- **Advanced Search**: Search by filename and content with file type filtering
- **Real-time Updates**: Live file system monitoring and UI updates
- **Backup System**: Automatic backups before destructive operations
- **Security**: Sandboxed operations within workspace directory

### Enhanced Features
- **Gradio Integration**: Modern, responsive web interface
- **MCP Protocol**: Full MCP server implementation for agent integration
- **Configuration Management**: Persistent settings with web-based configuration
- **Accessibility**: Keyboard navigation and screen reader support
- **Themes**: Light, dark, and system theme options
- **File Checksums**: SHA256 checksums for integrity verification
- **Drag & Drop**: Modern file handling with drag-and-drop support

## 📦 Installation

### Quick Install
```bash
# Make the installation script executable
chmod +x install.sh

# Run the installation
./install.sh
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install gradio>=4.0.0 mcp>=0.1.0

# Start the server
python server/main.py
```

### Requirements
- Python 3.8 or higher
- pip3
- 50MB disk space
- Internet connection for initial setup

## 🎯 Usage

### Web Interface
Access the modern Gradio interface:
```
http://localhost:7860
```

### MCP Server Endpoint
For agent integration:
```
http://localhost:7860/gradio_api/mcp/sse
```

### Command Line
```bash
# Basic usage
./start.sh

# Custom workspace
./start.sh --workspace /path/to/workspace

# Debug mode
./start.sh --debug --log-level DEBUG

# Custom port
./start.sh --port 8080

# Enable sharing
./start.sh --share
```

## 🔧 Configuration

### Configuration File
Settings are stored in `.config/config.json`:
```json
{
  "workspace_dir": "./workspace",
  "debug_mode": false,
  "max_file_size": 10485760,
  "log_level": "INFO",
  "theme": "system",
  "show_hidden_files": false,
  "enable_checksums": true,
  "auto_backup": true,
  "ui_port": 7860,
  "mcp_enabled": true
}
```

### Web Configuration
Access configuration through the web interface:
1. Open `http://localhost:7860`
2. Navigate to the "Configuration" tab
3. Modify settings as needed
4. Click "Update Config" to save

## 🔌 MCP Integration

### Available Tools
The MCP server exposes these tools for agent integration:

1. **list_files** - List files and directories
2. **read_file** - Read file contents
3. **write_file** - Write content to files
4. **delete_file** - Delete files or directories
5. **copy_file** - Copy files or directories
6. **move_file** - Move files or directories
7. **create_directory** - Create new directories
8. **search_files** - Search for files
9. **get_file_info** - Get detailed file information
10. **get_config** - Get current configuration
11. **update_config** - Update configuration settings

### MCP Client Configuration
For Claude Desktop or similar MCP clients:
```json
{
  "mcpServers": {
    "dxt-file-manager": {
      "command": "python",
      "args": ["/path/to/enhanced-dxt-file-manager/server/main.py"],
      "env": {
        "WORKSPACE_DIR": "/path/to/workspace"
      }
    }
  }
}
```

## 🎨 Overlay System Integration

### Hotkey Configuration
- **Default Hotkey**: Ctrl+Shift+F (Cmd+Shift+F on macOS)
- **Position**: Center screen
- **Size**: 900x700 (resizable)
- **Features**: Draggable, resizable, minimizable

### Overlay Features
- **Real-time Sync**: Changes sync with chat agent
- **Context Awareness**: Integrates with current workspace
- **Streaming Updates**: Live updates to overlay interface
- **Chat Integration**: Results stream to chat agent text UI

## 🔒 Security

### Sandboxing
- All file operations are restricted to the configured workspace directory
- Path validation prevents directory traversal attacks
- Input sanitization for all user inputs
- File size limits to prevent resource exhaustion

### Audit Logging
- All file operations are logged
- Configurable log levels
- Audit trail for security monitoring
- Error tracking and reporting

## 🎛️ Advanced Features

### Gradio Integration
- **Modern UI**: Responsive, accessible interface
- **Real-time Updates**: Live file system monitoring
- **Multiple Tabs**: Organized functionality
- **Theme Support**: Light, dark, and system themes
- **Accessibility**: Keyboard navigation and screen reader support

### Performance Optimization
- **Streaming**: Efficient data transfer
- **Caching**: Smart caching for better performance
- **Async Operations**: Non-blocking file operations
- **Memory Management**: Efficient resource usage

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=server tests/

# Run specific test category
python -m pytest tests/unit/
```

### Integration Tests
```bash
# Test MCP integration
python -m pytest tests/integration/

# Test Gradio interface
python -m pytest tests/gradio/
```

## 🔧 Development

### Project Structure
```
enhanced-dxt-file-manager/
├── server/
│   └── main.py              # Gradio + MCP server
├── .config/
│   └── config.json          # Configuration
├── workspace/               # Default workspace
├── assets/                  # Icons and graphics
├── venv/                    # Virtual environment
├── install.sh              # Installation script
├── start.sh                # Launch script
└── README.md               # This file
```

### Development Setup
```bash
# Clone and setup
git clone <repository>
cd enhanced-dxt-file-manager

# Create development environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e .
pip install pytest pytest-cov

# Run in development mode
python server/main.py --debug --port 7860
```

## 📊 Monitoring

### Health Checks
- **Endpoint**: `/health`
- **Status**: Real-time system status
- **Metrics**: Performance metrics
- **Logs**: Access to system logs

### Performance Metrics
- **Memory Usage**: < 100MB
- **CPU Usage**: < 5%
- **Network**: < 1MB/s
- **Startup Time**: < 3 seconds

## 🤝 Integration Examples

### Chat Agent Integration
```python
# Example MCP client integration
import gradio_client

client = gradio_client.Client("http://localhost:7860")

# List files
result = client.predict(
    directory=".",
    show_hidden=False,
    file_type="all",
    api_name="/list_files"
)

# Read file
content = client.predict(
    file_path="example.txt",
    encoding="utf-8",
    api_name="/read_file"
)
```

### Overlay System Integration
```javascript
// Example overlay integration
const ws = new WebSocket('ws://localhost:7860/gradio_api/mcp/sse');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    // Handle streaming updates
    updateChatUI(data);
};

// Send file operation
ws.send(JSON.stringify({
    tool: 'list_files',
    arguments: {
        directory: '.',
        show_hidden: false
    }
}));
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Use different port
   ./start.sh --port 8080
   ```

2. **Permission Denied**
   ```bash
   # Check workspace permissions
   chmod -R 755 workspace/
   ```

3. **Gradio Not Found**
   ```bash
   # Reinstall dependencies
   pip install --upgrade gradio>=4.0.0
   ```

4. **MCP Connection Failed**
   ```bash
   # Check MCP endpoint
   curl -s http://localhost:7860/gradio_api/mcp/sse
   ```

### Debug Mode
```bash
# Enable debug mode
./start.sh --debug --log-level DEBUG

# Check logs
tail -f file_manager.log
```

## 📚 API Reference

### MCP Tools

#### list_files
```python
def list_files(directory=".", show_hidden=False, file_type="all"):
    """List files and directories in the specified directory."""
```

#### read_file
```python
def read_file(file_path, encoding="utf-8"):
    """Read the contents of a file."""
```

#### write_file
```python
def write_file(file_path, content, encoding="utf-8", create_backup=True):
    """Write content to a file."""
```

### Configuration API

#### get_config
```python
def get_config():
    """Get current configuration settings."""
```

#### update_config
```python
def update_config(**kwargs):
    """Update configuration settings."""
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

- **Documentation**: This README
- **Issues**: GitHub Issues
- **Community**: Discord Server
- **Email**: support@compactmind.com

---

**Enhanced DXT File Manager** - Bridging the gap between traditional file management and modern agent-based workflows.