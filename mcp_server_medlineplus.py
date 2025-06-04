import logging
import asyncio
import os
from fastmcp import FastMCP

# Import MedlinePlus Connect tool registration
from tools.medlineplus_connect import register_medlineplus_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
MCP_APP_HOST = os.getenv("MCP_MEDLINEPLUS_HOST", "0.0.0.0")
MCP_APP_PORT = int(os.getenv("MCP_MEDLINEPLUS_PORT", "8892"))

# Initialize MCP server for MedlinePlus Connect
mcp = FastMCP("MedlinePlus Connect Server", host=MCP_APP_HOST, port=MCP_APP_PORT)

def register_tools():
    """Register MedlinePlus Connect tools with the MCP server."""
    logger.info("Registering MedlinePlus Connect tools...")
    register_medlineplus_tools(mcp)
    logger.info("MedlinePlus Connect tools registered successfully!")

async def main():
    """Main entry point for the MedlinePlus Connect MCP server."""
    try:
        # Register MedlinePlus Connect tools
        register_tools()
        
        # Start the server
        logger.info(f"Starting MedlinePlus Connect MCP Server on {MCP_APP_HOST}:{MCP_APP_PORT}")
        await mcp.run_sse_async(
            host=MCP_APP_HOST,
            port=MCP_APP_PORT,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start MedlinePlus Connect server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
