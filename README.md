# AWS Model Context Protocol (MCP) Server

A lightweight service that enables AI assistants to execute AWS CLI commands through the Model Context Protocol (MCP).

## Overview

The AWS MCP Server provides a bridge between MCP-aware AI assistants (like Claude Desktop, Cursor, Windsurf) and the AWS CLI. Built with the official MCP Python SDK, it enables these assistants to:

1. **Retrieve AWS CLI documentation** - Get detailed help on AWS services and commands
2. **Execute AWS CLI commands** - Run commands and receive formatted results optimized for AI consumption

## Features

- **MCP Protocol Support** - Fully implements the standard Model Context Protocol
- **Command Documentation** - Detailed help information for AWS CLI commands
- **Command Execution** - Execute AWS CLI commands and return human-readable results
- **Docker Integration** - Simple deployment through containerization with multi-architecture support (AMD64/x86_64 and ARM64)
- **AWS Authentication** - Leverages existing AWS credentials on the host machine

## Requirements

- Docker (default) or Python 3.13+ (and AWS CLI installed locally)
- AWS credentials configured

## Installation

### Option 1: Using Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/alexei-led/aws-mcp-server.git
cd aws-mcp-server

# Build and run Docker container
docker compose -f deploy/docker/docker-compose.yml up -d
```

The Docker image supports both AMD64/x86_64 (Intel/AMD) and ARM64 (Apple Silicon M1-M4, AWS Graviton) architectures.

> **Note**: The official image from GitHub Packages is multi-architecture and will automatically use the appropriate version for your system.
>
> ```bash
> # Use the latest stable version
> docker pull ghcr.io/alexei-led/aws-mcp-server:latest
> 
> # Or pin to a specific version (recommended for production)
> docker pull ghcr.io/alexei-led/aws-mcp-server:1.0.0
> 
> # Or use major.minor version for automatic patch updates
> docker pull ghcr.io/alexei-led/aws-mcp-server:1.0
> ```
>
> **Docker Image Tags**:
>
> - `latest`: Latest stable release
> - `x.y.z` (e.g., `1.0.0`): Specific version (recommended for production)
> - `x.y` (e.g., `1.0`): Specific major and minor version
> - `x` (e.g., `1`): Specific major version
> - `sha-abc123`: Development builds, tagged with Git commit SHA

### Option 2: Using Python

```bash
# Clone repository
git clone https://github.com/alexei-led/aws-mcp-server.git
cd aws-mcp-server

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Run the server
python -m aws_mcp_server
```

## Development

### Basic Development Setup

```bash
# Install only runtime dependencies
pip install -e .

# Install test dependencies
pip install -e ".[test]"

# Install linting dependencies
pip install -e ".[lint]"

# Install all development dependencies
pip install -e ".[dev]"

# Run unit tests (no AWS credentials required)
pytest -k "not integration"

# Run linting
ruff check src/ tests/

# Run formatting
ruff format src/ tests/

# Type checking is handled by Pylance in VS Code
```

### Integration Testing

The project includes integration tests that verify AWS MCP Server works correctly with actual AWS resources. These tests are skipped by default in CI/CD pipelines and when running regular tests to avoid requiring AWS credentials.

#### Requirements for Integration Tests

1. AWS CLI installed locally
2. AWS credentials configured with appropriate permissions
3. An S3 bucket for testing
4. EC2 describe-regions permission (available in all AWS accounts)

#### Setting Up for Integration Tests

1. Create an S3 bucket for testing (or use an existing one)
2. Set the environment variable with your test bucket name:

   ```bash
   export AWS_TEST_BUCKET=your-test-bucket-name
   ```

3. Ensure your AWS credentials are configured:

   ```bash
   aws configure
   # OR
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=your_region
   ```

#### Running Integration Tests

```bash
# Run all tests including integration tests
pytest --run-integration

# Run only integration tests
pytest --run-integration -m integration
```

The integration tests will:

- Test AWS CLI help command functionality
- List S3 buckets in your account
- Create, upload, download, and delete a test file in your specified S3 bucket
- Test JSON output formatting with AWS commands

> **Note**: Integration tests are designed to clean up after themselves, but if a test fails unexpectedly, you might need to manually remove test files from your S3 bucket.

## Usage

After starting the server, MCP-aware AI assistants can connect to it and use two primary tools:

### 1. describe_command

Retrieves documentation for AWS CLI commands:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/describe_command",
  "params": {
    "service": "s3",
    "command": "ls"  // Optional
  }
}
```

### 2. execute_command

