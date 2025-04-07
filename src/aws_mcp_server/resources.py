"""AWS Resource definitions for the AWS MCP Server.

This module provides MCP Resources that expose AWS environment information
including available profiles, regions, and current configuration state.
"""

import configparser
import logging
import os
import re
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


def get_aws_profiles() -> List[str]:
    """Get available AWS profiles from config and credentials files.

    Reads the AWS config and credentials files to extract all available profiles.

    Returns:
        List of profile names
    """
    profiles = ["default"]  # default profile always exists
    config_paths = [
        os.path.expanduser("~/.aws/config"),
        os.path.expanduser("~/.aws/credentials"),
    ]

    try:
        for config_path in config_paths:
            if not os.path.exists(config_path):
                continue

            config = configparser.ConfigParser()
            config.read(config_path)

            for section in config.sections():
                # In config file, profiles are named [profile xyz] except default
                # In credentials file, profiles are named [xyz]
                profile_match = re.match(r"profile\s+(.+)", section)
                if profile_match:
                    # This is from config file
                    profile_name = profile_match.group(1)
                    if profile_name not in profiles:
                        profiles.append(profile_name)
                elif section != "default" and section not in profiles:
                    # This is likely from credentials file
                    profiles.append(section)
    except Exception as e:
        logger.warning(f"Error reading AWS profiles: {e}")

    return profiles


def get_aws_regions() -> List[Dict[str, str]]:
    """Get available AWS regions.

    Uses boto3 to retrieve the list of available AWS regions.
    Prefers using the configured AWS profile.

    Returns:
        List of region dictionaries with name and description
    """
    try:
        # Create a session with the configured profile
        session = boto3.session.Session(
            profile_name=os.environ.get("AWS_PROFILE", "default"), region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        )
        ec2 = session.client("ec2")
        response = ec2.describe_regions()

        # Format the regions
        regions = []
        for region in response["Regions"]:
            region_name = region["RegionName"]
            # Create a friendly name based on the region code
            description = _get_region_description(region_name)
            regions.append({"RegionName": region_name, "RegionDescription": description})

        # Sort regions by name
        regions.sort(key=lambda r: r["RegionName"])
        return regions
    except (BotoCoreError, ClientError) as e:
        logger.warning(f"Error fetching AWS regions: {e}")
        # Fallback to a static list of common regions
        return [
            {"RegionName": "us-east-1", "RegionDescription": "US East (N. Virginia)"},
            {"RegionName": "us-east-2", "RegionDescription": "US East (Ohio)"},
            {"RegionName": "us-west-1", "RegionDescription": "US West (N. California)"},
            {"RegionName": "us-west-2", "RegionDescription": "US West (Oregon)"},
            {"RegionName": "eu-west-1", "RegionDescription": "EU West (Ireland)"},
            {"RegionName": "eu-west-2", "RegionDescription": "EU West (London)"},
            {"RegionName": "eu-central-1", "RegionDescription": "EU Central (Frankfurt)"},
            {"RegionName": "ap-northeast-1", "RegionDescription": "Asia Pacific (Tokyo)"},
            {"RegionName": "ap-northeast-2", "RegionDescription": "Asia Pacific (Seoul)"},
            {"RegionName": "ap-southeast-1", "RegionDescription": "Asia Pacific (Singapore)"},
            {"RegionName": "ap-southeast-2", "RegionDescription": "Asia Pacific (Sydney)"},
            {"RegionName": "sa-east-1", "RegionDescription": "South America (São Paulo)"},
        ]
    except Exception as e:
        logger.warning(f"Unexpected error fetching AWS regions: {e}")
        return []


def _get_region_description(region_code: str) -> str:
    """Convert region code to a human-readable description.

    Args:
        region_code: AWS region code (e.g., us-east-1)

    Returns:
        Human-readable region description
    """
    region_map = {
        "us-east-1": "US East (N. Virginia)",
        "us-east-2": "US East (Ohio)",
        "us-west-1": "US West (N. California)",
        "us-west-2": "US West (Oregon)",
        "af-south-1": "Africa (Cape Town)",
        "ap-east-1": "Asia Pacific (Hong Kong)",
        "ap-south-1": "Asia Pacific (Mumbai)",
        "ap-northeast-1": "Asia Pacific (Tokyo)",
        "ap-northeast-2": "Asia Pacific (Seoul)",
        "ap-northeast-3": "Asia Pacific (Osaka)",
        "ap-southeast-1": "Asia Pacific (Singapore)",
        "ap-southeast-2": "Asia Pacific (Sydney)",
        "ap-southeast-3": "Asia Pacific (Jakarta)",
        "ca-central-1": "Canada (Central)",
        "eu-central-1": "EU Central (Frankfurt)",
        "eu-west-1": "EU West (Ireland)",
        "eu-west-2": "EU West (London)",
        "eu-west-3": "EU West (Paris)",
        "eu-north-1": "EU North (Stockholm)",
        "eu-south-1": "EU South (Milan)",
        "me-south-1": "Middle East (Bahrain)",
        "sa-east-1": "South America (São Paulo)",
    }

    return region_map.get(region_code, f"AWS Region {region_code}")


