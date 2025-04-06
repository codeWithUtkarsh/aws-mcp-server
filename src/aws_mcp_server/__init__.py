"""AWS Model Context Protocol (MCP) Server.

A lightweight service that enables AI assistants to execute AWS CLI commands through the Model Context Protocol (MCP).
"""

try:
    from ._version import version as __version__
except ImportError:
    # Package is not installed, or during build
    __version__ = "0.0.0+unknown"
