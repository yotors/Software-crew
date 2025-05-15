from typing import Dict, Any, Optional
from github import Github, GithubException
from .base import BaseMCPServer
import os
from dotenv import load_dotenv

class GitHubMCPServer(BaseMCPServer):
    def __init__(self, github_token: str):
        super().__init__(
            name="GitHubMCP",
            description="MCP server for GitHub operations"
        )
        self.github_token = github_token
        self.github = Github(github_token)
    def get_github_instance(self):
        load_dotenv()
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return None, {"success": False, "error": "GITHUB_TOKEN environment variable not set."}
        try:
            github = Github(github_token)
            # Test authentication
            github.get_user().login
            return github, None
        except GithubException as e:
            return None, {"success": False, "error": f"Authentication failed: {str(e)}"}
        except Exception as e:
            return None, {"success": False, "error": f"Unexpected error: {str(e)}"}
    def _setup_tools(self):
        """Setup GitHub tools"""
        @self.mcp.tool()
        def create_repository(name: str, description: str, private: bool = False) -> Dict[str, Any]:
            """Create a new GitHub repository
            args:
                name(str): name of the repo to be created
                description(str): description of the repo
                private(bool): Wheather the repo is private or not
            Returns:
                dict about status
            """
            github, error = self.get_github_instance()
            if error:
                return error
            try:
                user = github.get_user()
                repo = user.create_repo(
                    name=name,
                    description=description,
                    private=private
                )
                return {
                    "success": True,
                    "message": f"Repository created: {repo.html_url}",
                    "url": repo.html_url
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def push_code(repo_name: str, branch: str, commit_message: str, paths: list, contents: list) -> Dict[str, Any]:
            """Push code to a GitHub repository
            args:
                repo_name(str): the name of the repo to push the branch to
                branch(str): the branch to be pushed to the repo
                commite_message(str): the commit message
                paths(list): list of paths where there is change
                contents(list): list of the contents that are changed
            Returns:
                dict about the status
            """
            github, error = self.get_github_instance()
            if error:
                return error
            try:
                user = github.get_user()
                repo = user.get_repo(repo_name)
                from github import InputGitTreeElement
                elements = []
                for path, content in zip(paths, contents):
                    elements.append(InputGitTreeElement(
                        path=path,
                        mode='100644', 
                        type='blob',
                        content=content
                    ))

                # Get the branch
                branch_ref = repo.get_git_ref(f"heads/{branch}")
                
                # Get the current tree
                current_tree = repo.get_git_tree(branch_ref.object.sha)
                
                # Create a new tree with your changes
                new_tree = repo.create_git_tree(
                    tree=elements,  
                    base_tree=current_tree
                )
                
                # Create a commit with the new tree
                new_commit = repo.create_git_commit(
                    message=commit_message,
                    tree=new_tree,
                    parents=[branch_ref.object.sha]
                )
                
                # Update the branch reference
                branch_ref.edit(sha=new_commit.sha)
                
                return {
                    "success": True,
                    "message": f"Code pushed to {repo_name} on branch {branch}"
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def create_branch(repo_name: str, branch_name: str, base_branch: str = "main") -> Dict[str, Any]:
            """Create a new branch in a repository
            args:
                repo_name(str): the name of the repo to create the branch on
                branch_name(str): the name of the branch to be created
                base_branch(str): the currennt branch. default is main
            Returns:
                dict about the status
            """
            github, error = self.get_github_instance()
            if error:
                return error
            try:
                user = github.get_user()
                repo = user.get_repo(repo_name)
                
                # Get the base branch reference
                base_ref = repo.get_git_ref(f"heads/{base_branch}")
                
                # Create the new branch
                repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}",
                    sha=base_ref.object.sha
                )
                
                return {
                    "success": True,
                    "message": f"Branch {branch_name} created from {base_branch}"
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        @self.mcp.tool()
        def get_repository_info(repo_name: str) -> Dict[str, Any]:
            """Get information about a repository
            args:
                repo_name(str): the name of the repo
            Return:
                dict about the status
            """
            github, error = self.get_github_instance()
            if error:
                return error
            try:
                user = github.get_user()
                repo = user.get_repo(repo_name)
                
                return {
                    "success": True,
                    "name": repo.name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "is_private": repo.private
                }
            except Exception as e:
                return {"success": False, "error": str(e)}