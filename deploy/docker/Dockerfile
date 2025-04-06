# Multi-stage build with platform-specific configuration
ARG PYTHON_VERSION=3.13-slim
ARG VERSION

# =========== BUILDER STAGE ===========
FROM --platform=${TARGETPLATFORM} python:${PYTHON_VERSION} AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /build

# Create version file from ARG for build environment without Git
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Make sure we have the version file available (VERSION arg is passed from makefile/GitHub Actions)
# This allows builds to work without git history but with proper version
RUN mkdir -p src/aws_mcp_server
RUN echo '"""' > src/aws_mcp_server/_version.py && \
    echo "Version file for Docker build" >> src/aws_mcp_server/_version.py && \
    echo '"""' >> src/aws_mcp_server/_version.py && \
    echo "" >> src/aws_mcp_server/_version.py && \
    echo "__version__ = \"${VERSION}\"" >> src/aws_mcp_server/_version.py && \
    echo "version = \"${VERSION}\"" >> src/aws_mcp_server/_version.py

# Install plain dependencies without setuptools_scm
RUN pip install --no-cache-dir wheel fastmcp mcp && \
    pip wheel --no-cache-dir --wheel-dir=/wheels fastmcp mcp

# =========== FINAL STAGE ===========
FROM --platform=${TARGETPLATFORM} python:${PYTHON_VERSION}

# Set build arguments
ARG TARGETPLATFORM
ARG TARGETARCH
ARG BUILD_DATE
ARG VERSION

# Add metadata
LABEL maintainer="alexei-led" \
      description="AWS Multi-Command Proxy Server" \
      org.opencontainers.image.source="https://github.com/alexei-led/aws-mcp-server" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}"

# Step 1: Install system packages - keeping all original packages
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
        curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"; \
    else \
        curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"; \
    fi \
    && unzip -q awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

# Step 3: Install Session Manager plugin based on architecture
RUN if [ "${TARGETARCH}" = "arm64" ]; then \
        curl -sSL "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_arm64/session-manager-plugin.deb" -o "session-manager-plugin.deb"; \
    else \
        curl -sSL "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"; \
    fi \
    && dpkg -i session-manager-plugin.deb 2>/dev/null || apt-get -f install -y \
    && rm session-manager-plugin.deb

# Set up application directory, user, and permissions
RUN useradd -m -s /bin/bash -u 10001 appuser \
    && mkdir -p /app/logs && chmod 777 /app/logs \
    && mkdir -p /home/appuser/.aws && chmod 700 /home/appuser/.aws

WORKDIR /app

# Copy just the source code we need
COPY README.md LICENSE ./
COPY src/ ./src/

# Copy wheels and version file from builder
COPY --from=builder /wheels /wheels
COPY --from=builder /build/src/aws_mcp_server/_version.py ./src/aws_mcp_server/

# Install dependencies and copy the code
RUN pip install --no-cache-dir --no-index --find-links=/wheels fastmcp mcp && \
    rm -rf /wheels

# Set ownership after all files have been copied - avoid .aws directory
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set all environment variables in one layer
ENV HOME="/home/appuser" \
    PATH="/usr/local/bin:/usr/local/aws-cli/v2/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    AWS_MCP_TRANSPORT=stdio

# Expose the service port
EXPOSE 8000

# Set command to run the server
ENTRYPOINT ["python", "-m", "aws_mcp_server"]