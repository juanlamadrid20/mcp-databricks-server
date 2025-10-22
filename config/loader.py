"""
Configuration loader for multi-environment and legacy .env support.

Handles loading environment configurations from YAML files or falling back
to legacy .env files for backward compatibility.
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from models.environment import EnvironmentConfig, EnvironmentsConfiguration
from utils.logger import logger


def load_from_yaml(file_path: str) -> EnvironmentsConfiguration:
    """
    Load and validate environments configuration from YAML file.

    Args:
        file_path: Path to environments.yaml file

    Returns:
        Validated EnvironmentsConfiguration object

    Raises:
        FileNotFoundError: If YAML file doesn't exist
        ValueError: If YAML is invalid or validation fails
        yaml.YAMLError: If YAML parsing fails
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    logger.info(f"Loading configuration from {file_path}")

    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Configuration file is empty: {file_path}")

        # Parse environment configs
        env_configs = {}
        for name, env_data in data.get('environments', {}).items():
            # Ensure name is set in the environment data
            env_data['name'] = name
            env_configs[name] = EnvironmentConfig(**env_data)

        # Create configuration object with validation
        config = EnvironmentsConfiguration(
            default=data.get('default'),
            environments=env_configs
        )

        logger.info(
            f"Configuration loaded: {file_path} "
            f"({len(config.environments)} environments)"
        )
        return config

    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {file_path}: {e}")
        raise ValueError(f"Invalid YAML format in {file_path}: {e}")
    except Exception as e:
        logger.error(f"Failed to load configuration from {file_path}: {e}")
        raise


def load_from_env(env_file: str = '.env') -> EnvironmentsConfiguration:
    """
    Load configuration from legacy .env file.

    Creates an implicit single-environment configuration with name "default"
    for backward compatibility with existing .env setups.

    Args:
        env_file: Path to .env file (default: .env)

    Returns:
        EnvironmentsConfiguration with single "default" environment

    Raises:
        FileNotFoundError: If .env file doesn't exist
        ValueError: If required environment variables are missing
    """
    if not os.path.exists(env_file):
        raise FileNotFoundError(f"Environment file not found: {env_file}")

    logger.warning(
        f"environments.yaml not found, using legacy .env configuration from {env_file}"
    )

    # Load environment variables from .env file
    load_dotenv(env_file)

    # Get required variables
    host = os.getenv('DATABRICKS_HOST')
    token = os.getenv('DATABRICKS_TOKEN')
    http_path = os.getenv('DATABRICKS_HTTP_PATH')

    if not all([host, token, http_path]):
        missing = []
        if not host:
            missing.append('DATABRICKS_HOST')
        if not token:
            missing.append('DATABRICKS_TOKEN')
        if not http_path:
            missing.append('DATABRICKS_HTTP_PATH')

        raise ValueError(
            f"Missing required environment variables in {env_file}: "
            f"{', '.join(missing)}"
        )

    # Create implicit environment config
    default_env = EnvironmentConfig(
        name='default',
        host=host,
        token=token,
        http_path=http_path,
        description=f"Migrated from {env_file}"
    )

    # Create configuration with single environment
    config = EnvironmentsConfiguration(
        default='default',
        environments={'default': default_env}
    )

    logger.info(f"Configuration loaded: {env_file} (1 environment, backward compatibility mode)")
    return config


def auto_load_configuration(
    yaml_file: str = 'environments.yaml',
    env_file: str = '.env'
) -> EnvironmentsConfiguration:
    """
    Automatically load configuration from YAML or fall back to .env.

    Detection logic:
    1. Check if environments.yaml exists
    2. If yes → Load multi-environment configuration
    3. If no → Check for .env file
    4. If .env exists → Create implicit single-environment config
    5. If neither → Error: No configuration found

    Args:
        yaml_file: Path to YAML config file (default: environments.yaml)
        env_file: Path to .env file (default: .env)

    Returns:
        EnvironmentsConfiguration object

    Raises:
        FileNotFoundError: If neither configuration file exists
        ValueError: If configuration is invalid
    """
    # DEBUG: Log current working directory
    current_dir = os.getcwd()
    logger.info(f"DEBUG: Current working directory: {current_dir}")
    logger.info(f"DEBUG: Looking for yaml_file: {yaml_file}")
    logger.info(f"DEBUG: yaml_file exists: {os.path.exists(yaml_file)}")
    logger.info(f"DEBUG: Absolute path to yaml_file: {os.path.abspath(yaml_file)}")
    
    # First, try to load from YAML
    if os.path.exists(yaml_file):
        # Warn if both files exist
        if os.path.exists(env_file):
            logger.warning(
                f"Both {yaml_file} and {env_file} exist. "
                f"Using {yaml_file} (preferred). "
                f"Consider removing {env_file} if no longer needed."
            )
        return load_from_yaml(yaml_file)

    # Fall back to .env
    if os.path.exists(env_file):
        return load_from_env(env_file)

    # No configuration found
    raise FileNotFoundError(
        f"No configuration file found. Please create either:\n"
        f"  - {yaml_file} (recommended for multiple environments)\n"
        f"  - {env_file} (legacy single environment)\n"
        f"See environments.yaml.template for an example.\n"
        f"DEBUG: Current working directory was: {current_dir}"
    )
