"""Configuration settings for the AWS MCP Server.

This module contains configuration settings for the AWS MCP Server.

Environment variables:
- AWS_MCP_TIMEOUT: Custom timeout in seconds (default: 30)
- AWS_MCP_MAX_OUTPUT: Maximum output size in characters (default: 10000)
- AWS_PROFILE: AWS profile to use (default: "default")
- AWS_REGION: AWS region to use (default: "us-east-1")
"""

import os
from pathlib import Path

# Server information
SERVER_INFO = {
    "name": "AWS MCP Server", 
    "version": "1.0.0"
}

# Command execution settings
DEFAULT_TIMEOUT = int(os.environ.get("AWS_MCP_TIMEOUT", "30"))
MAX_OUTPUT_SIZE = int(os.environ.get("AWS_MCP_MAX_OUTPUT", "10000"))

# AWS CLI settings
AWS_PROFILE = os.environ.get("AWS_PROFILE", "default")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Instructions displayed to client during initialization
INSTRUCTIONS = """
AWS MCP Server provides a simple interface to the AWS CLI.
- Use the describe_command tool to get AWS CLI documentation
- Use the execute_command tool to run AWS CLI commands
"""

# Application paths
BASE_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BASE_DIR / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True, parents=True)
