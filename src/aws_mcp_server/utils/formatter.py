"""Utilities for formatting AWS CLI output.

This module contains functions to format AWS CLI output for better readability,
including functions to handle JSON, table, and list formats.
"""

import json
import logging
import re
from typing import Optional

# Configure module logger
logger = logging.getLogger(__name__)


def is_json(text: Optional[str]) -> bool:
    """Check if a string is valid JSON.

    Args:
        text: The string to check

    Returns:
        True if the string is valid JSON, False otherwise
    """
    if not text:
        return False
        
    try:
        json.loads(text)
        return True
    except ValueError:
        return False
    except Exception as e:
        logger.debug(f"Unexpected error in is_json check: {e}")
        return False


def format_table_output(text: str) -> str:
    """Format tabular output for better readability.

    This function attempts to detect and format table-like outputs that have
    columns aligned with spaces.

    Args:
        text: The text output to format

    Returns:
        Formatted text
    """
    lines = text.strip().split("\n")
    if len(lines) <= 1:
        return text

    # Check if this looks like a table with header and rows
    formatted_lines = []

    # Add a separator line after the header
    if len(lines) > 1:
        header = lines[0]
        formatted_lines.append(header)
        
        # Create a separator line based on the header columns
        separator = ""
        for _i, char in enumerate(header):
            separator += "-" if char != " " else " "
        formatted_lines.append(separator)
        
        formatted_lines.extend(lines[1:])

    return "\n".join(formatted_lines)


def format_list_output(text: str) -> str:
    """Format list-like output for better readability.

    Improves the formatting of list-like outputs from AWS CLI commands
    by adding bullet points and indentation where appropriate.

    Args:
        text: The text output to format

    Returns:
        Formatted text with improved readability for list data
    """
    # Skip empty input
    if not text or not text.strip():
        return text
        
    lines = text.strip().split("\n")
    formatted_lines = []

    # Skip empty input
    if not lines:
        return text

    try:
        # Process each line individually without the regex pattern check
        for line in lines:
            if line.strip():
                # Get the indentation level
                indent = len(line) - len(line.lstrip())
                indentation = " " * indent
                # Add bullet point after the indentation, but use the content without the indentation
                formatted_line = indentation + "• " + line.lstrip()
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)  # Keep empty lines

        return "\n".join(formatted_lines)
    except Exception as e:
        logger.debug(f"Error formatting list output: {e}")

    # Default fallback
    return text


def format_aws_output(output: Optional[str], format_type: Optional[str] = None) -> Optional[str]:
    """Format AWS CLI output for better readability.

    This function attempts to detect the format of AWS CLI output and format it
    appropriately. It supports JSON, table-like, and list-like formats.

    Args:
        output: The raw output from AWS CLI
        format_type: Optional hint about the format type

    Returns:
        Formatted output with improved readability
    """
    # If empty output, return as is
    if output is None or not output.strip():
        return output

    try:
        # If format_type is specified, use it
        if format_type:
            if format_type.lower() == "json":
                # Pretty-print JSON
                try:
                    json_data = json.loads(output)
                    return json.dumps(json_data, indent=2)
                except ValueError:
                    logger.warning("Failed to parse output as JSON despite format hint")
                    return output
                except Exception as e:
                    logger.warning(f"Unexpected error formatting JSON: {e}")
                    return output
            elif format_type.lower() == "table":
                return format_table_output(output)
            elif format_type.lower() == "list":
                return format_list_output(output)

        # Auto-detect format
        # Try to detect and format JSON
        if output.strip().startswith("{") or output.strip().startswith("["):
            try:
                json_data = json.loads(output)
                return json.dumps(json_data, indent=2)
            except ValueError:
                logger.debug("Output looks like JSON but couldn't be parsed")
            except Exception as e:
                logger.debug(f"Error parsing JSON-like output: {e}")

        # Try to detect IAM list-users and similar outputs
        if "USERS" in output or "USER" in output:
            return format_list_output(output)

        # Try to detect and format table-like output
        if "\n" in output and len(output.strip().split("\n")) > 1:
            if all(len(line.split()) > 1 for line in output.strip().split("\n") if line.strip()):
                # Check if it looks more like a list than a table
                if any(line.strip().startswith("USERS") for line in output.strip().split("\n")):
                    return format_list_output(output)
                return format_table_output(output)
            else:
                return format_list_output(output)

    except Exception as e:
        logger.warning(f"Error formatting AWS output: {e}")
        # Even if formatting fails, return the original output

    # Default: return as is
    return output
