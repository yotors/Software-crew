from typing import Dict, Any, Optional, List
from software_crew.agents.base import BaseAgent

class GitHubAgent(BaseAgent):
    def __init__(self, mcp_url: str, registry_url: Optional[str] = None):
        super().__init__(
            name="GitHubAgent",
            description="Agent responsible for GitHub operations",
            capabilities={
                "create_repository": {
                    "description": "Create a new GitHub repository",
                    "parameters": {
                        "name": {"type": "string", "description": "Name of the repository"},
                        "description": {"type": "string", "description": "Repository description", "optional": True},
                        "private": {"type": "boolean", "description": "Whether the repository should be private", "optional": True}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "message": {"type": "string", "description": "Operation result message"},
                        "repository_url": {"type": "string", "description": "URL of the created repository", "optional": True}
                    },
                    "handler": self.create_repository,
                    "tags": ["github", "repository", "create"],
                    "examples": [
                        "Create a new repository named 'my-project'",
                        "Create a private repository 'internal-tools' with description"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                },
                "push_code": {
                    "description": "Push code to a GitHub repository",
                    "parameters": {
                        "repo_name": {"type": "string", "description": "Name of the repository"},
                        "branch": {"type": "string", "description": "Branch to push to", "optional": True},
                        "commit_message": {"type": "string", "description": "Commit message"},
                        "paths": {"type": "array", "description": "Paths of files to commit", "optional": True},
                        "contents": {"type": "array", "description": "Contents of files to commit", "optional": True}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "message": {"type": "string", "description": "Operation result message"}
                    },
                    "handler": self.push_code,
                    "tags": ["github", "push", "commit"],
                    "examples": [
                        "Push all changes to main branch with message 'Update code'",
                        "Push specific files to feature branch"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                },
                "get_repository_info": {
                    "description": "Get information about a repository",
                    "parameters": {
                        "repo_name": {"type": "string", "description": "Name of the repository"}
                    },
                    "returns": {
                        "success": {"type": "boolean", "description": "Whether the operation succeeded"},
                        "repository": {
                            "type": "object",
                            "description": "Repository information",
                            "properties": {
                                "name": {"type": "string", "description": "Repository name"},
                                "description": {"type": "string", "description": "Repository description"},
                                "url": {"type": "string", "description": "Repository URL"},
                                "stars": {"type": "integer", "description": "Number of stars"},
                                "forks": {"type": "integer", "description": "Number of forks"},
                                "private": {"type": "boolean", "description": "Whether the repository is private"}
                            }
                        }
                    },
                    "handler": self.get_repository_info,
                    "tags": ["github", "repository", "info"],
                    "examples": [
                        "Get information about repository 'my-project'",
                        "Check repository details and stats"
                    ],
                    "input_modes": ["text/plain"],
                    "output_modes": ["text/plain", "application/json"]
                }
            },
            registry_url=registry_url,
            mcp_url=mcp_url
        )
        self.mcp_url = mcp_url
        
    def create_repository(self, name: str, description: Optional[str] = None, private: Optional[bool] = None) -> Dict[str, Any]:
        """Create a new GitHub repository"""
        params = {"name": name}
        if description:
            params["description"] = description
        if private is not None:
            params["private"] = private
        return self.call_mcp(self.mcp_url, "create_repository", params)
        
    def push_code(self, repo_name: str, commit_message: str, branch: Optional[str] = None, 
                 paths: Optional[List[str]] = None, contents: Optional[List[str]] = None) -> Dict[str, Any]:
        """Push code to a GitHub repository"""
        params = {
            "repo_name": repo_name,
            "commit_message": commit_message
        }
        if branch:
            params["branch"] = branch
        if paths:
            params["paths"] = paths
        if contents:
            params["contents"] = contents
        return self.call_mcp(self.mcp_url, "push_code", params)
        
    def get_repository_info(self, repo_name: str) -> Dict[str, Any]:
        """Get information about a repository"""
        return self.call_mcp(self.mcp_url, "get_repository_info", {"repo_name": repo_name})

    def handle_task(self, task):
        message = task.message or {}
        msg_type = message.get("type")
        result = None

        if msg_type == "create_repository":
            name = message.get("name")
            description = message.get("description", "")
            private = message.get("private", False)
            if name:
                result = self.create_repository(name, description, private)
            else:
                result = {"success": False, "message": "Missing repository name."}
        elif msg_type == "push_code":
            repo_name = message.get("repo_name")
            branch = message.get("branch", "main")
            commit_message = message.get("commit_message", "Commit from agent")
            if repo_name:
                result = self.push_code(repo_name, commit_message, branch)
            else:
                result = {"success": False, "message": "Missing repository name."}
        elif msg_type == "get_repository_info":
            repo_name = message.get("repo_name")
            if repo_name:
                result = self.get_repository_info(repo_name)
            else:
                result = {"success": False, "message": "Missing repository name."}
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
        if msg_type == "create_repository":
            name = message.get("name")
            description = message.get("description", "")
            private = message.get("private", False)
            if name:
                result = self.create_repository(name, description, private)
            else:
                result = {"success": False, "message": "Missing repository name."}
        elif msg_type == "push_code":
            repo_name = message.get("repo_name")
            branch = message.get("branch", "main")
            commit_message = message.get("commit_message", "Commit from agent")
            if repo_name:
                result = self.push_code(repo_name, commit_message, branch)
            else:
                result = {"success": False, "message": "Missing repository name."}
        elif msg_type == "get_repository_info":
            repo_name = message.get("repo_name")
            if repo_name:
                result = self.get_repository_info(repo_name)
            else:
                result = {"success": False, "message": "Missing repository name."}
        else:
            result = {"success": False, "message": "Unknown or incomplete task message."}
            
        return result