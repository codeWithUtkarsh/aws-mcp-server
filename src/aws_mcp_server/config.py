"""Configuration settings for the AWS MCP Server.

This module contains configuration settings for the AWS MCP Server,
including server information, command execution settings, AWS CLI settings,
and user instructions.

Environment variables:
- AWS_MCP_TIMEOUT: Custom timeout in seconds (default: 30)
- AWS_MCP_MAX_OUTPUT: Maximum output size in characters (default: 10000)
- AWS_PROFILE: AWS profile to use (default: "default")
- AWS_REGION: AWS region to use (default: "")
"""

import os
from pathlib import Path
from typing import Any, Dict

# Server information
SERVER_INFO: Dict[str, str] = {"name": "AWS MCP Server", "version": "1.0.0"}

# Server capabilities
SERVER_CAPABILITIES: Dict[str, Any] = {"tools": {}}

# Command execution settings
DEFAULT_TIMEOUT: int = int(os.environ.get("AWS_MCP_TIMEOUT", "30"))  # Default timeout in seconds
MAX_OUTPUT_SIZE: int = int(os.environ.get("AWS_MCP_MAX_OUTPUT", "10000"))  # Max output size in characters

# AWS CLI settings
AWS_PROFILE: str = os.environ.get("AWS_PROFILE", "default")
AWS_REGION: str = os.environ.get("AWS_REGION", "")

# Instructions displayed to client during initialization
INSTRUCTIONS: str = "Use this server to retrieve AWS CLI documentation and execute AWS CLI commands."

# Application paths
BASE_DIR: Path = Path(__file__).parent.parent.parent
LOG_DIR: Path = BASE_DIR / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True, parents=True)
