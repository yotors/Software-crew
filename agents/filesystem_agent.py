import os
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from software_crew.agents.base import BaseAgent
from software_crew.mcp import filesystem

class FileSystemAgent(BaseAgent):
    def __init__(self, mcp_url: str, registry_url: Optional[str] = None):
        super().__init__(
            name="FileSystemAgent",
            description="Agent responsible for file system operations",
            capabilities={
                "create_directory": {
                    "description": "Create a directory at the specified path",
                    "parameters": {
                        "path": {"type": "string", "description": "Path to create the directory"}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "message": {"type": "string", "description": "Operation result message"}
                    },
                    "handler": self.create_directory,
                    "tags": ["filesystem", "directory", "create"],
                    "examples": [
                        "Create a directory at /path/to/new/directory",
                        "Create nested directories at /path/to/nested/dirs"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                },
                "write_file": {
                    "description": "Write content to a file",
                    "parameters": {
                        "path": {"type": "string", "description": "Path to the file"},
                        "content": {"type": "string", "description": "Content to write to the file"}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "message": {"type": "string", "description": "Operation result message"}
                    },
                    "handler": self.write_file,
                    "tags": ["filesystem", "file", "write"],
                    "examples": [
                        "Write 'Hello World' to /path/to/file.txt",
                        "Write JSON data to /path/to/config.json"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                },
                "read_file": {
                    "description": "Read content from a file",
                    "parameters": {
                        "path": {"type": "string", "description": "Path to the file to read"}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "content": {"type": "string", "description": "File content"}
                    },
                    "handler": self.read_file,
                    "tags": ["filesystem", "file", "read"],
                    "examples": [
                        "Read contents of /path/to/file.txt",
                        "Read configuration from /path/to/config.json"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                },
                "list_directory": {
                    "description": "List contents of a directory",
                    "parameters": {
                        "path": {"type": "string", "description": "Path to the directory to list"}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "items": {"type": "array", "description": "List of directory contents"}
                    },
                    "handler": self.list_directory,
                    "tags": ["filesystem", "directory", "list"],
                    "examples": [
                        "List contents of /path/to/directory",
                        "List files in current directory"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                },
                "run_command": {
                    "description": "Run a terminal command",
                    "parameters": {
                        "command": {"type": "string", "description": "Command to execute"},
                        "cwd": {"type": "string", "description": "Working directory for the command", "optional": True},
                        "timeout": {"type": "integer", "description": "Command timeout in seconds", "optional": True}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the command succeeded"},
                        "stdout": {"type": "string", "description": "Command standard output"},
                        "stderr": {"type": "string", "description": "Command error output"}
                    },
                    "handler": self.run_command,
                    "tags": ["terminal", "command", "shell"],
                    "examples": [
                        "Run 'ls -la' in current directory",
                        "Execute 'npm install' in /path/to/project"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                }
            },
            registry_url=registry_url,
            mcp_url=mcp_url
        )
        self.mcp_url = mcp_url
        
    def file_operations(self, path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Handle file operations"""
        if content is not None:
            return self.write_file(path, content)
        return self.read_file(path)
        
    def code_generation(self, template: str, output_path: str) -> Dict[str, Any]:
        """Generate code from template"""
        try:
            self.write_file(output_path, template)
            return {"success": True, "message": f"Code generated at {output_path}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
            
    def terminal_access(self, command: str) -> Dict[str, Any]:
        """Execute terminal command"""
        return self.run_command(command)
        
    def environment_management(self, name: str, value: str) -> Dict[str, Any]:
        """Manage environment variables"""
        return self.set_environment_variable(name, value)
        
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory at the specified path"""
        return self.call_mcp(self.mcp_url, "create_directory", {"path": path})
        
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        return self.call_mcp(self.mcp_url, "write_file", {"path": path, "content": content})
        
    def read_file(self, path: str) -> Dict[str, Any]:
        """Read content from a file"""
        return self.call_mcp(self.mcp_url, "read_file", {"path": path})
        
    def list_directory(self, path: str) -> Dict[str, Any]:
        """List contents of a directory"""
        return self.call_mcp(self.mcp_url, "list_directory", {"path": path})
        
    def run_command(self, command: str, cwd: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Run a terminal command"""
        params = {"command": command}
        if cwd:
            params["cwd"] = cwd
        if timeout:
            params["timeout"] = timeout
        return self.call_mcp(self.mcp_url, "run_command", params)
        
    def set_environment_variable(self, name: str, value: str) -> Dict[str, Any]:
        """Set an environment variable"""
        return self.call_mcp(self.mcp_url, "set_environment_variable", {"name": name, "value": value})


