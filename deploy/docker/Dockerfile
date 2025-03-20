# Define global args for both stages
ARG PYTHON_VERSION=3.13-slim
ARG TARGETARCH

# Build stage for Python dependencies
FROM --platform=${BUILDPLATFORM} python:${PYTHON_VERSION} AS builder

# Set working directory
WORKDIR /build

# Copy only files needed for dependency installation first (better caching)
COPY pyproject.toml README.md LICENSE ./

# Create empty src directory for pip install
RUN mkdir -p src/aws_mcp_server
# Copy __init__.py if it exists
RUN touch src/aws_mcp_server/__init__.py

# Install dependencies
RUN pip install --no-cache-dir .

# Copy the actual source code
COPY src/ ./src/

# Final stage
FROM --platform=${TARGETPLATFORM} python:${PYTHON_VERSION}

# Make sure to propagate the build arg to this stage
ARG TARGETARCH

# Step 1: Install system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    curl \
    wget \
    less \
    groff \
    jq \
    gnupg \
    tar \
    gzip \
    zip \
    vim \
    net-tools \
    dnsutils \
    openssh-client \
    grep \
    sed \
    gawk \
    findutils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Step 2: Install AWS CLI based on architecture
RUN if [ "${TARGETARCH}" = "arm64" ]; then \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"; \
    else \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"; \
    fi \
    && unzip -q awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

# Step 3: Install Session Manager plugin based on architecture
RUN if [ "${TARGETARCH}" = "arm64" ]; then \
        curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_arm64/session-manager-plugin.deb" -o "session-manager-plugin.deb"; \
    else \
        curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"; \
    fi \
    && sudo dpkg -i session-manager-plugin.deb \
    && rm session-manager-plugin.deb || true # Ignore error if package is not installed (wrong architecture in AWS S3 bucket)

# Set up application directory, user, and permissions all in one layer
RUN mkdir -p /app/logs && chmod 777 /app/logs \
    && useradd -m -s /bin/bash -u 10001 appuser \
    && mkdir -p /home/appuser/.aws \
    && chmod 700 /home/appuser/.aws

WORKDIR /app

# Copy application code
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Install the package
RUN pip install -e .

# Set ownership after all files have been copied
RUN chown -R appuser:appuser /app /home/appuser/.aws

# Switch to non-root user
USER appuser

# Set all environment variables in one layer
ENV HOME="/home/appuser" \
    PATH="/usr/local/bin:/usr/local/aws/v2/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    AWS_MCP_LOG_DIR=/app/logs

# Add metadata
LABEL maintainer="alexei-led" \
      description="AWS Multi-Command Proxy Server" \
      org.opencontainers.image.source="https://github.com/alexei-led/aws-mcp-server" \
      org.opencontainers.image.version="1.0.0"

# Expose the service port
EXPOSE 8000

# Set command to run the server
ENTRYPOINT ["python", "-m", "aws_mcp_server", "--tcp", "--host", "0.0.0.0"]