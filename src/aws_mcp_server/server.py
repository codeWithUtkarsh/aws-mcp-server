"""Main server implementation for AWS MCP Server.

This module defines the MCP server instance and tool functions for AWS CLI interaction,
providing a standardized interface for AWS CLI command execution and documentation.
"""

import logging
import sys
import json
import traceback

from mcp.server.fastmcp import FastMCP

from .utils.cli_executor import (
    CommandExecutionError,
    CommandHelpResult,
    CommandResult,
    CommandValidationError,
    check_aws_cli_installed,
    execute_aws_command,
    get_command_help,
)
from .utils.formatter import format_aws_output
from .config import SERVER_INFO, SERVER_CAPABILITIES, INSTRUCTIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("aws-mcp-server")


# Create the FastMCP server with additional configuration
mcp = FastMCP(
    name="AWS MCP Server",
    version=SERVER_INFO["version"],
    capabilities=SERVER_CAPABILITIES,
    description=INSTRUCTIONS
)

# Add an explicit handler for the initialize method
@mcp.method("initialize")
async def handle_initialize(params):
    """Handle the initialize request from the client.
    
    This is called when the client initiates a connection to the server.
    """
    try:
        logger.info(f"Received initialize request from client")
        protocol_version = params.get("protocolVersion", "unknown")
        client_info = params.get("clientInfo", {})
        client_name = client_info.get("name", "unknown")
        client_version = client_info.get("version", "unknown")
        
        logger.info(f"Client connected: {client_name} v{client_version}, protocol: {protocol_version}")
        
        # Return a successful initialization response
        return {
            "serverInfo": {
                "name": SERVER_INFO["name"],
                "version": SERVER_INFO["version"]
            },
            "capabilities": SERVER_CAPABILITIES
        }
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        logger.error(traceback.format_exc())
        # Return an empty response instead of raising to avoid client-side errors
        return {
            "serverInfo": {
                "name": SERVER_INFO["name"],
                "version": SERVER_INFO["version"]
            },
            "capabilities": SERVER_CAPABILITIES
        }

# Add a startup function that can be called when the server starts
async def startup():
    """Run startup tasks for the server."""
    # Check if AWS CLI is installed
    logger.info("Running startup checks...")
    if not await check_aws_cli_installed():
        logger.error("AWS CLI is not installed or not in PATH. Please install AWS CLI.")
        sys.exit(1)
    logger.info("AWS CLI is installed and available")


@mcp.tool()
async def describe_command(service: str, command: str | None = None) -> CommandHelpResult:
    """Get AWS CLI command documentation.

    Retrieves the help documentation for a specified AWS service or command
    by executing the 'aws <service> [command] help' command.

    Args:
        service: AWS service (e.g., s3, ec2)
        command: Command within the service (optional)

    Returns:
        CommandHelpResult containing the help text
    """
    logger.info(f"Getting documentation for service: {service}, command: {command or 'None'}")

    try:
        # Reuse the get_command_help function from cli_executor
        result = await get_command_help(service, command)
        return result
    except Exception as e:
        logger.error(f"Unexpected error in describe_command: {e}", exc_info=True)
        return CommandHelpResult(help_text=f"Error retrieving help: {str(e)}")


@mcp.tool()
async def execute_command(command: str) -> CommandResult:
    """Execute an AWS CLI command.

    Validates, executes, and processes the results of an AWS CLI command,
    handling errors and formatting the output for better readability.

    Args:
        command: Complete AWS CLI command to execute

    Returns:
        CommandResult containing output and status
    """
    logger.info(f"Executing command: {command}")

    try:
        result = await execute_aws_command(command)

        # Format the output for better readability
        if result["status"] == "success":
            result["output"] = format_aws_output(result["output"])
            logger.debug("Successfully formatted command output")

        return CommandResult(status=result["status"], output=result["output"])
    except CommandValidationError as e:
        logger.warning(f"Command validation error: {e}")
        return CommandResult(status="error", output=f"Command validation error: {str(e)}")
    except CommandExecutionError as e:
        logger.warning(f"Command execution error: {e}")
        return CommandResult(status="error", output=f"Command execution error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in execute_command: {e}", exc_info=True)
        return CommandResult(status="error", output=f"Unexpected error: {str(e)}")