def get_aws_environment() -> Dict[str, str]:
    """Get information about the current AWS environment.

    Collects information about the active AWS environment,
    including profile, region, and credential status.

    Returns:
        Dictionary with AWS environment information
    """
    env_info = {
        "aws_profile": os.environ.get("AWS_PROFILE", "default"),
        "aws_region": os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")),
        "has_credentials": False,
        "credentials_source": "none",
    }

    try:
        # Try to load credentials from the session (preferred method)
        session = boto3.session.Session()
        credentials = session.get_credentials()
        if credentials:
            env_info["has_credentials"] = True
            source = "profile"

            # Determine credential source if possible
            if credentials.method == "shared-credentials-file":
                source = "profile"
            elif credentials.method == "environment":
                source = "environment"
            elif credentials.method == "iam-role":
                source = "instance-profile"
            elif credentials.method == "assume-role":
                source = "assume-role"
            elif credentials.method == "container-role":
                source = "container-role"

            env_info["credentials_source"] = source
    except Exception as e:
        logger.warning(f"Error checking credentials: {e}")

    return env_info


def _mask_key(key: str) -> str:
    """Mask a sensitive key for security.

    Args:
        key: The key to mask

    Returns:
        Masked key with only the first few characters visible
    """
    if not key:
        return ""

    # Show only first few characters
    visible_len = min(3, len(key))
    return key[:visible_len] + "*" * (len(key) - visible_len)


def get_aws_account_info() -> Dict[str, Optional[str]]:
    """Get information about the current AWS account.

    Uses STS to retrieve account ID and alias information.
    Prefers using the configured AWS profile.

    Returns:
        Dictionary with AWS account information
    """
    account_info = {
        "account_id": None,
        "account_alias": None,
        "organization_id": None,
    }

    try:
        # Create a session with the configured profile
        session = boto3.session.Session(
            profile_name=os.environ.get("AWS_PROFILE", "default"), region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        )

        # Get account ID from STS
        sts = session.client("sts")
        account_id = sts.get_caller_identity().get("Account")
        account_info["account_id"] = account_id

        # Try to get account alias
        if account_id:
            try:
                iam = session.client("iam")
                aliases = iam.list_account_aliases().get("AccountAliases", [])
                if aliases:
                    account_info["account_alias"] = aliases[0]
            except Exception as e:
                logger.debug(f"Error getting account alias: {e}")

            # Try to get organization info
            try:
                org = session.client("organizations")
                account = org.describe_account(AccountId=account_id)
                if "Organization" in account:
                    account_info["organization_id"] = account["Organization"]["Id"]
            except Exception as e:
                # Organizations access is often restricted, so this is expected to fail in many cases
                logger.debug(f"Error getting organization info: {e}")
    except Exception as e:
        logger.warning(f"Error getting AWS account info: {e}")

    return account_info


def register_resources(mcp):
    """Register all resources with the MCP server instance.

    Args:
        mcp: The FastMCP server instance
    """
    logger.info("Registering AWS resources")

    @mcp.resource(uri="aws://config/profiles")
    async def aws_profiles() -> dict:
        """Get available AWS profiles.

        Retrieves a list of available AWS profile names from the
        AWS configuration and credentials files.

        Returns:
            Dictionary with profile information
        """
        profiles = get_aws_profiles()
        current_profile = os.environ.get("AWS_PROFILE", "default")
        return {"profiles": [{"name": profile, "is_current": profile == current_profile} for profile in profiles]}

    @mcp.resource(uri="aws://config/regions")
    async def aws_regions() -> dict:
        """Get available AWS regions.

        Retrieves a list of available AWS regions with
        their descriptive names.

        Returns:
            Dictionary with region information
        """
        regions = get_aws_regions()
        current_region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        return {
            "regions": [
                {
                    "name": region["RegionName"],
                    "description": region["RegionDescription"],
                    "is_current": region["RegionName"] == current_region,
                }
                for region in regions
            ]
        }

    @mcp.resource(uri="aws://config/environment")
    async def aws_environment() -> dict:
        """Get AWS environment information.

        Retrieves information about the current AWS environment,
        including profile, region, and credential status.

        Returns:
            Dictionary with environment information
        """
        return get_aws_environment()

    @mcp.resource(uri="aws://config/account")
    async def aws_account() -> dict:
        """Get AWS account information.

        Retrieves information about the current AWS account,
        including account ID and alias.

        Returns:
            Dictionary with account information
        """
        return get_aws_account_info()

    logger.info("Successfully registered all AWS resources")
