import logging
import asyncio
import os
from fastmcp import FastMCP

# Import CDC EPHT tool registration
from tools.cdc_epht import register_cdc_epht_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
MCP_APP_HOST = os.getenv("MCP_EPHT_HOST", "0.0.0.0")
MCP_APP_PORT = int(os.getenv("MCP_EPHT_PORT", "8889"))

# Initialize MCP server for CDC EPHT
mcp = FastMCP("CDC EPHT Server", host=MCP_APP_HOST, port=MCP_APP_PORT)

def register_tools():
    """Register CDC EPHT tools with the MCP server."""
    logger.info("Registering CDC EPHT tools...")
    register_cdc_epht_tools(mcp)
    logger.info("CDC EPHT tools registered successfully!")

async def main():
    """Main entry point for the CDC EPHT MCP server."""
    try:
        # Register CDC EPHT tools
        register_tools()
        
        # Start the server
        logger.info(f"Starting CDC EPHT MCP Server on {MCP_APP_HOST}:{MCP_APP_PORT}")
        await mcp.run_sse_async(
            host=MCP_APP_HOST,
            port=MCP_APP_PORT,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start CDC EPHT server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
