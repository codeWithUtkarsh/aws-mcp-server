"""Main entry point for the AWS MCP Server.

This module provides the command-line interface and entry point for running
the AWS MCP Server, with options for different transport methods and logging levels.
"""

import argparse
import asyncio
import logging
import sys

from .config import SERVER_INFO
from .server import mcp, startup

# Configure root logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("aws-mcp-server")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="AWS MCP Server")
    parser.add_argument("--tcp", action="store_true", help="Start with TCP transport instead of stdio")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to listen on when using TCP transport")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on when using TCP transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


async def main() -> None:
    """Main entry point for the AWS MCP Server.

    Parses command-line arguments, configures logging, and starts the server
    with the appropriate transport method.
    """
    args = parse_args()

    # Configure logging based on debug flag
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.getLogger().setLevel(log_level)  # Update root logger level

    # Log server information
    logger.info(f"Starting {SERVER_INFO['name']} version {SERVER_INFO['version']}")

    try:
        # Run startup checks
        await startup()
        
        # Run the server based on transport type
        if args.tcp:
            logger.info(f"Using TCP transport on {args.host}:{args.port}")
            mcp.run(transport="tcp", host=args.host, port=args.port)
        else:
            logger.info("Using stdio transport")
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)  # Exit with error code


if __name__ == "__main__":
    asyncio.run(main())
