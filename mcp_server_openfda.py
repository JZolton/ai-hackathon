import logging
import asyncio
import os
from fastmcp import FastMCP

# Import OpenFDA API tool registration
from tools.openfda_api import register_openfda_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
MCP_APP_HOST = os.getenv("MCP_OPENFDA_HOST", "0.0.0.0")
MCP_APP_PORT = int(os.getenv("MCP_OPENFDA_PORT", "8893"))

# Initialize MCP server for OpenFDA API
mcp = FastMCP("OpenFDA API Server", host=MCP_APP_HOST, port=MCP_APP_PORT)

def register_tools():
    """Register OpenFDA API tools with the MCP server."""
    logger.info("Registering OpenFDA API tools...")
    register_openfda_tools(mcp)
    logger.info("OpenFDA API tools registered successfully!")

async def main():
    """Main entry point for the OpenFDA API MCP server."""
    try:
        # Register OpenFDA API tools
        register_tools()
        
        # Start the server
        logger.info(f"Starting OpenFDA API MCP Server on {MCP_APP_HOST}:{MCP_APP_PORT}")
        await mcp.run_sse_async(
            host=MCP_APP_HOST,
            port=MCP_APP_PORT,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start OpenFDA API server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
