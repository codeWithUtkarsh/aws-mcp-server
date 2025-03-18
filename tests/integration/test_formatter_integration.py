"""Integration tests for the formatter module with real AWS CLI output.

These tests use real AWS CLI output patterns to verify the formatter works
with actual AWS CLI output formats.
"""

import json
import subprocess

import pytest

from aws_mcp_server.utils.formatter import format_aws_output


@pytest.mark.integration
def test_format_real_s3_ls_output():
    """Test formatting real AWS S3 ls output."""
    # Skip if AWS CLI is not installed
    try:
        subprocess.run(["aws", "--version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        pytest.skip("AWS CLI not installed")

    # Mock the AWS CLI output instead of actually running it
    mock_s3_ls_output = """2023-01-15 12:34:56 my-test-bucket-1
2023-02-20 09:45:32 my-test-bucket-2
2023-03-10 15:20:18 my-test-bucket-3"""

    # Format the output
    formatted = format_aws_output(mock_s3_ls_output)
    
    # Verify the formatting - should be formatted as a table with separator
    assert "2023-01-15" in formatted
    assert "my-test-bucket-1" in formatted
    assert "---" in formatted  # Should have a separator line


@pytest.mark.integration
def test_format_real_ec2_describe_instances_json():
    """Test formatting real EC2 describe-instances JSON output."""
    # Mock EC2 describe-instances JSON output
    mock_ec2_json = {
        "Reservations": [
            {
                "ReservationId": "r-1234567890abcdef0",
                "Instances": [
                    {
                        "InstanceId": "i-1234567890abcdef0",
                        "InstanceType": "t2.micro",
                        "State": {
                            "Code": 16,
                            "Name": "running"
                        }
                    }
                ]
            }
        ]
    }
    
    # Format the JSON output
    formatted = format_aws_output(json.dumps(mock_ec2_json))
    
    # Verify the formatting - should be pretty-printed JSON
    assert "{\n" in formatted
    assert "  \"Reservations\":" in formatted
    assert "    \"InstanceId\":" in formatted
    
    # Content should be preserved
    parsed = json.loads(formatted)
    assert parsed["Reservations"][0]["Instances"][0]["InstanceId"] == "i-1234567890abcdef0"


@pytest.mark.integration
def test_format_real_iam_list_users():
    """Test formatting real IAM list-users output."""
    # Mock IAM list-users output (text format)
    mock_iam_output = """
USERS   arn:aws:iam::123456789012:user/admin  2023-01-01T00:00:00Z    -       -
USERS   arn:aws:iam::123456789012:user/dev    2023-02-01T00:00:00Z    -       -
USERS   arn:aws:iam::123456789012:user/test   2023-03-01T00:00:00Z    -       -
"""
    
    # Format the output
    formatted = format_aws_output(mock_iam_output)
    
    # Verify the formatting - should be formatted as a list with bullet points
    assert "• USERS" in formatted
    assert "arn:aws:iam::123456789012:user/admin" in formatted


@pytest.mark.integration
def test_format_with_explicit_format_type():
    """Test formatting with explicit format type hints."""
    # Test with table format hint
    table_data = "Col1 Col2\nVal1 Val2\nVal3 Val4"
    formatted_table = format_aws_output(table_data, format_type="table")
    assert "---" in formatted_table
    
    # Test with list format hint
    list_data = "Item1 Description1\nItem2 Description2"
    formatted_list = format_aws_output(list_data, format_type="list")
    assert "• Item1" in formatted_list
    
    # Test with JSON format hint
    json_data = {"key": "value"}
    formatted_json = format_aws_output(json.dumps(json_data), format_type="json")
    assert "{\n  \"key\":" in formatted_json


@pytest.mark.integration
def test_format_error_output():
    """Test formatting AWS CLI error output."""
    # Mock AWS CLI error output
    error_output = "An error occurred (AccessDenied) when calling the ListBuckets operation: Access Denied"
    
    # Format the error output
    formatted = format_aws_output(error_output)
    
    # Error messages should be returned as-is
    assert formatted == error_output
