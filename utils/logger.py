"""
Logging configuration for environment management operations.

Provides structured logging with appropriate levels for environment operations,
configuration changes, and error handling.
"""

import logging
import sys


def setup_logger(name: str = 'databricks_mcp.environment') -> logging.Logger:
    """
    Set up a logger with structured formatting for environment operations.

    Args:
        name: Logger name (default: databricks_mcp.environment)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding handlers if they already exist
    if not logger.handlers:
        # Create console handler with formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # Create formatter with timestamp and context
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


def mask_token(token: str) -> str:
    """
    Mask a credential token for safe logging.

    Only shows the first 8 characters to help identify which token
    is being used without exposing the full credential.

    Args:
        token: The token to mask

    Returns:
        Masked token string (first 8 chars + "...")
    """
    if not token or len(token) <= 8:
        return "***"
    return f"{token[:8]}..."


# Create default logger instance
logger = setup_logger()
