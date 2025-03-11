"""Tests for the formatter module."""

import json

from aws_mcp_server.utils.formatter import format_aws_output, format_list_output, format_table_output, is_json


def test_is_json():
    """Test the is_json function."""
    assert is_json('{"key": "value"}')
    assert is_json("[1, 2, 3]")
    assert not is_json("Not JSON")
    assert not is_json("{invalid: json}")


def test_format_table_output():
    """Test the format_table_output function."""
    table_text = "Header1 Header2 Header3\nData1   Data2   Data3\nData4   Data5   Data6"
    formatted = format_table_output(table_text)

    assert "Header1 Header2 Header3" in formatted
    assert "---" in formatted  # Check for separator line
    assert "Data1   Data2   Data3" in formatted

    # Single line should be returned as is
    single_line = "Just a single line"
    assert format_table_output(single_line) == single_line


def test_format_list_output():
    """Test the format_list_output function."""
    # Tests the improved list formatting with bullet points
    list_text = "Item1 Description1\nItem2 Description2"
    formatted = format_list_output(list_text)

    # Check if bullet points are added
    assert formatted.startswith("• ")
    assert "\n• " in formatted

    # Check if the content is preserved
    assert "Item1 Description1" in formatted
    assert "Item2 Description2" in formatted


def test_format_aws_output_json():
    """Test formatting JSON output."""
    json_data = {"key1": "value1", "key2": ["item1", "item2"]}
    json_text = json.dumps(json_data)

    formatted = format_aws_output(json_text)

    # Should be pretty-printed JSON
    assert "{\n" in formatted
    assert '  "key1":' in formatted
    assert json.loads(formatted) == json_data  # Content should be unchanged


def test_format_aws_output_table():
    """Test formatting table-like output."""
    table_text = "Header1 Header2 Header3\nData1   Data2   Data3\nData4   Data5   Data6"

    formatted = format_aws_output(table_text)

    assert "Header1 Header2 Header3" in formatted
    assert "---" in formatted  # Check for separator line


def test_format_aws_output_plain():
    """Test formatting plain text output."""
    plain_text = "This is just plain text"

    formatted = format_aws_output(plain_text)

    assert formatted == plain_text  # Should be unchanged
