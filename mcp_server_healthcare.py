import logging
import asyncio
import os
from fastmcp import FastMCP

# Import Healthcare.gov tool registration
from tools.healthcare_gov_fixed import register_healthcare_gov_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
MCP_APP_HOST = os.getenv("MCP_HEALTHCARE_HOST", "0.0.0.0")
MCP_APP_PORT = int(os.getenv("MCP_HEALTHCARE_PORT", "8891"))

# Initialize MCP server for Healthcare.gov
mcp = FastMCP("Healthcare.gov Server", host=MCP_APP_HOST, port=MCP_APP_PORT)

def register_tools():
    """Register Healthcare.gov tools with the MCP server."""
    logger.info("Registering Healthcare.gov tools...")
    register_healthcare_gov_tools(mcp)
    logger.info("Healthcare.gov tools registered successfully!")

async def main():
    """Main entry point for the Healthcare.gov MCP server."""
    try:
        # Register Healthcare.gov tools
        register_tools()
        
        # Start the server
        logger.info(f"Starting Healthcare.gov MCP Server on {MCP_APP_HOST}:{MCP_APP_PORT}")
        await mcp.run_sse_async(
            host=MCP_APP_HOST,
            port=MCP_APP_PORT,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start Healthcare.gov server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
