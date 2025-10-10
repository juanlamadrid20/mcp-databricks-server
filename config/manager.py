"""
Environment manager for handling environment switching and state management.

Implements a singleton pattern to maintain a single active environment state
across the MCP server lifetime.
"""

from typing import Dict, Optional
from datetime import datetime

from models.environment import (
    EnvironmentConfig,
    EnvironmentsConfiguration,
    ActiveEnvironment
)
from config.loader import auto_load_configuration
from utils.logger import logger, mask_token


class EnvironmentManager:
    """
    Singleton manager for environment configuration and switching.

    Maintains the active environment state and provides methods for
    loading configurations, switching environments, and retrieving
    credentials for Databricks connections.
    """

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize instance variables
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the environment manager (only once)."""
        if self._initialized:
            return

        self._configuration: Optional[EnvironmentsConfiguration] = None
        self._active_environment: Optional[ActiveEnvironment] = None
        self._initialized = True
        logger.info("EnvironmentManager initialized")

    def load_configuration(
        self,
        yaml_file: str = 'environments.yaml',
        env_file: str = '.env'
    ) -> None:
        """
        Load environment configuration from YAML or .env file.

        Args:
            yaml_file: Path to YAML config file
            env_file: Path to .env file

        Raises:
            FileNotFoundError: If no configuration file found
            ValueError: If configuration is invalid
        """
        try:
            self._configuration = auto_load_configuration(yaml_file, env_file)
            logger.info(
                f"Loaded {len(self._configuration.environments)} environment(s)"
            )
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def set_active_to_default(self) -> None:
        """
        Set the active environment to the configured default.

        Raises:
            RuntimeError: If configuration not loaded
            ValueError: If default environment is invalid
        """
        if not self._configuration:
            raise RuntimeError(
                "Configuration not loaded. Call load_configuration() first."
            )

        default_name = self._configuration.default
        default_config = self._configuration.get_default_environment()

        self._active_environment = ActiveEnvironment(
            name=default_name,
            config=default_config,
            activated_at=datetime.now()
        )

        logger.info(
            f"Active environment set to default: {default_name} "
            f"(host: {default_config.host})"
        )

    def switch_to_environment(self, name: str) -> str:
        """
        Switch to a different environment by name.

        Validates that the environment exists and has complete credentials
        before switching. Logs the switch operation for audit trails.

        Args:
            name: The name of the environment to switch to

        Returns:
            Success message with environment details

        Raises:
            RuntimeError: If configuration not loaded
            ValueError: If environment doesn't exist or has invalid credentials
        """
        if not self._configuration:
            raise RuntimeError(
                "Configuration not loaded. Call load_configuration() first."
            )

        # Check if environment exists
        target_env = self._configuration.get_environment(name)
        if not target_env:
            available = ', '.join(self._configuration.list_environment_names())
            raise ValueError(
                f"Environment '{name}' not found. "
                f"Available environments: {available}"
            )

        # Store old environment for logging
        old_name = self._active_environment.name if self._active_environment else None

        # Switch to new environment
        self._active_environment = ActiveEnvironment(
            name=name,
            config=target_env,
            activated_at=datetime.now()
        )

        # Log the switch
        if old_name and old_name != name:
            logger.info(f"Environment switched: {old_name} → {name}")
        else:
            logger.info(f"Environment set to: {name}")

        # Return success message with details
        return (
            f"✓ Switched to environment: {name}\n"
            f"Host: {target_env.host}\n"
            f"Description: {target_env.description or 'N/A'}\n"
            f"Tags: {', '.join(target_env.tags) if target_env.tags else 'N/A'}"
        )

    def get_active_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get credentials for the currently active environment.

        Returns:
            Dictionary with host, token, and http_path keys, or None if no active environment

        Raises:
            RuntimeError: If no active environment is set
        """
        if not self._active_environment:
            raise RuntimeError(
                "No active environment set. Call set_active_to_default() or "
                "switch_to_environment() first."
            )

        return self._active_environment.get_credentials()

    def get_active_environment_name(self) -> Optional[str]:
        """
        Get the name of the currently active environment.

        Returns:
            Environment name, or None if no active environment
        """
        if not self._active_environment:
            return None
        return self._active_environment.name

    def get_active_environment_info(self) -> str:
        """
        Get detailed information about the currently active environment.

        Returns:
            Formatted string with environment details

        Raises:
            RuntimeError: If no active environment is set
        """
        if not self._active_environment:
            raise RuntimeError("No active environment set.")

        return self._active_environment.to_summary()

    def list_all_environments(self) -> Dict[str, EnvironmentConfig]:
        """
        Get all configured environments.

        Returns:
            Dictionary of environment name to EnvironmentConfig

        Raises:
            RuntimeError: If configuration not loaded
        """
        if not self._configuration:
            raise RuntimeError("Configuration not loaded.")

        return self._configuration.environments

    def reload_configuration(
        self,
        yaml_file: str = 'environments.yaml',
        env_file: str = '.env'
    ) -> None:
        """
        Reload configuration from file (used by file watcher).

        If the current active environment no longer exists after reload,
        resets to default environment.

        Args:
            yaml_file: Path to YAML config file
            env_file: Path to .env file

        Raises:
            ValueError: If new configuration is invalid
        """
        try:
            old_active = self._active_environment.name if self._active_environment else None

            # Load new configuration
            self._configuration = auto_load_configuration(yaml_file, env_file)
            logger.warning(f"Configuration file changed, reloading: {yaml_file}")

            # Check if active environment still exists
            if old_active and old_active not in self._configuration.environments:
                logger.warning(
                    f"Active environment '{old_active}' no longer exists in "
                    f"configuration. Resetting to default: "
                    f"{self._configuration.default}"
                )
                self.set_active_to_default()
            elif old_active:
                # Update active environment with new configuration
                new_config = self._configuration.get_environment(old_active)
                self._active_environment = ActiveEnvironment(
                    name=old_active,
                    config=new_config,
                    activated_at=datetime.now()
                )
                logger.info(f"Active environment '{old_active}' updated with new configuration")

            logger.info("Configuration reload successful")

        except Exception as e:
            logger.error(
                f"Failed to reload configuration: {e}. "
                f"Keeping current configuration."
            )
            # Don't raise - keep current configuration on error
