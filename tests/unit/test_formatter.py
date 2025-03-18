"""Tests for the formatter module."""

import json
from unittest.mock import patch

from aws_mcp_server.utils.formatter import format_aws_output, format_list_output, format_table_output, is_json


def test_is_json():
    """Test the is_json function."""
    assert is_json('{"key": "value"}')
    assert is_json("[1, 2, 3]")
    assert not is_json("Not JSON")
    assert not is_json("{invalid: json}")
    
    # Test edge cases
    assert not is_json("")
    assert not is_json(None)


def test_is_json_with_exception_handling():
    """Test the is_json function's exception handling."""
    with patch("json.loads") as mock_loads:
        mock_loads.side_effect = Exception("Unexpected error")
        assert not is_json('{"key": "value"}')


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
    
    # Empty input should be returned as is
    assert format_table_output("") == ""
    
    # Test with irregular spacing
    irregular_table = "Col1  Col2    Col3\nVal1 Val2  Val3\nLongVal1 Val2 Val3"
    formatted_irregular = format_table_output(irregular_table)
    assert "Col1  Col2    Col3" in formatted_irregular
    assert "---" in formatted_irregular


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
    
    # Test with empty input
    assert format_list_output("") == ""
    
    # Test with indented items
    indented_list = "  Item1 Description1\n    Item2 Description2"
    formatted_indented = format_list_output(indented_list)
    assert "  • Item1 Description1" in formatted_indented
    assert "    • Item2 Description2" in formatted_indented


def test_format_list_output_exception_handling():
    """Test exception handling in format_list_output."""
    with patch("re.match") as mock_match:
        mock_match.side_effect = Exception("Regex error")
        # Should return original text when exception occurs
        assert format_list_output("Item1 Description1") == "Item1 Description1"


def test_format_aws_output_json():
    """Test formatting JSON output."""
    json_data = {"key1": "value1", "key2": ["item1", "item2"]}
    json_text = json.dumps(json_data)

    formatted = format_aws_output(json_text)

    # Should be pretty-printed JSON
    assert "{\n" in formatted
    assert '  "key1":' in formatted
    assert json.loads(formatted) == json_data  # Content should be unchanged
    
    # Test with nested JSON
    nested_json = {"parent": {"child1": "value1", "child2": [1, 2, 3]}}
    nested_text = json.dumps(nested_json)
    formatted_nested = format_aws_output(nested_text)
    assert "{\n" in formatted_nested
    assert "  \"parent\":" in formatted_nested
    assert json.loads(formatted_nested) == nested_json


def test_format_aws_output_with_format_hint():
    """Test formatting with explicit format hint."""
    # Test with JSON hint
    json_data = {"key": "value"}
    json_text = json.dumps(json_data)
    formatted = format_aws_output(json_text, format_type="json")
    assert "{\n" in formatted
    assert json.loads(formatted) == json_data
    
    # Test with table hint
    table_text = "Header1 Header2\nData1 Data2"
    formatted_table = format_aws_output(table_text, format_type="table")
    assert "---" in formatted_table
    
    # Test with list hint
    list_text = "Item1 Description1\nItem2 Description2"
    formatted_list = format_aws_output(list_text, format_type="list")
    assert "• " in formatted_list


def test_format_aws_output_json_error_handling():
    """Test error handling when formatting JSON."""
    # Test with invalid JSON but JSON hint
    with patch("aws_mcp_server.utils.formatter.logger.warning") as mock_warning:
        result = format_aws_output("invalid json", format_type="json")
        assert result == "invalid json"  # Should return original on error
        mock_warning.assert_called()
    
    # Test with unexpected error
    with patch("json.loads") as mock_loads:
        mock_loads.side_effect = Exception("Unexpected error")
        with patch("aws_mcp_server.utils.formatter.logger.warning") as mock_warning:
            result = format_aws_output('{"key": "value"}', format_type="json")
            assert result == '{"key": "value"}'  # Should return original
            mock_warning.assert_called()


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
    
    # Test with empty input
    assert format_aws_output("") == ""
    assert format_aws_output(None) is None


def test_format_aws_output_error_handling():
    """Test error handling in format_aws_output."""
    with patch("aws_mcp_server.utils.formatter.format_table_output") as mock_format:
        mock_format.side_effect = Exception("Formatting error")
        # Should return original text when exception occurs
        assert format_aws_output("test data") == "test data"
