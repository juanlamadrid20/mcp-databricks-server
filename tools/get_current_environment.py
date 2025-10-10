"""
MCP tool for getting the currently active Databricks environment.
"""

from config.manager import EnvironmentManager
from utils.logger import logger


def get_current_environment() -> str:
    """
    Get the currently active Databricks environment.

    Returns detailed information about the active environment including
    when it was activated.

    Returns:
        Formatted string with current environment details

    Example:
        >>> get_current_environment()
        Current environment: dev
        Host: dev.cloud.databricks.com
        Description: Development environment
        Tags: development, testing
        Activated at: 2025-10-09T10:30:00Z

    Raises:
        RuntimeError: If no environment is active (should not happen in normal operation)
    """
    try:
        env_manager = EnvironmentManager()
        return env_manager.get_active_environment_info()
    except Exception as e:
        logger.error(f"Failed to get current environment: {e}")
        error_msg = (
            "No active environment set. This should not happen. "
            "Please restart the server."
        )
        raise RuntimeError(error_msg)
