import asyncio
from typing import Dict, Any, Optional
from software_crew.agents.filesystem_agent import FileSystemAgent
from software_crew.agents.github_agent import GitHubAgent
from software_crew.agents.vercel_agent import VercelAgent
from software_crew.mcp.filesystem import FileSystemMCPServer
from software_crew.mcp.github_mcp import GitHubMCPServer
from software_crew.mcp.vercel import VercelMCPServer
from python_a2a.discovery import AgentRegistry, run_registry
import uvicorn
from python_a2a.mcp import create_fastapi_app
import google.generativeai as genai
from dotenv import load_dotenv
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel()

class TaskRequest(BaseModel):
    task: str
    parameters: Optional[Dict[str, Any]] = None

class MessageRequest(BaseModel):
    message: str
    parameters: Optional[Dict[str, Any]] = None

class Orchestrator:
    def __init__(self, registry_url: Optional[str] = None, github_token: str = None):
        self.registry_url = registry_url
        self.filesystem_mcp = FileSystemMCPServer()
        self.github_mcp = GitHubMCPServer(github_token=github_token)
        self.vercel_mcp = VercelMCPServer()
        self.filesystem_agent = FileSystemAgent(mcp_url="http://localhost:8001", registry_url="f{registry_url}/filesystem")
        self.github_agent = GitHubAgent(mcp_url="http://localhost:8002", registry_url="f{registry_url}/github")
        self.vercel_agent = VercelAgent(mcp_url="http://localhost:8003", registry_url="f{registry_url}/vercel")
        self.registery = AgentRegistry(self.filesystem_agent.agent_card)
        self.registery.register_agent(self.github_agent.agent_card)
        self.registery.register_agent(self.vercel_agent.agent_card)
        self.agents = {
            "FileSystemAgent": self.filesystem_agent,
            "GitHubAgent": self.github_agent,
            "VercelAgent": self.vercel_agent
        }
        
        # Create FastAPI app for the orchestrator
        self.app = FastAPI(title="Software Crew Orchestrator")
        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes for the orchestrator"""
        @self.app.post("/task")
        def handle_task(request: TaskRequest):
            try:
                result = self.handle_task(request.task)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/message")
        def handle_message(request: MessageRequest):
            try:
                result = self.handle_message(request.message)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/agents")
        def list_agents():
            return self.discover_agents()

    async def start(self):
        """Start all agents, MCPs, and the orchestrator server"""
        # Start the orchestrator server
        config = uvicorn.Config(self.app, host="0.0.0.0", port=8006)
        server = uvicorn.Server(config)
        
        # Start all components
        await asyncio.gather(
            asyncio.to_thread(lambda: self.filesystem_agent.start().run(host="0.0.0.0", 
            port=8000)),
            asyncio.to_thread(lambda: self.github_agent.start().run(host="0.0.0.0", 
            port=8004)),
            asyncio.to_thread(lambda: self.vercel_agent.start().run(host="0.0.0.0", 
            port=8005)),
            self.filesystem_mcp.start(port=8001).serve(),
            self.github_mcp.start(port=8002).serve(),
            self.vercel_mcp.start(port=8003).serve(),
            server.serve()
        )

    def _clean_ai_response(self, response: str) -> str:
        """Clean the AI response by removing markdown code block formatting"""
        # Remove markdown code block markers if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()

    def select_agent(self, task_or_message):
        """Use AI to select the most appropriate agent for the task/message and its parameters"""
        # Get all available agents
        agents_info = self.discover_agents()
        
        # Create a prompt for the AI
        prompt = f"""
        You are an AI assistant helping to route tasks/messages to the appropriate agent.
        Available Agents: {agents_info['agents']}
        Task/Message: {task_or_message}

        Based on the task/message content and the available agents' skill, determine which agent should handle this and what parameters to use.
        Return a JSON object in this exact format:
        {{
            "agent": "name_of_agent",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
        If no agent matches, return:
        {{
            "agent": "unknown",
            "parameters": {{}}
        }}
        """

        # Get AI response
        response = model.generate_content(prompt).text.strip()
        

        try:
            # Clean and parse the JSON response
            cleaned_response = self._clean_ai_response(response)
            result = json.loads(cleaned_response)
            return result
        except json.JSONDecodeError as e:
            return {"agent": "unknown", "parameters": {}}

    def handle_task(self, task):
        """Handle a task by using AI to select the appropriate agent"""
        result = self.select_agent(task)
        print(result)
        if result["agent"] in self.agents:
            agent = self.agents[result["agent"]]
            # Pass both task and parameters to the agent
            return agent.handle_task({
                "task": task,
                "parameters": result["parameters"]
            })
        else:
            return {"success": False, "message": f"Unknown agent: {result['agent']}"}

    def handle_message(self, message):
        """Handle a message by using AI to select the appropriate agent"""
        result = self.select_agent(message)
        print(result)
        
        if result["agent"] in self.agents:
            agent = self.agents[result["agent"]]
            # Pass both message and parameters to the agent
            return agent.handle_message({
                "message": message,
                "parameters": result["parameters"]
            })
        else:
            return {"success": False, "message": f"Unknown agent: {result['agent']}"}

    def discover_agents(self):
        """Get information about all registered agents"""
        agents = self.registery.get_all_agents()
        return {"success": True, "agents": agents}