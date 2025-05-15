import os
import asyncio
import typer
from dotenv import load_dotenv
from software_crew.orchestrator import Orchestrator


async def run():
    load_dotenv()
    github_token = os.getenv("GITHUB_TOKEN")
    # Initialize orchestrator
    orchestrator = Orchestrator(
        github_token=github_token,
        registry_url="localhost:8000"
    )
    
    try:
        # Start the system
        await orchestrator.start()
        typer.echo("Software Crew system started successfully!")
                
    except KeyboardInterrupt:
        typer.echo("\nShutting down...")
    finally:
        typer.echo("System stopped")

# Run the async function

if __name__ == "__main__":
    asyncio.run(run())