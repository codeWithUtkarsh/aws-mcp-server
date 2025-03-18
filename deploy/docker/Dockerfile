FROM python:3.13-slim

LABEL maintainer="alexei-led" \
      description="AWS Multi-Command Proxy Server"

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

# Install the package with all dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -s /bin/bash appuser
USER appuser

# Expose the service port
EXPOSE 8000

# Set command to run the server
ENTRYPOINT ["python", "-m", "aws_mcp_server", "--tcp", "--host", "0.0.0.0"]