"""Unit tests for the tools module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aws_mcp_server.tools import (
    ALLOWED_UNIX_COMMANDS,
    execute_piped_command,
    is_pipe_command,
    split_pipe_command,
    validate_unix_command,
)


def test_allowed_unix_commands():
    """Test that ALLOWED_UNIX_COMMANDS contains expected commands."""
    # Verify that common Unix utilities are in the allowed list
    common_commands = ["grep", "xargs", "cat", "ls", "wc", "sort", "uniq", "jq"]
    for cmd in common_commands:
        assert cmd in ALLOWED_UNIX_COMMANDS


def test_validate_unix_command():
    """Test the validate_unix_command function."""
    # Test valid commands
    for cmd in ["grep pattern", "ls -la", "wc -l", "cat file.txt"]:
        assert validate_unix_command(cmd), f"Command should be valid: {cmd}"

    # Test invalid commands
    for cmd in ["invalid_cmd", "sudo ls", ""]:
        assert not validate_unix_command(cmd), f"Command should be invalid: {cmd}"


def test_is_pipe_command():
    """Test the is_pipe_command function."""
    # Test commands with pipes
    assert is_pipe_command("aws s3 ls | grep bucket")
    assert is_pipe_command("aws s3api list-buckets | jq '.Buckets[].Name' | sort")

    # Test commands without pipes
    assert not is_pipe_command("aws s3 ls")
    assert not is_pipe_command("aws ec2 describe-instances")

    # Test commands with pipes in quotes (should not be detected as pipe commands)
    assert not is_pipe_command("aws s3 ls 's3://my-bucket/file|other'")
    assert not is_pipe_command('aws ec2 run-instances --user-data "echo hello | grep world"')


def test_split_pipe_command():
    """Test the split_pipe_command function."""
    # Test simple pipe command
    cmd = "aws s3 ls | grep bucket"
    result = split_pipe_command(cmd)
    assert result == ["aws s3 ls", "grep bucket"]

    # Test multi-pipe command
    cmd = "aws s3api list-buckets | jq '.Buckets[].Name' | sort"
    result = split_pipe_command(cmd)
    assert result == ["aws s3api list-buckets", "jq '.Buckets[].Name'", "sort"]

    # Test with quoted pipe symbols (should not split inside quotes)
    cmd = "aws s3 ls 's3://bucket/file|name' | grep 'pattern|other'"
    result = split_pipe_command(cmd)
    assert result == ["aws s3 ls 's3://bucket/file|name'", "grep 'pattern|other'"]

    # Test with double quotes
    cmd = 'aws s3 ls "s3://bucket/file|name" | grep "pattern|other"'
    result = split_pipe_command(cmd)
    assert result == ['aws s3 ls "s3://bucket/file|name"', 'grep "pattern|other"']


@pytest.mark.asyncio
async def test_execute_piped_command_success():
    """Test successful execution of a piped command."""
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_subprocess:
        # Mock the first process in the pipe
        first_process_mock = AsyncMock()
        first_process_mock.returncode = 0
        first_process_mock.communicate.return_value = (b"S3 output", b"")

        # Mock the second process in the pipe
        second_process_mock = AsyncMock()
        second_process_mock.returncode = 0
        second_process_mock.communicate.return_value = (b"Filtered output", b"")

        # Set up the mock to return different values on subsequent calls
        mock_subprocess.side_effect = [first_process_mock, second_process_mock]

        result = await execute_piped_command("aws s3 ls | grep bucket")

        assert result["status"] == "success"
        assert result["output"] == "Filtered output"

        # Verify first command was called with correct args
        mock_subprocess.assert_any_call("aws", "s3", "ls", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        # Verify second command was called with correct args
        mock_subprocess.assert_any_call("grep", "bucket", stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)


@pytest.mark.asyncio
async def test_execute_piped_command_error_first_command():
    """Test error handling in execute_piped_command when first command fails."""
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_subprocess:
        # Mock a failed first process
        process_mock = AsyncMock()
        process_mock.returncode = 1
        process_mock.communicate.return_value = (b"", b"Command failed: aws")
        mock_subprocess.return_value = process_mock

        result = await execute_piped_command("aws s3 ls | grep bucket")

        assert result["status"] == "error"
        assert "Command failed: aws" in result["output"]


@pytest.mark.asyncio
async def test_execute_piped_command_error_second_command():
    """Test error handling in execute_piped_command when second command fails."""
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_subprocess:
        # Mock the first process in the pipe (success)
        first_process_mock = AsyncMock()
        first_process_mock.returncode = 0
        first_process_mock.communicate.return_value = (b"S3 output", b"")

        # Mock the second process in the pipe (failure)
        second_process_mock = AsyncMock()
        second_process_mock.returncode = 1
        second_process_mock.communicate.return_value = (b"", b"Command not found: xyz")

        # Set up the mock to return different values on subsequent calls
        mock_subprocess.side_effect = [first_process_mock, second_process_mock]

        result = await execute_piped_command("aws s3 ls | xyz")

        assert result["status"] == "error"
        assert "Command not found: xyz" in result["output"]


@pytest.mark.asyncio
async def test_execute_piped_command_timeout():
    """Test timeout handling in execute_piped_command."""
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_subprocess:
        # Mock a process that times out
        process_mock = AsyncMock()
        # Use a properly awaitable mock that raises TimeoutError
        communicate_mock = AsyncMock(side_effect=asyncio.TimeoutError())
        process_mock.communicate = communicate_mock
        # Use regular MagicMock since kill() is not an async method
        process_mock.kill = MagicMock()
        mock_subprocess.return_value = process_mock

        result = await execute_piped_command("aws s3 ls | grep bucket", timeout=1)

        assert result["status"] == "error"
        assert "Command timed out after 1 seconds" in result["output"]
        process_mock.kill.assert_called_once()


@pytest.mark.asyncio
async def test_execute_piped_command_exception():
    """Test general exception handling in execute_piped_command."""
    with patch("asyncio.create_subprocess_exec", side_effect=Exception("Test exception")):
        result = await execute_piped_command("aws s3 ls | grep bucket")

        assert result["status"] == "error"
        assert "Failed to execute command" in result["output"]
        assert "Test exception" in result["output"]
