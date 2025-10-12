"""
MCP tool for switching the active Databricks environment.
"""

from config.manager import EnvironmentManager
from utils.logger import logger


def switch_environment(name: str) -> str:
    """
    Switch the active Databricks environment.

    Validates that the target environment exists and has complete credentials
    before switching. Logs the switch operation for audit trails.

    Args:
        name: The name of the environment to switch to

    Returns:
        Success message with environment details

    Example:
        >>> switch_environment("production")
        ✓ Switched to environment: production
        Host: prod.cloud.databricks.com
        Description: Production environment
        Tags: production, critical

    Raises:
        ValueError: If environment doesn't exist or has invalid credentials
    """
    try:
        env_manager = EnvironmentManager()
        
        # Initialize if not already done
        if env_manager._configuration is None:
            logger.info("Environment manager not initialized, initializing now...")
            env_manager.load_configuration()
            env_manager.set_active_to_default()
        
        result = env_manager.switch_to_environment(name)
        return result
    except Exception as e:
        logger.error(f"Failed to switch environment: {e}")
        raise ValueError(str(e))