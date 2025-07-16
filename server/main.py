#!/usr/bin/env python3
"""
Enhanced DXT File Manager MCP Server with Gradio
Provides both web UI and MCP server endpoints for file operations
"""

import gradio as gr
import json
import os
import shutil
import hashlib
import logging
import argparse
import sys
import time
import mimetypes
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import tempfile
import asyncio
import uuid

# Configuration management
@dataclass
class Config:
    workspace_dir: str = "."
    debug_mode: bool = False
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    log_level: str = "INFO"
    theme: str = "system"
    show_hidden_files: bool = False
    enable_checksums: bool = True
    auto_backup: bool = True
    backup_dir: str = ".backups"
    ui_port: int = 7860
    mcp_enabled: bool = True

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Config:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                return Config(**data)
            except Exception as e:
                logging.warning(f"Failed to load config: {e}, using defaults")
        return Config()
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
    
    def update_config(self, **kwargs) -> Dict[str, Any]:
        """Update configuration with new values"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()
        return asdict(self.config)

# Global configuration manager
config_manager = ConfigManager()

# Security utilities
def is_safe_path(path: str, workspace: str) -> bool:
    """Check if path is within workspace directory"""
    try:
        workspace_path = Path(workspace).resolve()
        target_path = Path(path).resolve()
        return target_path.is_relative_to(workspace_path)
    except Exception:
        return False

def get_safe_path(path: str, workspace: str) -> Path:
    """Get safe path within workspace"""
    if not is_safe_path(path, workspace):
        raise ValueError(f"Path {path} is outside workspace {workspace}")
    return Path(path).resolve()

def create_backup(file_path: str) -> Optional[str]:
    """Create backup of file before modification"""
    if not config_manager.config.auto_backup:
        return None
    
    try:
        backup_dir = Path(config_manager.config.backup_dir)
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = int(time.time())
        backup_name = f"{Path(file_path).name}_{timestamp}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        return str(backup_path)
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return None

def calculate_checksum(file_path: str) -> Optional[str]:
    """Calculate SHA256 checksum of file"""
    if not config_manager.config.enable_checksums:
        return None
    
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

# File operation functions for Gradio/MCP
def list_files(directory: str = ".", show_hidden: bool = False, file_type: str = "all") -> List[Dict[str, Any]]:
    """
    List files and directories in the specified directory.
    
    Args:
        directory: The directory path to list (default: current directory)
        show_hidden: Whether to show hidden files (default: False)
        file_type: Filter by file type: 'all', 'files', 'directories' (default: 'all')
    
    Returns:
        List of file/directory information dictionaries
    """
    try:
        workspace = config_manager.config.workspace_dir
        safe_path = get_safe_path(directory, workspace)
        
        if not safe_path.exists():
            return [{"error": f"Directory {directory} does not exist"}]
        
        if not safe_path.is_dir():
            return [{"error": f"{directory} is not a directory"}]
        
        items = []
        for item in safe_path.iterdir():
            if not show_hidden and item.name.startswith('.'):
                continue
                
            item_info = {
                "name": item.name,
                "path": str(item.relative_to(Path(workspace))),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": item.stat().st_mtime,
                "permissions": oct(item.stat().st_mode)[-3:],
                "checksum": calculate_checksum(str(item)) if item.is_file() else None
            }
            
            if file_type == "all" or \
               (file_type == "files" and item.is_file()) or \
               (file_type == "directories" and item.is_dir()):
                items.append(item_info)
        
        return sorted(items, key=lambda x: (x["type"], x["name"]))
        
    except Exception as e:
        logging.error(f"Error listing files: {e}")
        return [{"error": str(e)}]

def read_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        encoding: Text encoding to use (default: utf-8)
    
    Returns:
        Dictionary containing file content and metadata
    """
    try:
        workspace = config_manager.config.workspace_dir
        safe_path = get_safe_path(file_path, workspace)
        
        if not safe_path.exists():
            return {"error": f"File {file_path} does not exist"}
        
        if not safe_path.is_file():
            return {"error": f"{file_path} is not a file"}
        
        file_size = safe_path.stat().st_size
        if file_size > config_manager.config.max_file_size:
            return {"error": f"File too large ({file_size} bytes > {config_manager.config.max_file_size} bytes)"}
        
        # Detect encoding if not specified
        if encoding == "auto":
            try:
                with open(safe_path, 'rb') as f:
                    raw_data = f.read(1024)
                    encoding = 'utf-8'  # Default fallback
            except Exception:
                encoding = 'utf-8'
        
        with open(safe_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        return {
            "content": content,
            "size": file_size,
            "encoding": encoding,
            "checksum": calculate_checksum(str(safe_path)),
            "mime_type": mimetypes.guess_type(str(safe_path))[0],
            "modified": safe_path.stat().st_mtime
        }
        
    except UnicodeDecodeError:
        return {"error": f"Unable to decode file with {encoding} encoding"}
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return {"error": str(e)}

def write_file(file_path: str, content: str, encoding: str = "utf-8", create_backup: bool = True) -> Dict[str, Any]:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        encoding: Text encoding to use (default: utf-8)
        create_backup: Whether to create a backup if file exists (default: True)
    
    Returns:
        Dictionary containing operation result and metadata
    """
    try:
        workspace = config_manager.config.workspace_dir
        safe_path = get_safe_path(file_path, workspace)
        
        # Create backup if file exists
        backup_path = None
        if safe_path.exists() and create_backup:
            backup_path = create_backup(str(safe_path))
        
        # Create parent directories if they don't exist
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(safe_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return {
            "success": True,
            "path": str(safe_path.relative_to(Path(workspace))),
            "size": len(content.encode(encoding)),
            "encoding": encoding,
            "backup_path": backup_path,
            "checksum": calculate_checksum(str(safe_path))
        }
        
    except Exception as e:
        logging.error(f"Error writing file: {e}")
        return {"error": str(e)}

def delete_file(file_path: str, create_backup: bool = True) -> Dict[str, Any]:
    """
    Delete a file or directory.
    
    Args:
        file_path: Path to the file or directory to delete
        create_backup: Whether to create a backup before deletion (default: True)
    
    Returns:
        Dictionary containing operation result
    """
    try:
        workspace = config_manager.config.workspace_dir
        safe_path = get_safe_path(file_path, workspace)
        
        if not safe_path.exists():
            return {"error": f"Path {file_path} does not exist"}
        
        # Create backup if requested and it's a file
        backup_path = None
        if safe_path.is_file() and create_backup:
            backup_path = create_backup(str(safe_path))
        
        if safe_path.is_dir():
            shutil.rmtree(safe_path)
        else:
            safe_path.unlink()
        
        return {
            "success": True,
            "path": str(safe_path.relative_to(Path(workspace))),
            "backup_path": backup_path,
            "type": "directory" if safe_path.is_dir() else "file"
        }
        
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        return {"error": str(e)}

def copy_file(source_path: str, destination_path: str, overwrite: bool = False) -> Dict[str, Any]:
    """
    Copy a file or directory.
    
    Args:
        source_path: Path to the source file or directory
        destination_path: Path to the destination
        overwrite: Whether to overwrite existing files (default: False)
    
    Returns:
        Dictionary containing operation result
    """
    try:
        workspace = config_manager.config.workspace_dir
        safe_source = get_safe_path(source_path, workspace)
        safe_dest = get_safe_path(destination_path, workspace)
        
        if not safe_source.exists():
            return {"error": f"Source {source_path} does not exist"}
        
        if safe_dest.exists() and not overwrite:
            return {"error": f"Destination {destination_path} already exists"}
        
        if safe_source.is_dir():
            shutil.copytree(safe_source, safe_dest, dirs_exist_ok=overwrite)
        else:
            safe_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(safe_source, safe_dest)
        
        return {
            "success": True,
            "source": str(safe_source.relative_to(Path(workspace))),
            "destination": str(safe_dest.relative_to(Path(workspace))),
            "type": "directory" if safe_source.is_dir() else "file",
            "size": safe_source.stat().st_size if safe_source.is_file() else 0
        }
        
    except Exception as e:
        logging.error(f"Error copying file: {e}")
        return {"error": str(e)}

def move_file(source_path: str, destination_path: str, overwrite: bool = False) -> Dict[str, Any]:
    """
    Move a file or directory.
    
    Args:
        source_path: Path to the source file or directory
        destination_path: Path to the destination
        overwrite: Whether to overwrite existing files (default: False)
    
    Returns:
        Dictionary containing operation result
    """
    try:
        workspace = config_manager.config.workspace_dir
        safe_source = get_safe_path(source_path, workspace)
        safe_dest = get_safe_path(destination_path, workspace)
        
        if not safe_source.exists():
            return {"error": f"Source {source_path} does not exist"}
        
        if safe_dest.exists() and not overwrite:
            return {"error": f"Destination {destination_path} already exists"}
        
        shutil.move(str(safe_source), str(safe_dest))
        
        return {
            "success": True,
            "source": source_path,
            "destination": str(safe_dest.relative_to(Path(workspace))),
            "type": "directory" if safe_dest.is_dir() else "file"
        }
        
    except Exception as e:
        logging.error(f"Error moving file: {e}")
        return {"error": str(e)}

def create_directory(directory_path: str, create_parents: bool = True) -> Dict[str, Any]:
    """
    Create a new directory.
    
    Args:
        directory_path: Path of the directory to create
        create_parents: Whether to create parent directories if they don't exist (default: True)
    
    Returns:
        Dictionary containing operation result
    """
    try:
        workspace = config_manager.config.workspace_dir
        safe_path = get_safe_path(directory_path, workspace)
        
        if safe_path.exists():
            return {"error": f"Directory {directory_path} already exists"}
        
        safe_path.mkdir(parents=create_parents, exist_ok=False)
        
        return {
            "success": True,
            "path": str(safe_path.relative_to(Path(workspace))),
            "created": True
        }
        
    except Exception as e:
        logging.error(f"Error creating directory: {e}")
        return {"error": str(e)}

def search_files(query: str, directory: str = ".", search_content: bool = False, file_extensions: str = "") -> List[Dict[str, Any]]:
    """
    Search for files by name and optionally content.
    
    Args:
        query: Search query string
        directory: Directory to search in (default: current directory)
        search_content: Whether to search file contents (default: False)
        file_extensions: Comma-separated list of file extensions to filter (default: all)
    
    Returns:
        List of matching files with metadata
    """
    try:
        workspace = config_manager.config.workspace_dir
        safe_path = get_safe_path(directory, workspace)
        
        if not safe_path.exists() or not safe_path.is_dir():
            return [{"error": f"Directory {directory} does not exist"}]
        
        extensions = [ext.strip().lower() for ext in file_extensions.split(",") if ext.strip()]
        results = []
        
        for item in safe_path.rglob("*"):
            if item.is_file():
                # Filter by extension if specified
                if extensions and item.suffix.lower() not in extensions:
                    continue
                
                # Search filename
                if query.lower() in item.name.lower():
                    results.append({
                        "path": str(item.relative_to(Path(workspace))),
                        "name": item.name,
                        "size": item.stat().st_size,
                        "modified": item.stat().st_mtime,
                        "match_type": "filename",
                        "checksum": calculate_checksum(str(item))
                    })
                # Search content if requested
                elif search_content and item.stat().st_size < config_manager.config.max_file_size:
                    try:
                        with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                results.append({
                                    "path": str(item.relative_to(Path(workspace))),
                                    "name": item.name,
                                    "size": item.stat().st_size,
                                    "modified": item.stat().st_mtime,
                                    "match_type": "content",
                                    "checksum": calculate_checksum(str(item))
                                })
                    except Exception:
                        continue
        
        return sorted(results, key=lambda x: x["name"])
        
    except Exception as e:
        logging.error(f"Error searching files: {e}")
        return [{"error": str(e)}]

def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get detailed information about a file or directory.
    
    Args:
        file_path: Path to the file or directory
    
    Returns:
        Dictionary containing detailed file information
    """
    try:
        workspace = config_manager.config.workspace_dir
        safe_path = get_safe_path(file_path, workspace)
        
        if not safe_path.exists():
            return {"error": f"Path {file_path} does not exist"}
        
        stat = safe_path.stat()
        
        info = {
            "name": safe_path.name,
            "path": str(safe_path.relative_to(Path(workspace))),
            "absolute_path": str(safe_path),
            "type": "directory" if safe_path.is_dir() else "file",
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "permissions": oct(stat.st_mode)[-3:],
            "owner": stat.st_uid,
            "group": stat.st_gid,
            "checksum": calculate_checksum(str(safe_path)) if safe_path.is_file() else None
        }
        
        if safe_path.is_file():
            info["mime_type"] = mimetypes.guess_type(str(safe_path))[0]
            info["extension"] = safe_path.suffix
        
        return info
        
    except Exception as e:
        logging.error(f"Error getting file info: {e}")
        return {"error": str(e)}

def get_config() -> Dict[str, Any]:
    """
    Get current configuration settings.
    
    Returns:
        Dictionary containing current configuration
    """
    return asdict(config_manager.config)

def update_config(workspace_dir: str = None, debug_mode: bool = None, max_file_size: str = None, 
                 log_level: str = None, theme: str = None, show_hidden_files: bool = None,
                 enable_checksums: bool = None, auto_backup: bool = None) -> Dict[str, Any]:
    """
    Update configuration settings.
    
    Args:
        workspace_dir: Workspace directory path
        debug_mode: Enable debug mode
        max_file_size: Maximum file size in bytes (as string)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        theme: UI theme (light, dark, system)
        show_hidden_files: Show hidden files by default
        enable_checksums: Enable file checksums
        auto_backup: Enable automatic backups
    
    Returns:
        Dictionary containing updated configuration
    """
    try:
        updates = {}
        
        if workspace_dir is not None:
            updates["workspace_dir"] = workspace_dir
        if debug_mode is not None:
            updates["debug_mode"] = debug_mode
        if max_file_size is not None:
            updates["max_file_size"] = int(max_file_size)
        if log_level is not None:
            updates["log_level"] = log_level
        if theme is not None:
            updates["theme"] = theme
        if show_hidden_files is not None:
            updates["show_hidden_files"] = show_hidden_files
        if enable_checksums is not None:
            updates["enable_checksums"] = enable_checksums
        if auto_backup is not None:
            updates["auto_backup"] = auto_backup
        
        return config_manager.update_config(**updates)
        
    except Exception as e:
        logging.error(f"Error updating config: {e}")
        return {"error": str(e)}

# Create Gradio interface
def create_interface():
    """Create the Gradio interface for the file manager"""
    
    # File listing interface
    with gr.Blocks(title="Enhanced DXT File Manager", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# Enhanced DXT File Manager")
        gr.Markdown("A powerful file management system with both web UI and MCP server capabilities")
        
        with gr.Tab("File Browser"):
            with gr.Row():
                directory_input = gr.Textbox(label="Directory", value=".", placeholder="Enter directory path")
                show_hidden_checkbox = gr.Checkbox(label="Show Hidden Files", value=False)
                file_type_dropdown = gr.Dropdown(
                    choices=["all", "files", "directories"],
                    value="all",
                    label="Filter Type"
                )
                list_button = gr.Button("List Files", variant="primary")
            
            file_list_output = gr.JSON(label="Files and Directories")
            
            list_button.click(
                list_files,
                inputs=[directory_input, show_hidden_checkbox, file_type_dropdown],
                outputs=file_list_output
            )
        
        with gr.Tab("File Operations"):
            with gr.Tab("Read File"):
                with gr.Row():
                    read_file_input = gr.Textbox(label="File Path", placeholder="Enter file path to read")
                    read_encoding_input = gr.Textbox(label="Encoding", value="utf-8")
                    read_button = gr.Button("Read File", variant="primary")
                
                read_output = gr.JSON(label="File Content")
                
                read_button.click(
                    read_file,
                    inputs=[read_file_input, read_encoding_input],
                    outputs=read_output
                )
            
            with gr.Tab("Write File"):
                with gr.Row():
                    write_file_input = gr.Textbox(label="File Path", placeholder="Enter file path to write")
                    write_encoding_input = gr.Textbox(label="Encoding", value="utf-8")
                    write_backup_checkbox = gr.Checkbox(label="Create Backup", value=True)
                
                write_content_input = gr.Textbox(
                    label="Content",
                    placeholder="Enter file content",
                    lines=10
                )
                write_button = gr.Button("Write File", variant="primary")
                write_output = gr.JSON(label="Write Result")
                
                write_button.click(
                    write_file,
                    inputs=[write_file_input, write_content_input, write_encoding_input, write_backup_checkbox],
                    outputs=write_output
                )
            
            with gr.Tab("Copy/Move"):
                with gr.Row():
                    source_input = gr.Textbox(label="Source Path", placeholder="Enter source path")
                    dest_input = gr.Textbox(label="Destination Path", placeholder="Enter destination path")
                    overwrite_checkbox = gr.Checkbox(label="Overwrite if exists", value=False)
                
                with gr.Row():
                    copy_button = gr.Button("Copy", variant="secondary")
                    move_button = gr.Button("Move", variant="secondary")
                
                copy_move_output = gr.JSON(label="Operation Result")
                
                copy_button.click(
                    copy_file,
                    inputs=[source_input, dest_input, overwrite_checkbox],
                    outputs=copy_move_output
                )
                
                move_button.click(
                    move_file,
                    inputs=[source_input, dest_input, overwrite_checkbox],
                    outputs=copy_move_output
                )
            
            with gr.Tab("Delete"):
                with gr.Row():
                    delete_input = gr.Textbox(label="File/Directory Path", placeholder="Enter path to delete")
                    delete_backup_checkbox = gr.Checkbox(label="Create Backup", value=True)
                    delete_button = gr.Button("Delete", variant="stop")
                
                delete_output = gr.JSON(label="Delete Result")
                
                delete_button.click(
                    delete_file,
                    inputs=[delete_input, delete_backup_checkbox],
                    outputs=delete_output
                )
        
        with gr.Tab("Search"):
            with gr.Row():
                search_query_input = gr.Textbox(label="Search Query", placeholder="Enter search term")
                search_dir_input = gr.Textbox(label="Directory", value=".", placeholder="Directory to search")
                search_content_checkbox = gr.Checkbox(label="Search Content", value=False)
                search_extensions_input = gr.Textbox(label="File Extensions", placeholder="e.g. .txt,.py,.md")
                search_button = gr.Button("Search", variant="primary")
            
            search_output = gr.JSON(label="Search Results")
            
            search_button.click(
                search_files,
                inputs=[search_query_input, search_dir_input, search_content_checkbox, search_extensions_input],
                outputs=search_output
            )
        
        with gr.Tab("File Info"):
            with gr.Row():
                info_input = gr.Textbox(label="File/Directory Path", placeholder="Enter path to get info")
                info_button = gr.Button("Get Info", variant="primary")
            
            info_output = gr.JSON(label="File Information")
            
            info_button.click(
                get_file_info,
                inputs=[info_input],
                outputs=info_output
            )
        
        with gr.Tab("Configuration"):
            with gr.Row():
                config_workspace_input = gr.Textbox(label="Workspace Directory", placeholder="Enter workspace path")
                config_debug_checkbox = gr.Checkbox(label="Debug Mode", value=False)
                config_max_size_input = gr.Textbox(label="Max File Size (bytes)", placeholder="10485760")
            
            with gr.Row():
                config_log_level_dropdown = gr.Dropdown(
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                    value="INFO",
                    label="Log Level"
                )
                config_theme_dropdown = gr.Dropdown(
                    choices=["light", "dark", "system"],
                    value="system",
                    label="Theme"
                )
                config_hidden_checkbox = gr.Checkbox(label="Show Hidden Files", value=False)
            
            with gr.Row():
                config_checksums_checkbox = gr.Checkbox(label="Enable Checksums", value=True)
                config_backup_checkbox = gr.Checkbox(label="Auto Backup", value=True)
            
            with gr.Row():
                get_config_button = gr.Button("Get Config", variant="secondary")
                update_config_button = gr.Button("Update Config", variant="primary")
            
            config_output = gr.JSON(label="Configuration")
            
            get_config_button.click(
                get_config,
                inputs=[],
                outputs=config_output
            )
            
            update_config_button.click(
                update_config,
                inputs=[
                    config_workspace_input, config_debug_checkbox, config_max_size_input,
                    config_log_level_dropdown, config_theme_dropdown, config_hidden_checkbox,
                    config_checksums_checkbox, config_backup_checkbox
                ],
                outputs=config_output
            )
        
        with gr.Tab("Directory Operations"):
            with gr.Row():
                create_dir_input = gr.Textbox(label="Directory Path", placeholder="Enter directory path to create")
                create_parents_checkbox = gr.Checkbox(label="Create Parent Directories", value=True)
                create_dir_button = gr.Button("Create Directory", variant="primary")
            
            create_dir_output = gr.JSON(label="Directory Creation Result")
            
            create_dir_button.click(
                create_directory,
                inputs=[create_dir_input, create_parents_checkbox],
                outputs=create_dir_output
            )
        
        # Status information
        with gr.Row():
            gr.Markdown("### Status")
            status_output = gr.Textbox(
                label="System Status",
                value="Enhanced DXT File Manager ready. MCP server enabled for agent integration.",
                interactive=False
            )
    
    return demo

def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, config_manager.config.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('file_manager.log')
        ]
    )

