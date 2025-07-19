#!/usr/bin/env python3

import os
import sys
import json
import hashlib
import shutil
import logging
import asyncio
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from mcp.server.fastmcp import FastMCP
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import threading
import time

# Parse command line arguments
parser = argparse.ArgumentParser(description="Enhanced File Manager MCP Server with Dual UI")
parser.add_argument(
    "--workspace", default=os.path.expanduser("~/Documents"), help="Workspace directory"
)
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
parser.add_argument("--ui-port", type=int, default=8080, help="UI server port")
parser.add_argument("--max-file-size", type=int, default=100, help="Maximum file size in MB")
parser.add_argument("--log-level", default="info", choices=["error", "warn", "info", "debug"], help="Log level")
args = parser.parse_args()

# Configure logging
log_level = getattr(logging, args.log_level.upper())
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(os.path.expanduser("~/.config/FileManagerMCP/server.log"))
    ]
)
logger = logging.getLogger(__name__)

# Initialize enhanced server
mcp = FastMCP("file-manager-python-enhanced")

# Configuration management
class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "FileManagerMCP"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self.get_default_config()
                self.save_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "workspace_directory": args.workspace,
            "debug_mode": args.debug,
            "max_file_size": args.max_file_size,
            "log_level": args.log_level,
            "theme": "auto",
            "show_hidden_files": False,
            "enable_checksums": False,
            "backup_on_delete": True,
            "ui_port": args.ui_port
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()

# Initialize configuration manager
config_manager = ConfigManager()

