"""Main entry point for the AWS MCP Server.

This module provides the entry point for running the AWS MCP Server.
FastMCP handles the command-line arguments and server configuration.
"""

import logging
import signal
import sys

from aws_mcp_server.server import logger, mcp

# Configure root logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stderr)])


def handle_interrupt(sig, frame):
    """Handle keyboard interrupt (Ctrl+C) gracefully."""
    logger.info("Received interrupt signal. Shutting down gracefully...")
    sys.exit(0)


# Using FastMCP's built-in CLI handling
if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        # FastMCP's run method handles command-line arguments,
        # transport selection, and error handling automatically
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down gracefully...")
        sys.exit(0)
