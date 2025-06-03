import logging
import asyncio
import os
from fastmcp import FastMCP
from typing import Dict, Any

# Import tool registration functions
from tools.cdc_wonder import register_cdc_wonder_tools
from tools.cdc_epht import register_cdc_epht_tools
from tools.cdc_open_data import register_cdc_open_data_tools
from tools.healthcare_gov_fixed import register_healthcare_gov_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
MCP_APP_HOST = os.getenv("MCP_APP_HOST", "0.0.0.0")
MCP_APP_PORT = int(os.getenv("MCP_APP_PORT", "8888"))

# Initialize MCP server
mcp = FastMCP("CDC Health Data Server", host=MCP_APP_HOST, port=MCP_APP_PORT)

# Register all tool modules
def register_all_tools():
    """Register all available tools with the MCP server."""
    # logger.info("Registering CDC WONDER tools...")
    # Not current enough
    #register_cdc_wonder_tools(mcp)
    
    logger.info("Registering CDC EPHT tools...")
    register_cdc_epht_tools(mcp)
    
    logger.info("Registering CDC Open Data tools...")
    #good data
    register_cdc_open_data_tools(mcp)
    
    logger.info("Registering Healthcare.gov tools...")
    #good data
    register_healthcare_gov_tools(mcp)
    
    logger.info("All tools registered successfully!")

async def main():
    """Main entry point for the MCP server."""
    try:
        # Register all tools
        register_all_tools()
        
        # Start the server
        logger.info(f"Starting CDC Health Data MCP Server on {MCP_APP_HOST}:{MCP_APP_PORT}")
        await mcp.run_sse_async(
            host=MCP_APP_HOST,
            port=MCP_APP_PORT,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
