"""Test file to verify AWS integration setup works correctly."""

import asyncio
import os
import pytest
import subprocess
import time
import uuid

from aws_mcp_server.server import execute_command


def test_aws_cli_installed():
    """Test that AWS CLI is installed."""
    result = subprocess.run(['aws', '--version'], stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, check=False)
    assert result.returncode == 0, "AWS CLI is not installed or not in PATH"


def test_aws_credentials_exist():
    """Test that AWS credentials exist."""
    result = subprocess.run(['aws', 'sts', 'get-caller-identity'],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    assert result.returncode == 0, f"AWS credentials check failed: {result.stderr.decode('utf-8')}"


@pytest.mark.asyncio
async def test_aws_execute_command():
    """Test that we can execute a basic AWS command."""
    # Test a simple S3 bucket listing command
    result = await execute_command(command="aws s3 ls", timeout=None, ctx=None)
    
    # Verify the result
    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] == "success", f"Command failed: {result.get('output', '')}"


@pytest.mark.asyncio
async def test_aws_bucket_creation():
    """Test that we can create and delete a bucket."""
    # Import the required functions
    import uuid
    import time
    
    # Generate a bucket name
    timestamp = int(time.time())
    random_id = str(uuid.uuid4())[:8]
    bucket_name = f"aws-mcp-test-{timestamp}-{random_id}"
    
    # Get region from environment or use default
    region = os.environ.get("AWS_TEST_REGION", os.environ.get("AWS_REGION", "us-east-1"))
    
    try:
        # Create bucket with region specification
        create_result = await execute_command(
            command=f"aws s3 mb s3://{bucket_name} --region {region}", 
            timeout=None, 
            ctx=None
        )
        assert create_result["status"] == "success", f"Failed to create bucket: {create_result['output']}"
        
        # Verify bucket exists
        await asyncio.sleep(3)  # Wait for bucket to be fully available
        list_result = await execute_command(
            command="aws s3 ls", 
            timeout=None, 
            ctx=None
        )
        assert bucket_name in list_result["output"], "Bucket was not found in bucket list"
        
    finally:
        # Clean up - delete the bucket
        await execute_command(
            command=f"aws s3 rb s3://{bucket_name} --region {region}", 
            timeout=None, 
            ctx=None
        )