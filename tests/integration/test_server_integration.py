"""Mocked integration tests for AWS MCP Server functionality.

These tests use mocks rather than actual AWS CLI calls, so they can
run without AWS credentials or AWS CLI installed.
"""

import json
import logging
import os
from unittest.mock import patch

import pytest

from aws_mcp_server.server import describe_command, execute_command, mcp

# Enable debug logging for tests
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def mock_aws_environment():
    """Set up mock AWS environment variables for testing."""
    original_env = os.environ.copy()
    os.environ["AWS_PROFILE"] = "test-profile"
    os.environ["AWS_REGION"] = "us-west-2"
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mcp_client():
    """Return a FastMCP client for testing."""
    return mcp


class TestServerIntegration:
    """Integration tests for the AWS MCP Server using mocks.

    These tests use mocks and don't actually call AWS, but they test
    more of the system together than unit tests. They don't require the
    integration marker since they can run without AWS CLI or credentials."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "service,command,mock_response,expected_content",
        [
            # Basic service help
            ("s3", None, {"help_text": "AWS S3 HELP\nCommands:\ncp\nls\nmv\nrm\nsync"}, ["AWS S3 HELP", "Commands", "ls", "sync"]),
            # Command-specific help
            (
                "ec2",
                "describe-instances",
                {"help_text": "DESCRIPTION\n  Describes the specified instances.\n\nSYNOPSIS\n  describe-instances\n  [--instance-ids <value>]"},
                ["DESCRIPTION", "SYNOPSIS", "instance-ids"],
            ),
            # Help for a different service
            ("lambda", "list-functions", {"help_text": "LAMBDA LIST-FUNCTIONS\nLists your Lambda functions"}, ["LAMBDA", "LIST-FUNCTIONS", "Lists"]),
        ],
    )
    @patch("aws_mcp_server.server.get_command_help")
    async def test_describe_command_integration(self, mock_get_help, mock_aws_environment, service, command, mock_response, expected_content):
        """Test the describe_command functionality with table-driven tests."""
        # Configure the mock response
        mock_get_help.return_value = mock_response

        # Call the describe_command function
        result = await describe_command(service=service, command=command, ctx=None)

        # Verify the results
        assert "help_text" in result
        for content in expected_content:
            assert content in result["help_text"], f"Expected '{content}' in help text"

        # Verify the mock was called correctly
        mock_get_help.assert_called_once_with(service, command)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "command,mock_response,expected_result,timeout",
        [
            # JSON output test
            (
                "aws s3 ls --output json",
                {"status": "success", "output": json.dumps({"Buckets": [{"Name": "test-bucket", "CreationDate": "2023-01-01T00:00:00Z"}]})},
                {"status": "success", "contains": ["Buckets", "test-bucket"]},
                None,
            ),
            # Text output test
            (
                "aws ec2 describe-instances --query 'Reservations[*]' --output text",
                {"status": "success", "output": "i-12345\trunning\tt2.micro"},
                {"status": "success", "contains": ["i-12345", "running"]},
                None,
            ),
            # Test with custom timeout
            ("aws rds describe-db-instances", {"status": "success", "output": "DB instances list"}, {"status": "success", "contains": ["DB instances"]}, 60),
            # Error case
            (
                "aws s3 ls --invalid-flag",
                {"status": "error", "output": "Unknown options: --invalid-flag"},
                {"status": "error", "contains": ["--invalid-flag"]},
                None,
            ),
            # Piped command
            (
                "aws s3api list-buckets --query 'Buckets[*].Name' --output text | sort",
                {"status": "success", "output": "bucket1\nbucket2\nbucket3"},
                {"status": "success", "contains": ["bucket1", "bucket3"]},
                None,
            ),
        ],
    )
    @patch("aws_mcp_server.server.execute_aws_command")
    async def test_execute_command_scenarios(self, mock_execute, mock_aws_environment, command, mock_response, expected_result, timeout):
        """Test execute_command with various scenarios using table-driven tests."""
        # Configure the mock response
        mock_execute.return_value = mock_response

        # Call the execute_command function
        result = await execute_command(command=command, timeout=timeout, ctx=None)

        # Verify status
        assert result["status"] == expected_result["status"]

        # Verify expected content is present
        for content in expected_result["contains"]:
            assert content in result["output"], f"Expected '{content}' in output"

        # Verify the mock was called correctly
        mock_execute.assert_called_once_with(command, timeout)
