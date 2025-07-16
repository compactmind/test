# Enhanced Python File Manager MCP - DXT Integration

This is an Desktop Extension (DXT) implementation of a Python-based MCP (Model Context Protocol) server that provides comprehensive file management capabilities with interface.

## Features

### Core File Operations
- **List Files**: Enhanced directory listing with metadata, filtering, and hidden file support
- **Read Files**: Read file contents with encoding detection and size limits
- **File Information**: Comprehensive file/directory information with permissions and checksums
- **Create Directory**: Create directories with proper permissions
- **Delete Files**: Safe deletion with backup support
- **Copy/Move Files**: File operations with progress tracking
- **Search Files**: Advanced search with content search and regex support

### Enhanced DXT Features
- **Theme Support**: Dark/light/auto themes with system preference detection
- **Real-time Updates**: WebSocket-based real-time file system monitoring
- **Security**: Sandboxed operations with capability-based permissions
- **Configuration**: Persistent user configuration with validation

### Security & Permissions
- **Workspace Isolation**: All operations restricted to user-defined workspace
- **Path Validation**: Security checks to prevent directory traversal
- **Capability System**: Detailed permission declarations for all operations
- **Backup System**: Automatic backups before destructive operations
- **Audit Logging**: Comprehensive logging of all file operations

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js (for development)
- FastMCP library (`pip install fastmcp`)
- WebSocket support (`pip install websockets`)

### Setup
1. Install Python dependencies:
```bash
pip install fastmcp websockets
```

2. Configure the workspace directory and other settings in the manifest.json

3. Run the enhanced server:
```bash
python server/main.py --workspace=/path/to/workspace --ui-port=8080
```

## Configuration

### User Configuration Options
- **Workspace Directory**: Primary directory for file operations
- **Debug Mode**: Enable verbose logging and debug features
- **Max File Size**: Maximum file size limit (MB)
- **Log Level**: Logging verbosity (error, warn, info, debug)
- **Theme**: UI theme (auto, dark, light)
- **Show Hidden Files**: Display hidden files and directories
- **Enable Checksums**: Calculate and display file checksums
- **Backup on Delete**: Create backups when deleting files

### Environment Variables
- `WORKSPACE_PATH`: Default workspace directory
- `UI_PORT`: Port for UI
- `MCP_PORT`: Port for MCP communication
- `LOG_LEVEL`: Logging level
- `MAX_FILE_SIZE`: Maximum file size limit

## Interface
- **Responsive Design**: Adapts to different screen sizes
- **Keyboard Navigation**: Full keyboard support for accessibility

### UI Components
- **File Browser**: Grid-based file listing with metadata
- **Search Interface**: Advanced search with content search
- **Settings Panel**: User configuration interface
- **Context Menus**: Right-click operations
- **Notifications**: Real-time operation feedback

### Themes
- **Dark Theme**: Modern dark interface with blue accents
- **Light Theme**: Clean light interface with Google-inspired colors
- **Auto Theme**: Automatically follows system preference

## MCP Tools

### File Operations
- `list_files(path, include_hidden, filter_pattern, include_metadata)`
- `read_file(path, encoding, max_size)`
- `get_file_info(path, include_permissions, include_checksums)`
- `create_directory(path, parents, permissions)`
- `delete_file(path, recursive, confirm)`
- `copy_file(source, destination, overwrite, preserve_metadata)`
- `move_file(source, destination, overwrite)`
- `search_files(path, pattern, content_search, case_sensitive)`

### Configuration
- `get_config()`: Get current configuration
- `set_config(key, value)`: Set configuration value

## Security Model

### Capabilities
- **File System Access**: Limited to workspace directory
- **Network Access**: Localhost-only for UI server
- **System Integration**: Notifications and clipboard access
- **Cryptography**: File checksums and configuration encryption

### Sandboxing
- **Strict Mode**: All operations are sandboxed
- **Capability Enforcement**: Operations validated against declared capabilities
- **Path Validation**: Prevents access outside workspace

## Development

### Project Structure
```
test/
├── server/
│   ├── main.py           # Enhanced MCP server
│   └── lib/              # Server libraries
├── ui/
│   ├── index.html        # Main UI interface
│   ├── app.js            # JavaScript application
│   ├── themes/
│   │   ├── dark.css      # Dark theme
│   │   └── light.css     # Light theme
│   └── dist/             # Built assets
├── assets/
│   ├── icon.png          # Application icon
│   └── screenshots/      # UI screenshots
└── manifest.json         # Enhanced DXT manifest
```

### API Endpoints
- `GET /`: Main UI interface
- `POST /api/mcp`: MCP tool execution
- `WebSocket /ws`: Real-time communication

### WebSocket Events
- `file_changed`: File system change notification
- `operation_progress`: Operation progress updates
- `notification`: User notifications

## Usage Examples

### Basic File Operations
```python
# List files with metadata
result = await mcp.call_tool("list_files", {
    "path": "/workspace",
    "include_metadata": True,
    "include_hidden": False
})

# Read file with size limit
result = await mcp.call_tool("read_file", {
    "path": "/workspace/document.txt",
    "max_size": 50
})

# Create directory
result = await mcp.call_tool("create_directory", {
    "path": "/workspace/new_folder",
    "parents": True
})
```

### Advanced Search
```python
# Search files with content search
result = await mcp.call_tool("search_files", {
    "path": "/workspace",
    "pattern": "TODO",
    "content_search": True,
    "case_sensitive": False
})
```

### Configuration Management
```python
# Get current configuration
config = await mcp.call_tool("get_config")

# Update configuration
await mcp.call_tool("set_config", {
    "key": "theme",
    "value": "dark"
})
```

## Troubleshooting

### Common Issues

1. **Server won't start**: Check Python dependencies and port availability
2. **UI not loading**: Verify UI port is not blocked by firewall
3. **WebSocket connection failed**: Check WebSocket port (UI_PORT + 1)
4. **File operations fail**: Verify workspace directory permissions

### Debug Mode
Enable debug mode for detailed logging:
```bash
python server/main.py --debug --log-level=debug
```

### Log Files
- Server logs: `~/.config/FileManagerMCP/server.log`
- Browser console: Use developer tools for UI debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Project Issues](https://github.com/anthropics/file-manager-python-mcp/issues)
- Documentation: [Project Wiki](https://github.com/anthropics/file-manager-python-mcp/wiki)
- Email: support@anthropic.com
