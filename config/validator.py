"""
Validation utilities for environment configurations.

Provides functions to validate credential completeness and format.
"""

from typing import List, Optional
from models.environment import EnvironmentConfig


def validate_credentials_complete(env: EnvironmentConfig) -> tuple[bool, Optional[List[str]]]:
    """
    Validate that an environment has all required credentials.

    Args:
        env: EnvironmentConfig to validate

    Returns:
        Tuple of (is_valid, missing_fields)
        - is_valid: True if all required fields are present and non-empty
        - missing_fields: List of missing field names, or None if all present
    """
    missing = []

    if not env.host or env.host.strip() == '':
        missing.append('host')

    if not env.token or env.token.strip() == '':
        missing.append('token')

    if not env.http_path or env.http_path.strip() == '':
        missing.append('http_path')

    if missing:
        return False, missing

    return True, None


def get_validation_error_message(env_name: str, missing_fields: List[str]) -> str:
    """
    Generate a user-friendly error message for missing credentials.

    Args:
        env_name: Name of the environment with missing fields
        missing_fields: List of missing field names

    Returns:
        Formatted error message with actionable guidance
    """
    fields_str = ', '.join(missing_fields)
    return (
        f"Environment '{env_name}' has incomplete credentials.\n"
        f"Missing required fields: {fields_str}\n\n"
        f"Please update your environments.yaml file to include all required fields:\n"
        f"  - host: Your Databricks workspace hostname\n"
        f"  - token: Your Databricks personal access token\n"
        f"  - http_path: SQL warehouse HTTP path"
    )
