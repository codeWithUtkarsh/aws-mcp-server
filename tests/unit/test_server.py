"""Tests for the FastMCP server implementation."""

from unittest.mock import AsyncMock, patch

import pytest

from aws_mcp_server.server import describe_command, execute_command
from aws_mcp_server.utils.cli_executor import CommandExecutionError, CommandValidationError


@pytest.mark.asyncio
async def test_describe_command():
    """Test the describe_command tool."""
    # Mock the get_command_help function instead of execute_aws_command
    with patch("aws_mcp_server.server.get_command_help", new_callable=AsyncMock) as mock_get_help:
        mock_get_help.return_value = {"help_text": "Test help text"}

        # Call the tool with service only
        result = await describe_command(service="s3")
        assert result == {"help_text": "Test help text"}
        mock_get_help.assert_called_with("s3", None)

        # Call the tool with service and command
        result = await describe_command(service="s3", command="ls")
        assert result == {"help_text": "Test help text"}
        mock_get_help.assert_called_with("s3", "ls")


@pytest.mark.asyncio
async def test_execute_command_success():
    """Test the execute_command tool with successful execution."""
    # Mock the execute_aws_command function
    with patch("aws_mcp_server.server.execute_aws_command", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"status": "success", "output": "Test output"}

        # Also mock the format_aws_output function
        with patch("aws_mcp_server.server.format_aws_output", return_value="Formatted output") as mock_format:
            # Call the tool
            result = await execute_command(command="aws s3 ls")

            assert result["status"] == "success"
            assert result["output"] == "Formatted output"
            mock_execute.assert_called_with("aws s3 ls")
            mock_format.assert_called_with("Test output")


@pytest.mark.asyncio
async def test_execute_command_validation_error():
    """Test the execute_command tool with validation error."""
    # Mock the execute_aws_command function to raise validation error
    with patch("aws_mcp_server.server.execute_aws_command", side_effect=CommandValidationError("Invalid command")) as mock_execute:
        # Call the tool
        result = await execute_command(command="not aws")

        assert result["status"] == "error"
        assert "Command validation error" in result["output"]
        mock_execute.assert_called_with("not aws")


@pytest.mark.asyncio
async def test_execute_command_execution_error():
    """Test the execute_command tool with execution error."""
    # Mock the execute_aws_command function to raise execution error
    with patch("aws_mcp_server.server.execute_aws_command", side_effect=CommandExecutionError("Execution failed")) as mock_execute:
        # Call the tool
        result = await execute_command(command="aws s3 ls")

        assert result["status"] == "error"
        assert "Command execution error" in result["output"]
        mock_execute.assert_called_with("aws s3 ls")
