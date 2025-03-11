"""Tests for the CLI executor module."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from aws_mcp_server.utils.cli_executor import CommandExecutionError, CommandValidationError, execute_aws_command, get_command_help


@pytest.mark.asyncio
async def test_execute_aws_command_validation_error():
    """Test that execute_aws_command raises error for invalid commands."""
    # Command doesn't start with 'aws'
    with pytest.raises(CommandValidationError):
        await execute_aws_command("s3 ls")

    # Empty command
    with pytest.raises(CommandValidationError):
        await execute_aws_command("")


@pytest.mark.asyncio
async def test_execute_aws_command_success():
    """Test successful command execution."""
    with patch("asyncio.create_subprocess_shell", new_callable=AsyncMock) as mock_subprocess:
        # Mock a successful process
        process_mock = AsyncMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = (b"Success output", b"")
        mock_subprocess.return_value = process_mock

        result = await execute_aws_command("aws s3 ls")

        assert result["status"] == "success"
        assert result["output"] == "Success output"


@pytest.mark.asyncio
async def test_execute_aws_command_error():
    """Test command execution error."""
    with patch("asyncio.create_subprocess_shell", new_callable=AsyncMock) as mock_subprocess:
        # Mock a failed process
        process_mock = AsyncMock()
        process_mock.returncode = 1
        process_mock.communicate.return_value = (b"", b"Error message")
        mock_subprocess.return_value = process_mock

        result = await execute_aws_command("aws s3 ls")

        assert result["status"] == "error"
        assert result["output"] == "Error message"


@pytest.mark.asyncio
async def test_execute_aws_command_timeout():
    """Test command timeout."""
    with patch("asyncio.create_subprocess_shell", new_callable=AsyncMock) as mock_subprocess:
        # Mock a process that times out
        process_mock = AsyncMock()
        process_mock.communicate.side_effect = asyncio.TimeoutError()
        mock_subprocess.return_value = process_mock

        # Mock a regular function instead of an async one for process.kill
        process_mock.kill = lambda: None

        with pytest.raises(CommandExecutionError):
            await execute_aws_command("aws s3 ls", timeout=1)


@pytest.mark.asyncio
async def test_get_command_help():
    """Test getting command help."""
    with patch("aws_mcp_server.utils.cli_executor.execute_aws_command", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"status": "success", "output": "Help text"}

        result = await get_command_help("s3", "ls")

        assert result["help_text"] == "Help text"
        mock_execute.assert_called_once_with("aws s3 ls help")
