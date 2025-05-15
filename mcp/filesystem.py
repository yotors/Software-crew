import os
import shutil
from typing import Dict, Any, List
from pathlib import Path
from software_crew.mcp.base import BaseMCPServer

class FileSystemMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            name="FileSystemMCP",
            description="MCP server for file system operations"
        )
        
    def _setup_tools(self):
        """Setup file system tools"""
        @self.mcp.tool()
        def create_directory(path: str) -> Dict[str, Any]:
            """Create a directory at the specified path
            Args:
                path(str): path to create the file
            Returns:
                dict of status
            """
            try:
                Path(path).mkdir(parents=True, exist_ok=True)
                return {"success": True, "message": f"Directory created at {path}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def write_file(path: str, content: str) -> Dict[str, Any]:
            """Write content to a file
            args:
                path: file path to open and write on
                content: the content to be written to the file path
            Returns:
                dict of status
            """
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {"success": True, "message": f"File written to {path}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def read_file(path: str) -> Dict[str, Any]:
            """Read content from a 
            args:
                path(str): path to the file to be read
            """
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"success": True, "content": content}
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def list_directory(path: str) -> Dict[str, Any]:
            """List contents of a directory
            args:
                path(str): path to the folder to list the files in it
            """

            try:
                items = os.listdir(path)
                return {"success": True, "items": items}
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def run_command(command: str, cwd: str = None, timeout: int = 30) -> Dict[str, Any]:
            """Run a terminal command
            args:
                command(str): to be executed
                cwd(str, optional): full directory path to run the command in
                timeout: the timeout for the command
            """
            try:
                import asyncio
                import shlex
                # Split the command string into args for subprocess
                args = shlex.split(command)
                proc = asyncio.create_subprocess_exec(
                    *args,
                    cwd=cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
                try:
                    stdout, stderr = asyncio.wait_for(proc.communicate(), timeout=timeout)
                except asyncio.TimeoutError:
                    proc.kill()
                    proc.wait()
                    return {"success": False, "error": f"Timeout expired after {timeout} seconds."}
                return {
                    "success": proc.returncode == 0,
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}