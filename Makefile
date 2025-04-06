.PHONY: help install dev-install test test-unit test-integration test-all test-coverage lint lint-fix format clean docker-build docker-run docker-compose docker-compose-down docker-buildx

# Default target
.DEFAULT_GOAL := help

# Python related commands (with optional uv support)
install: ## Install the package
	pip install -e .

dev-install: ## Install the package with development dependencies
	pip install -e ".[dev]"

lint: ## Run linters (ruff check and format --check)
	ruff check src/ tests/
	ruff format --check src/ tests/

lint-fix: ## Run linters and auto-fix issues where possible
	ruff check --fix src/ tests/
	ruff format src/ tests/

format: ## Format code with ruff
	ruff format src/ tests/

test: ## Run tests excluding integration tests
	pytest -v -m 'not integration'

test-unit: ## Run unit tests only
	pytest -v -m unit

test-integration: ## Run integration tests only (requires AWS credentials)
	pytest -v -m integration

test-all: ## Run all tests including integration tests
	pytest -v -o addopts=""

test-coverage: ## Run tests with coverage report
	pytest --cov=aws_mcp_server --cov-report=term-missing

clean: ## Remove build artifacts and cache directories
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .ruff_cache/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +

# Server run commands
run: ## Run server with default transport (stdio)
	python -m aws_mcp_server

run-sse: ## Run server with SSE transport
	AWS_MCP_TRANSPORT=sse python -m aws_mcp_server

run-mcp-cli: ## Run server with MCP CLI
	mcp run src/aws_mcp_server/server.py

# Docker related commands
docker-build: ## Build Docker image
	docker build -t aws-mcp-server -f deploy/docker/Dockerfile .

docker-run: ## Run server in Docker with AWS credentials mounted
	docker run -p 8000:8000 -v ~/.aws:/home/appuser/.aws:ro aws-mcp-server

docker-compose: ## Run server using Docker Compose
	docker-compose -f deploy/docker/docker-compose.yml up -d

docker-compose-down: ## Stop Docker Compose services
	docker-compose -f deploy/docker/docker-compose.yml down

# Multi-architecture build (requires Docker Buildx)
docker-buildx: ## Build multi-architecture Docker image
	bash scripts/build-multiarch.sh

# GitHub Actions local testing (requires act: https://github.com/nektos/act)
ci-local: ## Run GitHub Actions workflows locally
	act -j test

# Help command
help: ## Display this help message
	@echo "AWS MCP Server Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'