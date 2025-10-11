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
        
        # Initialize if not already done
        if env_manager._configuration is None:
            logger.info("Environment manager not initialized, initializing now...")
            env_manager.load_configuration()
            env_manager.set_active_to_default()
        
        return env_manager.get_active_environment_info()
    except Exception as e:
        logger.error(f"Failed to get current environment: {e}")
        error_msg = (
            f"Error getting current environment: {str(e)}\n"
            "Please ensure your environments.yaml or .env file is properly configured."
        )
        raise RuntimeError(error_msg)