def main():
    """Main function to run the Enhanced DXT File Manager"""
    parser = argparse.ArgumentParser(description="Enhanced DXT File Manager with Gradio")
    parser.add_argument("--workspace", default=".", help="Workspace directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=7860, help="UI port")
    parser.add_argument("--max-file-size", type=int, default=10485760, help="Maximum file size in bytes")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    parser.add_argument("--no-mcp", action="store_true", help="Disable MCP server")
    parser.add_argument("--share", action="store_true", help="Enable Gradio sharing")
    
    args = parser.parse_args()
    
    # Update configuration with command line arguments
    config_manager.config.workspace_dir = os.path.abspath(args.workspace)
    config_manager.config.debug_mode = args.debug
    config_manager.config.ui_port = args.port
    config_manager.config.max_file_size = args.max_file_size
    config_manager.config.log_level = args.log_level
    config_manager.config.mcp_enabled = not args.no_mcp
    config_manager.save_config()
    
    setup_logging()
    
    # Create workspace directory if it doesn't exist
    os.makedirs(config_manager.config.workspace_dir, exist_ok=True)
    
    logging.info(f"Starting Enhanced DXT File Manager")
    logging.info(f"Workspace: {config_manager.config.workspace_dir}")
    logging.info(f"UI Port: {config_manager.config.ui_port}")
    logging.info(f"MCP Enabled: {config_manager.config.mcp_enabled}")
    
    # Create and launch Gradio interface
    demo = create_interface()
    
    try:
        # Launch with MCP server enabled
        demo.launch(
            server_port=config_manager.config.ui_port,
            server_name="0.0.0.0",
            mcp_server=config_manager.config.mcp_enabled,
            share=args.share,
            inbrowser=True
        )
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
