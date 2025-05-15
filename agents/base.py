from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from python_a2a import AgentCard, AgentSkill, mcp
from python_a2a.discovery import DiscoveryClient
from python_a2a.server import A2AServer
import uvicorn
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import asyncio

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel()

class BaseAgent(A2AServer):
    def __init__(self, name: str, description: str, capabilities: Dict[str, Dict[str, Any]], registry_url: Optional[str] = None, mcp_url:str =None):
        # Convert capabilities to A2A specification format
        self.name = name
        self.description = description
        self.capabilities = capabilities
        a2a_skills = []
        for skill_name, cap_info in capabilities.items():
            a2a_skills.append(AgentSkill(
                name=skill_name,
                description=cap_info.get("description", ""),
                tags=cap_info.get("tags", []),
                examples=cap_info.get("examples", []),
                input_modes=cap_info.get("input_modes", ["text/plain"]),
                output_modes=cap_info.get("output_modes", ["text/plain"])
            ))
        self.agent_card = AgentCard(
            name=name,
            description=description,
            url=registry_url, 
            capabilities={
                "agent_discovery": True,
                "registry": True,
                "google_a2a_compatible": True,
                "parts_array_format": True
            },
            skills=a2a_skills,
        )
        self.mcp_url = mcp_url
        self.registry_url = registry_url
        self.discovery_client = None
        if registry_url:
            self.discovery_client = DiscoveryClient(agent_card=self.agent_card)
            self.discovery_client.add_registry(registry_url)
        # Initialize the parent A2AServer with the agent_card
        super().__init__(agent_card=self.agent_card)
        # Register skills from capabilities
        self.capabilities = capabilities  # Store capabilities for AI routing

    def get_agent_card(self) -> AgentCard:
        """Get the agent's card"""
        return self.agent_card

    def call_mcp(self, mcp_url: str, tool: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP server"""
        try:
            tool_url = f"{mcp_url}/tools/{tool}"
            response = requests.post(
                    tool_url, 
                    json=parameters,
                    headers={"Content-Type": "application/json"}
                )
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Extract the text content
            if "content" in result and len(result["content"]) > 0:
                if "text" in result["content"][0]:
                    return result["content"][0]["text"]
            
            # Return the raw response if we couldn't extract text
            return str(result)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the A2A server using FastAPI and uvicorn"""
        from flask import Flask
        a2a = Flask(self.name)
        self.setup_routes(a2a)
        return a2a

    # --- A2AServer core methods for task/message handling ---
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

    def handle_task(self, task):
        """Use AI to determine which capability to use for the task and its parameters"""
        # Create a prompt for the AI
        prompt = f"""
        You are an AI assistant helping to route tasks to the appropriate capability.
        Agent Name: {self.name}
        Agent Description: {self.description}
        Available Capabilities: {self.capabilities}
        Task: {task}

        Based on the task description and available capabilities, determine which capability should handle this task and what parameters to use.
        Return a JSON object in this exact format:
        {{
            "capability": "name_of_capability",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
        If no capability matches, return:
        {{
            "capability": "unknown",
            "parameters": {{}}
        }}
        """

        # Get AI response
        response = model.generate_content(prompt).text.strip()
        
        try:
            # Clean and parse the JSON response
            cleaned_response = self._clean_ai_response(response)
            result = json.loads(cleaned_response)
            
            # If AI suggests a capability, use it
            if result["capability"] in self.capabilities:
                capability = self.capabilities[result["capability"]]
                # Call the capability handler with the parameters
                handler_result = capability["handler"](**result["parameters"])
                return {
                    "success": True, 
                    "capability": result["capability"],
                    "parameters": result["parameters"],
                    "result": handler_result
                }
        except json.JSONDecodeError:
            pass
        
        # If no matching capability or invalid JSON, delegate to parent
        return super().handle_task(task)

    def handle_message(self, message):
        """Use AI to determine how to handle the message and its parameters"""
        # Create a prompt for the AI
        prompt = f"""
        You are an AI assistant helping to process messages.
        Agent Name: {self.name}
        Agent Description: {self.description}
        Available Capabilities: {self.capabilities}
        Message: {message}

        Based on the message content and available capabilities, determine how to handle this message and what parameters to use.
        Return a JSON object in this exact format:
        {{
            "capability": "name_of_capability",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
        If no capability matches, return:
        {{
            "capability": "unknown",
            "parameters": {{}}
        }}
        """

        # Get AI response
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        try:
            # Clean and parse the JSON response
            cleaned_response = self._clean_ai_response(response_text)
            result = json.loads(cleaned_response)
            
            # If AI suggests a capability, use it
            if result["capability"] in self.capabilities:
                capability = self.capabilities[result["capability"]]
                # Call the capability handler with the parameters
                handler_result = capability["handler"](**result["parameters"])
                return {
                    "success": True,
                    "capability": result["capability"],
                    "parameters": result["parameters"],
                    "result": handler_result
                }
        except json.JSONDecodeError:
            pass
        
        # If no matching capability or invalid JSON, return error
        return {
            "success": False,
            "message": "No matching capability found or invalid response format"
        }

    def setup_routes(self, app):
        """Setup FastAPI routes for A2A endpoints. By default, delegates to parent."""
        return super().setup_routes(app=app) 