Executes AWS CLI commands:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/execute_command",
  "params": {
    "command": "aws s3 ls"
  }
}
```

## Security

- The server uses AWS credentials from the host machine
- All commands are validated before execution
- Timeout limits prevent long-running commands
- Commands must start with the 'aws' prefix

## CI/CD Pipelines

The project includes GitHub Actions workflows:

- **CI**: Runs on every PR and push to main branch
- **Development**: Runs on pushes to non-main branches and manual dispatch
- **Release**: Publishes multi-architecture Docker image (AMD64 and ARM64) and PyPI package when a new release is created

## Claude Desktop Integration

The AWS MCP Server can be easily integrated with Claude Desktop to enable AI-assisted AWS CLI operations.

### Setting Up Claude Desktop with AWS MCP Server

#### Method 1: Using the UI Settings

1. **Install Claude Desktop**:
   - Download and install [Claude Desktop](https://claude.ai/download) for your platform

2. **Start the AWS MCP Server**:
   - Start the server using Docker:
     ```bash
     docker compose -f deploy/docker/docker-compose.yml up -d
     ```
   - Or run it directly:
     ```bash
     python -m aws_mcp_server --tcp --host 0.0.0.0 --port 8000
     ```

3. **Connect Claude Desktop to the AWS MCP Server**:
   - Open Claude Desktop
   - Click on the settings icon (⚙️) in the top right corner
   - Select "Servers" from the menu
   - Click "Add Server"
   - Enter the following details:
     - **Name**: AWS CLI
     - **URL**: `http://localhost:8000` (or the appropriate host/port if different)
     - **Description**: AWS CLI commands and documentation
   - Click "Add Server"

#### Method 2: Using the Configuration File

1. **Locate the Claude Desktop configuration file**:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Edit the configuration file** to include AWS MCP Server as a Docker container:
   ```json
   {
     "mcpServers": {
       "aws": {
         "command": "docker",
         "args": [
           "run",
           "-i",
           "--rm",
           "-v",
           "/Users/yourusername/.aws:/root/.aws:ro",
           "ghcr.io/alexei-led/aws-mcp-server:latest"
         ]
       }
     }
   }
   ```

   > **Note for macOS/Linux users**: Replace `/Users/yourusername` with your actual home directory path. Do not use environment variables like `$HOME` as they won't be expanded correctly.
   > **Note for Windows users**: Use the appropriate path format for your AWS credentials location, for example:
   > ```json
   > {
   >   "mcpServers": {
   >     "aws": {
   >       "command": "docker",
   >       "args": [
   >         "run",
   >         "-i",
   >         "--rm",
   >         "-v",
   >         "C:/Users/yourusername/.aws:/root/.aws:ro",
   >         "ghcr.io/alexei-led/aws-mcp-server:latest"
   >       ]
   >     }
   >   }
   > }
   > ```

   This configuration:
   - Uses the official AWS MCP Server Docker image
   - Mounts your local AWS credentials (read-only) into the container
   - Runs the container on demand and removes it after use

3. **Restart Claude Desktop** after updating the configuration
   - After restarting, you should see a hammer 🔨 icon in the bottom right corner of the input box
   - This indicates that the AWS MCP Server is available for use

4. **Using AWS CLI with Claude**:
   - Start a new conversation in Claude Desktop
   - Claude will now have access to the AWS MCP Server tools
   - You can ask Claude to:
     - Get documentation for AWS services: "Show me documentation for AWS S3 commands"
     - Execute AWS CLI commands: "List my S3 buckets" or "Show me my EC2 instances in us-west-2"
     - Help with AWS CLI syntax: "How do I copy files between S3 buckets?"

### Example Interactions

**Getting AWS CLI Documentation**:
```
User: What are the available options for the AWS S3 cp command?

Claude: Let me get that information for you.

[Claude uses the describe_command tool to fetch AWS S3 cp documentation]

The AWS S3 cp command has the following options:

NAME
    cp - Copies a local file or S3 object to another location locally or in S3.

SYNOPSIS
    cp <LocalPath> <S3Uri> or <S3Uri> <LocalPath> or <S3Uri> <S3Uri> [--acl <value>] [--cache-control <value>] [--content-disposition <value>] [--content-encoding <value>] [--content-language <value>] [--content-type <value>] [--copy-props <value>] [--dryrun] [--grants <value>] [--only-show-errors] [--quiet] [--recursive] [--request-payer <value>] [--source-region <value>] [--storage-class <value>] [--sse <value>] [--sse-c <value>] [--sse-c-key <value>] [--sse-kms-key-id <value>] [--metadata <value>] [--metadata-directive <value>] [--expected-size <value>] [--page-size <value>] [--checksum <value>] [--checksum-algorithm <value>]
```

**Executing AWS CLI Commands**:
```
User: List my S3 buckets

Claude: I'll list your S3 buckets for you.

[Claude uses the execute_command tool to run "aws s3 ls"]

2023-10-15 14:30:45 my-bucket-1
2023-11-20 09:15:32 my-bucket-2
2024-01-05 11:22:18 my-backup-bucket
```

### Troubleshooting

- **Authentication Issues**: Ensure your AWS credentials are properly configured on the host running the AWS MCP Server
- **Connection Errors**: Verify the server is running and the URL in Claude Desktop is correct
- **Permission Errors**: Check that your AWS credentials have the necessary permissions for the commands you're trying to execute

## License

This project is licensed under the MIT License - see the LICENSE file for details.
