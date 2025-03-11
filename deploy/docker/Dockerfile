FROM python:3.13-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    less \
    groff \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2 based on architecture
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"; \
    else \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"; \
    fi \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir -e .

# Install the official MCP CLI tools
RUN pip install "mcp[cli]"

# Set command to run the server
# Option 1: Using the built-in server
ENTRYPOINT ["python", "-m", "aws_mcp_server", "--tcp", "--host", "0.0.0.0"]

# Option 2: Using MCP CLI (uncomment below and comment above to use this option)
# ENTRYPOINT ["mcp", "run", "src/aws_mcp_server/server.py", "--host", "0.0.0.0"]