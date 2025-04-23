"""FastAPI application for AWS MCP Server.

This module provides REST API endpoints for AWS MCP Server functionality.
It exposes AWS CLI operations, security validations, and resource management
through HTTP endpoints.
"""

import logging
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aws_mcp_server.cli_executor import check_aws_cli_installed
from aws_mcp_server.server import aws_cli_help, aws_cli_pipeline
from aws_mcp_server.resources import (
    get_aws_account_info,
    get_aws_environment,
    get_aws_profiles,
    get_region_details
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AWS MCP Server API",
    description="REST API for AWS MCP Server operations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event handler
@app.on_event("startup")
async def startup_event():
    """Perform startup checks when the API server starts."""
    logger.info("Performing startup checks...")
    if not await check_aws_cli_installed():
        logger.error("AWS CLI is not installed or not accessible")
        raise RuntimeError("AWS CLI is not installed or not accessible")
    logger.info("Startup checks completed successfully")

# Pydantic models
class AwsCommandRequest(BaseModel):
    """Model for AWS CLI command requests."""
    command: str
    timeout: Optional[int] = None

class AwsHelpRequest(BaseModel):
    """Model for AWS CLI help requests."""
    service: str
    command: Optional[str] = None

class AwsProfilesResponse(BaseModel):
    """Model for AWS profiles response."""
    profiles: List[Dict[str, Union[str, bool]]]

class AwsRegionResponse(BaseModel):
    """Model for AWS region details response."""
    code: str
    name: str
    geographic_location: Dict[str, str]
    availability_zones: List[Dict[str, str]]
    services: List[Dict[str, str]]
    is_current: bool

# API endpoints
@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "AWS MCP Server API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/aws/execute")
async def execute_aws_command(request: AwsCommandRequest):
    """Execute an AWS CLI command."""
    try:
        result = await aws_cli_pipeline(
            command=request.command,
            timeout=request.timeout
        )
        return result
    except Exception as e:
        logger.error(f"Error executing AWS command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/aws/help")
async def get_aws_help(request: AwsHelpRequest):
    """Get help for AWS CLI commands."""
    try:
        result = await aws_cli_help(
            service=request.service,
            command=request.command
        )
        return result
    except Exception as e:
        logger.error(f"Error getting AWS help: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/aws/profiles", response_model=AwsProfilesResponse)
async def get_profiles():
    """Get available AWS profiles."""
    try:
        profiles = get_aws_profiles()
        env = get_aws_environment()
        current_profile = env.get("aws_profile")

        return {
            "profiles": [
                {
                    "name": profile,
                    "is_current": profile == current_profile
                }
                for profile in profiles
            ]
        }
    except Exception as e:
        logger.error(f"Error getting AWS profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/aws/environment")
async def get_environment():
    """Get AWS environment information."""
    try:
        return get_aws_environment()
    except Exception as e:
        logger.error(f"Error getting AWS environment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/aws/account")
async def get_account():
    """Get AWS account information."""
    try:
        return get_aws_account_info()
    except Exception as e:
        logger.error(f"Error getting AWS account info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/aws/regions/{region_code}", response_model=AwsRegionResponse)
async def get_region(region_code: str):
    """Get detailed information about an AWS region."""
    try:
        return get_region_details(region_code)
    except Exception as e:
        logger.error(f"Error getting region details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests."""
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
