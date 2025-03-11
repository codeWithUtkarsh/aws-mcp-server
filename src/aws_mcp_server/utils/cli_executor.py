"""Utility for executing AWS CLI commands.

This module provides functions to validate and execute AWS CLI commands
with proper error handling, timeouts, and output processing.
"""

import asyncio
import logging
import shlex
from typing import TypedDict

from ..config import DEFAULT_TIMEOUT, MAX_OUTPUT_SIZE

# Configure module logger
logger = logging.getLogger(__name__)


class CommandResult(TypedDict):
    """Type definition for command execution results."""

    status: str
    output: str


class CommandHelpResult(TypedDict):
    """Type definition for command help results."""

    help_text: str


class CommandValidationError(Exception):
    """Exception raised when a command fails validation.

    This exception is raised when a command doesn't meet the
    validation requirements, such as starting with 'aws'.
    """

    pass


class CommandExecutionError(Exception):
    """Exception raised when a command fails to execute.

    This exception is raised when there's an error during command
    execution, such as timeouts or subprocess failures.
    """

    pass


async def execute_aws_command(command: str, timeout: int | None = None) -> CommandResult:
    """Execute an AWS CLI command and return the result.

    Validates, executes, and processes the results of an AWS CLI command,
    handling timeouts and output size limits.

    Args:
        command: The AWS CLI command to execute (must start with 'aws')
        timeout: Optional timeout in seconds (defaults to DEFAULT_TIMEOUT)

    Returns:
        CommandResult containing output and status

    Raises:
        CommandValidationError: If the command is invalid
        CommandExecutionError: If the command fails to execute
    """
    # Validate the command
    cmd_parts = shlex.split(command)
    if not cmd_parts or cmd_parts[0].lower() != "aws":
        raise CommandValidationError("Commands must start with 'aws'")

    # Set timeout
    if timeout is None:
        timeout = DEFAULT_TIMEOUT

    logger.debug(f"Executing AWS command: {command}")

    try:
        # Create subprocess
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        # Wait for the process to complete with timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
            logger.debug(f"Command completed with return code: {process.returncode}")
        except asyncio.TimeoutError as timeout_error:
            logger.warning(f"Command timed out after {timeout} seconds: {command}")
            try:
                # Use synchronous kill to avoid coroutine issues in tests
                process.kill()
            except Exception as e:
                logger.error(f"Error killing process: {e}")
            raise CommandExecutionError(f"Command timed out after {timeout} seconds") from timeout_error

        # Process output
        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")

        # Truncate output if necessary
        if len(stdout_str) > MAX_OUTPUT_SIZE:
            logger.info(f"Output truncated from {len(stdout_str)} to {MAX_OUTPUT_SIZE} characters")
            stdout_str = stdout_str[:MAX_OUTPUT_SIZE] + "\n... (output truncated)"

        if process.returncode != 0:
            logger.warning(f"Command failed with return code {process.returncode}: {command}")
            logger.debug(f"Command error output: {stderr_str}")
            return CommandResult(status="error", output=stderr_str or "Command failed with no error output")

        return CommandResult(status="success", output=stdout_str)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        raise CommandExecutionError(f"Failed to execute command: {str(e)}") from e


async def get_command_help(service: str, command: str | None = None) -> CommandHelpResult:
    """Get help documentation for an AWS CLI service or command.

    Retrieves the help documentation for a specified AWS service or command
    by executing the appropriate AWS CLI help command.

    Args:
        service: The AWS service (e.g., s3, ec2)
        command: Optional command within the service

    Returns:
        CommandHelpResult containing the help text

    Raises:
        CommandExecutionError: If the help command fails
    """
    # Build the help command
    cmd_parts: list[str] = ["aws", service]
    if command:
        cmd_parts.append(command)
    cmd_parts.append("help")

    cmd_str = " ".join(cmd_parts)

    try:
        logger.debug(f"Getting command help for: {cmd_str}")
        result = await execute_aws_command(cmd_str)

        help_text = result["output"] if result["status"] == "success" else f"Error: {result['output']}"

        return CommandHelpResult(help_text=help_text)
    except CommandValidationError as e:
        logger.warning(f"Command validation error while getting help: {e}")
        return CommandHelpResult(help_text=f"Command validation error: {str(e)}")
    except CommandExecutionError as e:
        logger.warning(f"Command execution error while getting help: {e}")
        return CommandHelpResult(help_text=f"Error retrieving help: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while getting command help: {e}", exc_info=True)
        return CommandHelpResult(help_text=f"Error retrieving help: {str(e)}")
