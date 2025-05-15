import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
from .base import BaseMCPServer

class VercelMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            name="VercelMCP",
            description="MCP server for Vercel deployments"
        )
        
    def _setup_tools(self):
        """Setup Vercel tools"""
        @self.mcp.tool()
        def login(email) -> Dict[str, Any]:
            """Login to Vercel CLI"""
            try:
                result = subprocess.run(
                    f"vercel login {email}",
                    capture_output=True,
                    text=True,
                    shell=True
                )
                return {
                    "success": result.returncode == 0,
                    "message": "Successfully logged in to Vercel" if result.returncode == 0 else "Failed to login",
                    "output": result.stdout
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def deploy(project_path: str) -> Dict[str, Any]:
            """Deploy a project to Vercel"""
            try:
                result = subprocess.run(
                    ["vercel", "deploy", "--prod"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    shell=True
                )
                return {
                    "success": result.returncode == 0,
                    "message": "Successfully deployed to Vercel" if result.returncode == 0 else "Failed to deploy",
                    "output": result.stdout
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def set_environment_variable(project_path: str, name: str, value: str) -> Dict[str, Any]:
            """Set an environment variable for a Vercel project"""
            try:
                result = subprocess.run(
                    ["vercel", "env", "add", name],
                    cwd=project_path,
                    input=value,
                    capture_output=True,
                    text=True,
                    shell=True
                )
                return {
                    "success": result.returncode == 0,
                    "message": f"Environment variable {name} set" if result.returncode == 0 else "Failed to set environment variable",
                    "output": result.stdout
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def get_deployment_status(project_path: str) -> Dict[str, Any]:
            """Get the deployment status of a project"""
            try:
                result = subprocess.run(
                    ["vercel", "list"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    shell=True
                )
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout
                }
            except Exception as e:
                return {"success": False, "error": str(e)} 