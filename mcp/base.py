import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel
from python_a2a.mcp import FastMCP, create_fastapi_app
import uvicorn
import uvicorn.server

class BaseMCPServer:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.mcp = FastMCP(name)
        self._setup_tools()
        
    def _setup_tools(self):
        """Setup MCP tools - to be implemented by subclasses"""
        pass
        
    def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the MCP server"""
        app = create_fastapi_app(self.mcp)
        config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        return server
        
    async def stop(self):
        """Stop the MCP server"""
        await self.mcp.stop()
        
    def get_tools(self) -> Dict[str, Any]:
        """Get information about available tools"""
        return {
            name: {
                "description": tool.__doc__,
                "parameters": tool.__annotations__
            }
            for name, tool in self.mcp.get_tools()
        } 