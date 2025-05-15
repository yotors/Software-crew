from typing import Dict, Any, Optional
from .base import BaseAgent

class VercelAgent(BaseAgent):
    def __init__(self, mcp_url: str, registry_url: Optional[str] = None):
        super().__init__(
            name="VercelAgent",
            description="Agent responsible for Vercel deployments",
            capabilities={
                "login": {
                    "description": "Log in to Vercel CLI",
                    "parameters": {
                        "email": {"type": "string", "description": "Vercel account email"}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "message": {"type": "string", "description": "Operation result message"},
                        "output": {"type": "string", "description": "Command output", "optional": True}
                    },
                    "handler": self.login,
                    "tags": ["vercel", "login", "auth"],
                    "examples": [
                        "Login to Vercel with email user@example.com",
                        "Authenticate with Vercel account"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                },
                "deploy": {
                    "description": "Deploy a project to Vercel",
                    "parameters": {
                        "project_path": {"type": "string", "description": "Path to the project directory"}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "message": {"type": "string", "description": "Operation result message"},
                        "deployment_url": {"type": "string", "description": "URL of the deployment", "optional": True},
                        "output": {"type": "string", "description": "Deployment output", "optional": True}
                    },
                    "handler": self.deploy,
                    "tags": ["vercel", "deploy", "deployment"],
                    "examples": [
                        "Deploy project from /path/to/project",
                        "Deploy current directory to Vercel"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                },
                "set_environment_variable": {
                    "description": "Set an environment variable for a Vercel project",
                    "parameters": {
                        "project_path": {"type": "string", "description": "Path to the project directory"},
                        "name": {"type": "string", "description": "Environment variable name"},
                        "value": {"type": "string", "description": "Environment variable value"}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "message": {"type": "string", "description": "Operation result message"},
                        "output": {"type": "string", "description": "Command output", "optional": True}
                    },
                    "handler": self.set_environment_variable,
                    "tags": ["vercel", "env", "environment"],
                    "examples": [
                        "Set API_KEY environment variable for project",
                        "Configure environment variables for deployment"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                },
                "get_deployment_status": {
                    "description": "Get the deployment status of a project",
                    "parameters": {
                        "project_path": {"type": "string", "description": "Path to the project directory"}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "status": {
                            "type": "object",
                            "description": "Deployment status information",
                            "properties": {
                                "state": {"type": "string", "description": "Current deployment state"},
                                "url": {"type": "string", "description": "Deployment URL"},
                                "ready": {"type": "boolean", "description": "Whether deployment is ready"},
                                "error": {"type": "string", "description": "Error message if any"}
                            }
                        }
                    },
                    "handler": self.get_deployment_status,
                    "tags": ["vercel", "status", "deployment"],
                    "examples": [
                        "Check deployment status of project",
                        "Get current deployment state"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                }
            },
            registry_url=registry_url,
            mcp_url=mcp_url
        )
        self.mcp_url = mcp_url
        
    def login(self, email: str) -> Dict[str, Any]:
        """Log in to Vercel CLI"""
        return self.call_mcp(self.mcp_url, "login", {"email": email})
        
    def deploy(self, project_path: str) -> Dict[str, Any]:
        """Deploy a project to Vercel"""
        return self.call_mcp(self.mcp_url, "deploy", {"project_path": project_path})
        
    def set_environment_variable(self, project_path: str, name: str, value: str) -> Dict[str, Any]:
        """Set an environment variable for a Vercel project"""
        return self.call_mcp(
            self.mcp_url,
            "set_environment_variable",
            {"project_path": project_path, "name": name, "value": value}
        )
        
    def get_deployment_status(self, project_path: str) -> Dict[str, Any]:
        """Get the deployment status of a project"""
        return self.call_mcp(self.mcp_url, "get_deployment_status", {"project_path": project_path})

    def handle_task(self, task):
        message = task.message or {}
        msg_type = message.get("type")
        result = None

        if msg_type == "deploy":
            project_path = message.get("project_path")
            if project_path:
                result = self.deploy(project_path)
            else:
                result = {"success": False, "message": "Missing project_path."}
        elif msg_type == "set_environment_variable":
            project_path = message.get("project_path")
            name = message.get("name")
            value = message.get("value")
            if project_path and name and value is not None:
                result = self.set_environment_variable(project_path, name, value)
            else:
                result = {"success": False, "message": "Missing project_path, name, or value."}
        elif msg_type == "get_deployment_status":
            project_path = message.get("project_path")
            if project_path:
                result = self.get_deployment_status(project_path)
            else:
                result = {"success": False, "message": "Missing project_path."}
        elif msg_type == "login":
            result = self.login(message.get('email'))
        else:
            result = {"success": False, "message": "Unknown or incomplete task message."}

        # Update task artifacts and status
        task.artifacts = [{"parts": [{"type": "data", "data": result}]}]
        from python_a2a.models.task import TaskStatus, TaskState
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task

    def handle_message(self, message):
        """Override to handle incoming messages."""
        # First try the base agent's AI-based routing
        result = super().handle_message(message)
        if result["success"]:
            return result
            
        # If AI routing didn't work, try direct message handling
        msg_type = message.get("type")
        if msg_type == "deploy":
            project_path = message.get("project_path")
            if project_path:
                result = self.deploy(project_path)
            else:
                result = {"success": False, "message": "Missing project_path."}
        elif msg_type == "set_environment_variable":
            project_path = message.get("project_path")
            name = message.get("name")
            value = message.get("value")
            if project_path and name and value is not None:
                result = self.set_environment_variable(project_path, name, value)
            else:
                result = {"success": False, "message": "Missing project_path, name, or value."}
        elif msg_type == "get_deployment_status":
            project_path = message.get("project_path")
            if project_path:
                result = self.get_deployment_status(project_path)
            else:
                result = {"success": False, "message": "Missing project_path."}
        elif msg_type == "login":
            result = self.login(message.get('email'))
        else:
            result = {"success": False, "message": "Unknown or incomplete task message."}
            
        return result
