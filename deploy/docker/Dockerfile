FROM python:3.13-slim AS builder
LABEL maintainer="alexei-led" \
      description="AWS Multi-Command Proxy Server"

# Set working directory
WORKDIR /build

# Install minimal dependencies required for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    curl \
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
    && ./aws/install --bin-dir /build/bin --install-dir /build/aws-cli \
    && rm -rf awscliv2.zip aws

# Copy all project files needed for installation
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Install dependencies
RUN pip install --no-cache-dir .

# Start from a clean image for the final stage
FROM python:3.13-slim

# Copy installed AWS CLI from builder
COPY --from=builder /build/aws-cli /usr/local/aws-cli
COPY --from=builder /build/bin/aws /usr/local/bin/aws
COPY --from=builder /build/bin/aws_completer /usr/local/bin/aws_completer

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    less \
    groff \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application code
COPY README.md LICENSE ./
COPY src/ ./src/
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Create non-root user
RUN useradd -m -s /bin/bash -u 10001 appuser

# Set proper ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add metadata
LABEL org.opencontainers.image.source="https://github.com/alexei-led/aws-mcp-server" \
      org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
      org.opencontainers.image.version="1.0.0"

# Expose the service port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set command to run the server
ENTRYPOINT ["python", "-m", "aws_mcp_server", "--tcp", "--host", "0.0.0.0"]