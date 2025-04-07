"""Live AWS integration tests for the AWS MCP Server.

These tests connect to real AWS resources and require:
1. AWS CLI installed locally
2. AWS credentials configured with access to test resources
3. The --run-integration flag when running pytest

Note: The tests that require an S3 bucket will create a temporary bucket
if AWS_TEST_BUCKET environment variable is not set.
"""

import asyncio
import json
import logging
import os
import time
import uuid

import pytest

from aws_mcp_server.server import describe_command, execute_command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAWSLiveIntegration:
    """Integration tests that interact with real AWS services.

    These tests require AWS credentials and actual AWS resources.
    They verify the AWS MCP Server can properly interact with AWS.
    """

    # Apply the integration marker to each test method instead of the class

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "service,command,expected_content",
        [
            ("s3", None, ["description", "ls", "cp", "mv"]),
            ("ec2", None, ["description", "run-instances", "describe-instances"]),
            # The AWS CLI outputs help with control characters that complicate exact matching
            # We need to use content that will be in the help text even with the escape characters
            ("s3", "ls", ["list s3 objects", "options", "examples"]),
        ],
    )
    async def test_describe_command(self, ensure_aws_credentials, service, command, expected_content):
        """Test getting help for various AWS commands."""
        result = await describe_command(service=service, command=command, ctx=None)

        # Verify we got a valid response
        assert isinstance(result, dict)
        assert "help_text" in result

        # Check for expected content in the help text (case-insensitive)
        help_text = result["help_text"].lower()
        for content in expected_content:
            assert content.lower() in help_text, f"Expected '{content}' in {service} {command} help text"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_s3_buckets(self, ensure_aws_credentials):
        """Test listing S3 buckets."""
        result = await execute_command(command="aws s3 ls", timeout=None, ctx=None)

        # Verify the result format
        assert isinstance(result, dict)
        assert "status" in result
        assert "output" in result
        assert result["status"] == "success"

        # Output should be a string containing the bucket listing (or empty if no buckets)
        assert isinstance(result["output"], str)

        logger.info(f"S3 bucket list result: {result['output']}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_s3_operations_with_test_bucket(self, ensure_aws_credentials):
        """Test S3 operations using a test bucket.

        This test:
        1. Creates a temporary bucket
        2. Creates a test file
        3. Uploads it to S3
        4. Lists the bucket contents
        5. Downloads the file with a different name
        6. Verifies the downloaded content
        7. Cleans up all test files and the bucket
        """
        # Get region from environment or use default
        region = os.environ.get("AWS_TEST_REGION", os.environ.get("AWS_REGION", "us-east-1"))
        print(f"Using AWS region: {region}")

        # Generate a unique bucket name
        timestamp = int(time.time())
        random_id = str(uuid.uuid4())[:8]
        bucket_name = f"aws-mcp-test-{timestamp}-{random_id}"

        test_file_name = "test_file.txt"
        test_file_content = "This is a test file for AWS MCP Server integration tests"
        downloaded_file_name = "test_file_downloaded.txt"

        try:
            # Create the bucket
            create_cmd = f"aws s3 mb s3://{bucket_name} --region {region}"
            result = await execute_command(command=create_cmd, timeout=None, ctx=None)
            assert result["status"] == "success", f"Failed to create bucket: {result['output']}"

            # Wait for bucket to be fully available
            await asyncio.sleep(3)

            # Create a local test file
            with open(test_file_name, "w") as f:
                f.write(test_file_content)

            # Upload the file to S3
            upload_result = await execute_command(
                command=f"aws s3 cp {test_file_name} s3://{bucket_name}/{test_file_name} --region {region}", timeout=None, ctx=None
            )
            assert upload_result["status"] == "success"

            # List the bucket contents
            list_result = await execute_command(command=f"aws s3 ls s3://{bucket_name}/ --region {region}", timeout=None, ctx=None)
            assert list_result["status"] == "success"
            assert test_file_name in list_result["output"]

            # Download the file with a different name
            download_result = await execute_command(
                command=f"aws s3 cp s3://{bucket_name}/{test_file_name} {downloaded_file_name} --region {region}", timeout=None, ctx=None
            )
            assert download_result["status"] == "success"

            # Verify the downloaded file content
            with open(downloaded_file_name, "r") as f:
                downloaded_content = f.read()
            assert downloaded_content == test_file_content

        finally:
            # Clean up local files
            for file_name in [test_file_name, downloaded_file_name]:
                if os.path.exists(file_name):
                    os.remove(file_name)

            # Clean up: Remove files from S3
            await execute_command(command=f"aws s3 rm s3://{bucket_name} --recursive --region {region}", timeout=None, ctx=None)

            # Delete the bucket
            await execute_command(command=f"aws s3 rb s3://{bucket_name} --region {region}", timeout=None, ctx=None)

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "command,expected_attributes,description",
        [
            # Test JSON formatting with EC2 regions
            ("aws ec2 describe-regions --output json", {"json_key": "Regions", "expected_type": list}, "JSON output with EC2 regions"),
            # Test JSON formatting with S3 buckets (may be empty but should be valid JSON)
            ("aws s3api list-buckets --output json", {"json_key": "Buckets", "expected_type": list}, "JSON output with S3 buckets"),
        ],
    )
    async def test_aws_json_output_formatting(self, ensure_aws_credentials, command, expected_attributes, description):
        """Test JSON output formatting from various AWS commands."""
        result = await execute_command(command=command, timeout=None, ctx=None)

        assert result["status"] == "success", f"Command failed: {result.get('output', '')}"

        # The output should be valid JSON
        try:
            json_data = json.loads(result["output"])

            # Verify expected JSON structure
            json_key = expected_attributes["json_key"]
            expected_type = expected_attributes["expected_type"]

            assert json_key in json_data, f"Expected key '{json_key}' not found in JSON response"
            assert isinstance(json_data[json_key], expected_type), f"Expected {json_key} to be of type {expected_type.__name__}"

            # Log some info about the response
            logger.info(f"Successfully parsed JSON response for {description} with {len(json_data[json_key])} items")

        except json.JSONDecodeError:
            pytest.fail(f"Output is not valid JSON: {result['output'][:100]}...")

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "command,validation_func,description",
        [
            # Test simple pipe with count
            ("aws ec2 describe-regions --query 'Regions[*].RegionName' --output text | wc -l", lambda output: int(output.strip()) > 0, "Count of AWS regions"),
            # Test pipe with grep and sort
            (
                "aws ec2 describe-regions --query 'Regions[*].RegionName' --output text | grep east | sort",
                lambda output: all("east" in r.lower() for r in output.strip().split("\n")),
                "Filtered and sorted east regions",
            ),
            # Test more complex pipe with multiple operations
            (
                "aws ec2 describe-regions --output json | grep RegionName | head -3 | wc -l",
                lambda output: int(output.strip()) <= 3,
                "Limited region output with multiple pipes",
            ),
        ],
    )
    async def test_piped_commands(self, ensure_aws_credentials, command, validation_func, description):
        """Test execution of various piped commands with AWS CLI and Unix utilities."""
        result = await execute_command(command=command, timeout=None, ctx=None)

        assert result["status"] == "success", f"Command failed: {result.get('output', '')}"

        # Validate the output using the provided validation function
        assert validation_func(result["output"]), f"Output validation failed for {description}"

        # Log success
        logger.info(f"Successfully executed piped command for {description}: {result['output'][:50]}...")