# Utility functions
def get_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate file checksum"""
    hash_obj = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        return ""

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def check_file_permissions(file_path: Path) -> Dict[str, bool]:
    """Check file permissions"""
    return {
        "readable": os.access(file_path, os.R_OK),
        "writable": os.access(file_path, os.W_OK),
        "executable": os.access(file_path, os.X_OK)
    }

def is_safe_path(workspace: Path, target: Path) -> bool:
    """Check if target path is within workspace (security check)"""
    try:
        workspace.resolve().relative_to(workspace.resolve())
        target.resolve().relative_to(workspace.resolve())
        return True
    except ValueError:
        return False

# Enhanced MCP Tools
@mcp.tool()
def list_files(path: str, include_hidden: bool = False, filter_pattern: str = None, include_metadata: bool = False) -> str:
    """List files in a directory with enhanced filtering and metadata"""
    try:
        path_obj = Path(path)
        workspace = Path(config_manager.get("workspace_directory"))
        
        # Security check
        if not is_safe_path(workspace, path_obj):
            return json.dumps({"error": "Access denied: Path outside workspace"})
        
        if not path_obj.exists():
            return json.dumps({"error": f"Directory not found: {path}"})

        if not path_obj.is_dir():
            return json.dumps({"error": f"Path is not a directory: {path}"})

        files = []
        for item in path_obj.iterdir():
            # Skip hidden files if not requested
            if not include_hidden and item.name.startswith('.'):
                continue
            
            # Apply filter pattern if provided
            if filter_pattern and filter_pattern not in item.name:
                continue
            
            file_info = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "path": str(item)
            }
            
            if include_metadata:
                try:
                    stat_info = item.stat()
                    file_info.update({
                        "size": stat_info.st_size,
                        "size_formatted": format_file_size(stat_info.st_size),
                        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                        "permissions": check_file_permissions(item)
                    })
                    
                    if config_manager.get("enable_checksums") and item.is_file():
                        file_info["checksum"] = get_file_checksum(item)
                
                except Exception as e:
                    logger.warning(f"Failed to get metadata for {item}: {e}")
            
            files.append(file_info)
        
        result = {
            "success": True,
            "path": path,
            "files": files,
            "total_count": len(files)
        }
        
        return json.dumps(result, indent=2)

    except PermissionError:
        return json.dumps({"error": f"Permission denied accessing: {path}"})
    except Exception as e:
        logger.error(f"Error listing directory {path}: {e}")
        return json.dumps({"error": f"Error listing directory: {str(e)}"})

@mcp.tool()
def read_file(path: str, encoding: str = "utf-8", max_size: int = None) -> str:
    """Read file contents with encoding detection and size limits"""
    try:
        path_obj = Path(path)
        workspace = Path(config_manager.get("workspace_directory"))
        
        # Security check
        if not is_safe_path(workspace, path_obj):
            return json.dumps({"error": "Access denied: Path outside workspace"})
        
        if not path_obj.exists():
            return json.dumps({"error": f"File not found: {path}"})

        if not path_obj.is_file():
            return json.dumps({"error": f"Path is not a file: {path}"})

        # Check file size limits
        file_size = path_obj.stat().st_size
        max_size_bytes = (max_size or config_manager.get("max_file_size", 100)) * 1024 * 1024
        
        if file_size > max_size_bytes:
            return json.dumps({
                "error": f"File too large: {format_file_size(file_size)} exceeds limit of {format_file_size(max_size_bytes)}"
            })

        with path_obj.open("r", encoding=encoding) as f:
            content = f.read()

        result = {
            "success": True,
            "path": path,
            "content": content,
            "size": file_size,
            "size_formatted": format_file_size(file_size),
            "encoding": encoding,
            "lines": len(content.splitlines())
        }
        
        if config_manager.get("enable_checksums"):
            result["checksum"] = get_file_checksum(path_obj)
        
        return json.dumps(result, indent=2)

    except UnicodeDecodeError:
        return json.dumps({"error": f"File is not text or uses unsupported encoding: {path}"})
    except PermissionError:
        return json.dumps({"error": f"Permission denied reading: {path}"})
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return json.dumps({"error": f"Error reading file: {str(e)}"})

@mcp.tool()
def get_file_info(path: str, include_permissions: bool = True, include_checksums: bool = False) -> str:
    """Get comprehensive information about a file or directory"""
    try:
        path_obj = Path(path)
        workspace = Path(config_manager.get("workspace_directory"))
        
        # Security check
        if not is_safe_path(workspace, path_obj):
            return json.dumps({"error": "Access denied: Path outside workspace"})
        
        if not path_obj.exists():
            return json.dumps({"error": f"Path not found: {path}"})

        stat_info = path_obj.stat()
        file_type = "directory" if path_obj.is_dir() else "file"

        result = {
            "success": True,
            "path": path,
            "name": path_obj.name,
            "type": file_type,
            "size": stat_info.st_size,
            "size_formatted": format_file_size(stat_info.st_size),
            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat()
        }
        
        if include_permissions:
            result["permissions"] = check_file_permissions(path_obj)
        
        if include_checksums and path_obj.is_file():
            result["checksums"] = {
                "sha256": get_file_checksum(path_obj, "sha256"),
                "md5": get_file_checksum(path_obj, "md5")
            }
        
        return json.dumps(result, indent=2)

    except PermissionError:
        return json.dumps({"error": f"Permission denied accessing: {path}"})
    except Exception as e:
        logger.error(f"Error getting file info for {path}: {e}")
        return json.dumps({"error": f"Error getting file info: {str(e)}"})

@mcp.tool()
def create_directory(path: str, parents: bool = True, permissions: str = "755") -> str:
    """Create a new directory with proper permissions"""
    try:
        path_obj = Path(path)
        workspace = Path(config_manager.get("workspace_directory"))
        
        # Security check
        if not is_safe_path(workspace, path_obj):
            return json.dumps({"error": "Access denied: Path outside workspace"})
        
        if path_obj.exists():
            return json.dumps({"error": f"Directory already exists: {path}"})
        
        path_obj.mkdir(parents=parents, exist_ok=False)
        
        # Set permissions if specified
        if permissions:
            os.chmod(path_obj, int(permissions, 8))
        
        result = {
            "success": True,
            "path": path,
            "created": True,
            "permissions": permissions
        }
        
        return json.dumps(result, indent=2)

    except PermissionError:
        return json.dumps({"error": f"Permission denied creating directory: {path}"})
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return json.dumps({"error": f"Error creating directory: {str(e)}"})

@mcp.tool()
def delete_file(path: str, recursive: bool = False, confirm: bool = False) -> str:
    """Safely delete a file or directory"""
    try:
        path_obj = Path(path)
        workspace = Path(config_manager.get("workspace_directory"))
        
        # Security check
        if not is_safe_path(workspace, path_obj):
            return json.dumps({"error": "Access denied: Path outside workspace"})
        
        if not path_obj.exists():
            return json.dumps({"error": f"Path not found: {path}"})
        
        if not confirm:
            return json.dumps({
                "error": "Deletion requires confirmation. Set confirm=true to proceed.",
                "path": path,
                "type": "directory" if path_obj.is_dir() else "file"
            })
        
        # Create backup if enabled
        if config_manager.get("backup_on_delete", True):
            backup_dir = workspace / ".backups"
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / f"{path_obj.name}.{int(time.time())}.bak"
            
            if path_obj.is_file():
                shutil.copy2(path_obj, backup_path)
            else:
                shutil.copytree(path_obj, backup_path)
            
            logger.info(f"Created backup at {backup_path}")
        
        # Delete the file/directory
        if path_obj.is_file():
            path_obj.unlink()
        elif path_obj.is_dir():
            if recursive:
                shutil.rmtree(path_obj)
            else:
                path_obj.rmdir()
        
        result = {
            "success": True,
            "path": path,
            "deleted": True,
            "backup_created": config_manager.get("backup_on_delete", True)
        }
        
        return json.dumps(result, indent=2)

    except PermissionError:
        return json.dumps({"error": f"Permission denied deleting: {path}"})
    except OSError as e:
        return json.dumps({"error": f"OS error deleting {path}: {str(e)}"})
    except Exception as e:
        logger.error(f"Error deleting {path}: {e}")
        return json.dumps({"error": f"Error deleting: {str(e)}"})

@mcp.tool()
def copy_file(source: str, destination: str, overwrite: bool = False, preserve_metadata: bool = True) -> str:
    """Copy files or directories with progress tracking"""
    try:
        source_obj = Path(source)
        dest_obj = Path(destination)
        workspace = Path(config_manager.get("workspace_directory"))
        
        # Security checks
        if not is_safe_path(workspace, source_obj) or not is_safe_path(workspace, dest_obj):
            return json.dumps({"error": "Access denied: Path outside workspace"})
        
        if not source_obj.exists():
            return json.dumps({"error": f"Source not found: {source}"})
        
        if dest_obj.exists() and not overwrite:
            return json.dumps({"error": f"Destination exists and overwrite=false: {destination}"})
        
        # Perform copy operation
        if source_obj.is_file():
            if preserve_metadata:
                shutil.copy2(source_obj, dest_obj)
            else:
                shutil.copy(source_obj, dest_obj)
        else:
            if dest_obj.exists():
                shutil.rmtree(dest_obj)
            shutil.copytree(source_obj, dest_obj)
        
        result = {
            "success": True,
            "source": source,
            "destination": destination,
            "copied": True,
            "preserve_metadata": preserve_metadata
        }
        
        return json.dumps(result, indent=2)

    except PermissionError:
        return json.dumps({"error": f"Permission denied copying from {source} to {destination}"})
    except Exception as e:
        logger.error(f"Error copying {source} to {destination}: {e}")
        return json.dumps({"error": f"Error copying: {str(e)}"})

@mcp.tool()
def move_file(source: str, destination: str, overwrite: bool = False) -> str:
    """Move or rename files and directories"""
    try:
        source_obj = Path(source)
        dest_obj = Path(destination)
        workspace = Path(config_manager.get("workspace_directory"))
        
        # Security checks
        if not is_safe_path(workspace, source_obj) or not is_safe_path(workspace, dest_obj):
            return json.dumps({"error": "Access denied: Path outside workspace"})
        
        if not source_obj.exists():
            return json.dumps({"error": f"Source not found: {source}"})
        
        if dest_obj.exists() and not overwrite:
            return json.dumps({"error": f"Destination exists and overwrite=false: {destination}"})
        
        # Perform move operation
        if dest_obj.exists():
            if dest_obj.is_dir():
                shutil.rmtree(dest_obj)
            else:
                dest_obj.unlink()
        
        shutil.move(str(source_obj), str(dest_obj))
        
        result = {
            "success": True,
            "source": source,
            "destination": destination,
            "moved": True
        }
        
        return json.dumps(result, indent=2)

    except PermissionError:
        return json.dumps({"error": f"Permission denied moving from {source} to {destination}"})
    except Exception as e:
        logger.error(f"Error moving {source} to {destination}: {e}")
        return json.dumps({"error": f"Error moving: {str(e)}"})

@mcp.tool()
def search_files(path: str, pattern: str, content_search: bool = False, case_sensitive: bool = False) -> str:
    """Search for files using various criteria"""
    try:
        path_obj = Path(path)
        workspace = Path(config_manager.get("workspace_directory"))
        
        # Security check
        if not is_safe_path(workspace, path_obj):
            return json.dumps({"error": "Access denied: Path outside workspace"})
        
        if not path_obj.exists():
            return json.dumps({"error": f"Search path not found: {path}"})
        
        results = []
        search_pattern = pattern if case_sensitive else pattern.lower()
        
        for item in path_obj.rglob("*"):
            if item.is_file():
                # Check filename match
                filename = item.name if case_sensitive else item.name.lower()
                filename_match = search_pattern in filename
                
                content_match = False
                if content_search:
                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if not case_sensitive:
                                content = content.lower()
                            content_match = search_pattern in content
                    except (UnicodeDecodeError, PermissionError):
                        pass
                
                if filename_match or content_match:
                    results.append({
                        "path": str(item),
                        "name": item.name,
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        "filename_match": filename_match,
                        "content_match": content_match
                    })
        
        result = {
            "success": True,
            "search_path": path,
            "pattern": pattern,
            "content_search": content_search,
            "case_sensitive": case_sensitive,
            "results": results,
            "total_matches": len(results)
        }
        
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error searching files in {path}: {e}")
        return json.dumps({"error": f"Error searching files: {str(e)}"})

# Configuration tools
@mcp.tool()
def get_config() -> str:
    """Get current configuration"""
    return json.dumps(config_manager.config, indent=2)

@mcp.tool()
def set_config(key: str, value: str) -> str:
    """Set configuration value"""
    try:
        # Parse JSON value if it looks like JSON
        if value.startswith('{') or value.startswith('[') or value in ['true', 'false', 'null']:
            value = json.loads(value)
        
        config_manager.set(key, value)
        
        result = {
            "success": True,
            "key": key,
            "value": value,
            "message": "Configuration updated"
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        logger.error(f"Error setting config {key}={value}: {e}")
        return json.dumps({"error": f"Error setting configuration: {str(e)}"})

# **CRITICAL FIX: Simplified Dual UI Server - No WebSocket Blocking**
class DualUIServer:
    def __init__(self, port: int):
        self.port = port
        self.server = None
        self.server_thread = None
        self._running = False
    
    def start(self):
        """Start the simplified dual UI server"""
        try:
            # Check if port is already in use
            if self._check_port_in_use():
                logger.warning(f"Port {self.port} is already in use, attempting to use different port")
                # Try alternative port
                self.port = self._find_available_port(self.port)
            
            self._running = True
            
            # Start HTTP server for static files only
            self.server_thread = Thread(target=self._run_http_server)
            self.server_thread.daemon = False  # **CRITICAL FIX: Non-daemon thread to keep process alive**
            self.server_thread.start()
            
            logger.info(f"Dual UI server started on port {self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start dual UI server: {e}")
    
    def _check_port_in_use(self) -> bool:
        """Check if the required port is already in use"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", self.port))
            return False
        except OSError:
            return True
    
    def _find_available_port(self, start_port: int) -> int:
        """Find an available port starting from start_port"""
        import socket
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                logger.info(f"Found available port: HTTP={port}")
                return port
            except OSError:
                continue
        logger.error("No available ports found in range")
        return start_port  # Fallback to original port
    
    def _run_http_server(self):
        """Run HTTP server for static files"""
        try:
            handler = SimpleHTTPRequestHandler
            self.server = HTTPServer(("localhost", self.port), handler)
            while self._running:
                self.server.handle_request()
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
    
    def stop(self):
        """Stop the dual UI server"""
        self._running = False
        
        if self.server:
            try:
                self.server.shutdown()
            except:
                pass
        
        # Wait for thread to finish
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2)

# Initialize dual UI server
ui_server = DualUIServer(args.ui_port)

# Main execution
if __name__ == "__main__":
    # Debug output if enabled
    if args.debug:
        logger.info("Starting Enhanced File Manager MCP Server with Dual UI...")
        logger.info(f"Workspace: {args.workspace}")
        logger.info(f"UI Port: {args.ui_port}")
        logger.info(f"Max File Size: {args.max_file_size}MB")
        logger.info(f"Log Level: {args.log_level}")
    
    # Start dual UI server
    ui_server.start()
    
    # **CRITICAL FIX: Run the MCP server properly to keep it running**
    try:
        logger.info("Starting MCP server...")
        
        # **CRITICAL FIX: Add proper signal handling and process management**
        import signal
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            ui_server.stop()
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # **CRITICAL FIX: Run MCP server in a way that keeps the process alive**
        logger.info("MCP server starting, process will stay alive...")
        
        # **CRITICAL FIX: Simple and reliable MCP server execution**
        logger.info("Starting MCP server in main thread...")
        
        # Use FastMCP's built-in run method which should block forever
        # This is the correct way to run a FastMCP server
        # The dual UI server threads will keep the process alive
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        ui_server.stop()
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        ui_server.stop()
        sys.exit(1)
