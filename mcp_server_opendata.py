import logging
import asyncio
import os
from fastmcp import FastMCP

# Import CDC Open Data tool registration
from tools.cdc_open_data import register_cdc_open_data_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
MCP_APP_HOST = os.getenv("MCP_OPENDATA_HOST", "0.0.0.0")
MCP_APP_PORT = int(os.getenv("MCP_OPENDATA_PORT", "8890"))

# Initialize MCP server for CDC Open Data
mcp = FastMCP("CDC Open Data Server", host=MCP_APP_HOST, port=MCP_APP_PORT)

def register_tools():
    """Register CDC Open Data tools with the MCP server."""
    logger.info("Registering CDC Open Data tools...")
    register_cdc_open_data_tools(mcp)
    logger.info("CDC Open Data tools registered successfully!")

async def main():
    """Main entry point for the CDC Open Data MCP server."""
    try:
        # Register CDC Open Data tools
        register_tools()
        
        # Start the server
        logger.info(f"Starting CDC Open Data MCP Server on {MCP_APP_HOST}:{MCP_APP_PORT}")
        await mcp.run_sse_async(
            host=MCP_APP_HOST,
            port=MCP_APP_PORT,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start CDC Open Data server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
