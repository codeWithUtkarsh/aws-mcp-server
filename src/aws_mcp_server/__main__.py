"""Main entry point for the AWS MCP Server.

This module provides the entry point for running the AWS MCP Server.
FastMCP handles the command-line arguments and server configuration.
"""

import logging
import sys
from .server import mcp

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)

# Using FastMCP's built-in CLI handling
if __name__ == "__main__":
    # FastMCP's run method handles command-line arguments, 
    # transport selection, and error handling automatically
    mcp.run()
