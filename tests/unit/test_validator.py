"""
Unit tests for the config.validator module.

Tests cover validation of environment credentials and error message generation,
including edge cases for empty, None, and whitespace-only values.
"""

import pytest
from typing import List, Optional
from unittest.mock import Mock

from config.validator import validate_credentials_complete, get_validation_error_message
from models.environment import EnvironmentConfig


class TestValidateCredentialsComplete:
    """Test suite for validate_credentials_complete function."""

    def test_valid_credentials_all_fields_present(self):
        """Test that validation passes when all required fields are present and non-empty."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "dev.cloud.databricks.com"
        env.token = "dapi123456789"
        env.http_path = "/sql/1.0/warehouses/abc123"

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is True
        assert missing_fields is None

    def test_valid_credentials_with_whitespace_surrounding(self):
        """Test that validation passes when fields have surrounding whitespace but contain content."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "  dev.cloud.databricks.com  "
        env.token = "  dapi123456789  "
        env.http_path = "  /sql/1.0/warehouses/abc123  "

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is True
        assert missing_fields is None

    def test_invalid_credentials_host_is_none(self):
        """Test that validation fails when host is None."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = None
        env.token = "dapi123456789"
        env.http_path = "/sql/1.0/warehouses/abc123"

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['host']

    def test_invalid_credentials_host_is_empty_string(self):
        """Test that validation fails when host is an empty string."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = ""
        env.token = "dapi123456789"
        env.http_path = "/sql/1.0/warehouses/abc123"

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['host']

    def test_invalid_credentials_host_is_whitespace_only(self):
        """Test that validation fails when host contains only whitespace."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "   "
        env.token = "dapi123456789"
        env.http_path = "/sql/1.0/warehouses/abc123"

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['host']

    def test_invalid_credentials_token_is_none(self):
        """Test that validation fails when token is None."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "dev.cloud.databricks.com"
        env.token = None
        env.http_path = "/sql/1.0/warehouses/abc123"

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['token']

    def test_invalid_credentials_token_is_empty_string(self):
        """Test that validation fails when token is an empty string."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "dev.cloud.databricks.com"
        env.token = ""
        env.http_path = "/sql/1.0/warehouses/abc123"

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['token']

    def test_invalid_credentials_token_is_whitespace_only(self):
        """Test that validation fails when token contains only whitespace."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "dev.cloud.databricks.com"
        env.token = "\t\n  "
        env.http_path = "/sql/1.0/warehouses/abc123"

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['token']

    def test_invalid_credentials_http_path_is_none(self):
        """Test that validation fails when http_path is None."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "dev.cloud.databricks.com"
        env.token = "dapi123456789"
        env.http_path = None

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['http_path']

    def test_invalid_credentials_http_path_is_empty_string(self):
        """Test that validation fails when http_path is an empty string."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "dev.cloud.databricks.com"
        env.token = "dapi123456789"
        env.http_path = ""

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['http_path']

    def test_invalid_credentials_http_path_is_whitespace_only(self):
        """Test that validation fails when http_path contains only whitespace."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "dev.cloud.databricks.com"
        env.token = "dapi123456789"
        env.http_path = "     "

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['http_path']

    def test_invalid_credentials_multiple_fields_missing(self):
        """Test that validation fails and lists all missing fields when multiple are invalid."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = ""
        env.token = None
        env.http_path = "  "

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['host', 'token', 'http_path']

    def test_invalid_credentials_host_and_token_missing(self):
        """Test that validation fails when host and token are missing."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = None
        env.token = ""
        env.http_path = "/sql/1.0/warehouses/abc123"

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['host', 'token']

    def test_invalid_credentials_host_and_http_path_missing(self):
        """Test that validation fails when host and http_path are missing."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "   "
        env.token = "dapi123456789"
        env.http_path = None

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['host', 'http_path']

    def test_invalid_credentials_token_and_http_path_missing(self):
        """Test that validation fails when token and http_path are missing."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = "dev.cloud.databricks.com"
        env.token = ""
        env.http_path = "  "

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['token', 'http_path']

    def test_invalid_credentials_all_fields_none(self):
        """Test that validation fails when all fields are None."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = None
        env.token = None
        env.http_path = None

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['host', 'token', 'http_path']

    def test_invalid_credentials_all_fields_empty(self):
        """Test that validation fails when all fields are empty strings."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = ""
        env.token = ""
        env.http_path = ""

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert
        assert is_valid is False
        assert missing_fields == ['host', 'token', 'http_path']

    def test_missing_fields_order_is_consistent(self):
        """Test that missing fields are returned in a consistent order."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.host = ""
        env.token = ""
        env.http_path = ""

        # Act
        _, missing_fields = validate_credentials_complete(env)

        # Assert - fields should be in the order: host, token, http_path
        assert missing_fields == ['host', 'token', 'http_path']


class TestGetValidationErrorMessage:
    """Test suite for get_validation_error_message function."""

    def test_error_message_single_missing_field(self):
        """Test error message generation for a single missing field."""
        # Arrange
        env_name = "dev"
        missing_fields = ["host"]

        # Act
        message = get_validation_error_message(env_name, missing_fields)

        # Assert
        assert "Environment 'dev' has incomplete credentials." in message
        assert "Missing required fields: host" in message
        assert "Please update your environments.yaml file" in message
        assert "- host: Your Databricks workspace hostname" in message
        assert "- token: Your Databricks personal access token" in message
        assert "- http_path: SQL warehouse HTTP path" in message

    def test_error_message_multiple_missing_fields(self):
        """Test error message generation for multiple missing fields."""
        # Arrange
        env_name = "production"
        missing_fields = ["host", "token"]

        # Act
        message = get_validation_error_message(env_name, missing_fields)

        # Assert
        assert "Environment 'production' has incomplete credentials." in message
        assert "Missing required fields: host, token" in message
        assert "Please update your environments.yaml file" in message

    def test_error_message_all_fields_missing(self):
        """Test error message generation when all fields are missing."""
        # Arrange
        env_name = "staging"
        missing_fields = ["host", "token", "http_path"]

        # Act
        message = get_validation_error_message(env_name, missing_fields)

        # Assert
        assert "Environment 'staging' has incomplete credentials." in message
        assert "Missing required fields: host, token, http_path" in message

    def test_error_message_environment_name_preserved(self):
        """Test that the environment name is properly preserved in the message."""
        # Arrange
        env_name = "my-special-env-123"
        missing_fields = ["token"]

        # Act
        message = get_validation_error_message(env_name, missing_fields)

        # Assert
        assert f"Environment '{env_name}' has incomplete credentials." in message

    def test_error_message_with_special_characters_in_env_name(self):
        """Test error message with special characters in environment name."""
        # Arrange
        env_name = "test-env_2024"
        missing_fields = ["http_path"]

        # Act
        message = get_validation_error_message(env_name, missing_fields)

        # Assert
        assert f"Environment '{env_name}' has incomplete credentials." in message
        assert "Missing required fields: http_path" in message

    def test_error_message_structure_contains_all_sections(self):
        """Test that the error message contains all expected sections."""
        # Arrange
        env_name = "dev"
        missing_fields = ["host"]

        # Act
        message = get_validation_error_message(env_name, missing_fields)

        # Assert
        # Check for main sections
        assert "has incomplete credentials" in message
        assert "Missing required fields:" in message
        assert "Please update your environments.yaml file" in message

        # Check for all field descriptions
        assert "host: Your Databricks workspace hostname" in message
        assert "token: Your Databricks personal access token" in message
        assert "http_path: SQL warehouse HTTP path" in message

    def test_error_message_fields_comma_separated(self):
        """Test that multiple missing fields are properly comma-separated."""
        # Arrange
        env_name = "test"
        missing_fields = ["host", "token", "http_path"]

        # Act
        message = get_validation_error_message(env_name, missing_fields)

        # Assert
        assert "host, token, http_path" in message

    def test_error_message_with_empty_env_name(self):
        """Test error message generation with an empty environment name."""
        # Arrange
        env_name = ""
        missing_fields = ["host"]

        # Act
        message = get_validation_error_message(env_name, missing_fields)

        # Assert
        # Should still generate a valid message, even with empty env name
        assert "Environment ''" in message
        assert "Missing required fields: host" in message

    def test_error_message_consistent_formatting(self):
        """Test that the message formatting is consistent across different inputs."""
        # Arrange
        test_cases = [
            ("dev", ["host"]),
            ("prod", ["token"]),
            ("staging", ["http_path"]),
            ("test", ["host", "token"]),
        ]

        # Act & Assert
        for env_name, missing_fields in test_cases:
            message = get_validation_error_message(env_name, missing_fields)

            # All messages should have these structural elements
            lines = message.split('\n')
            assert len(lines) >= 7  # Should have multiple lines
            assert lines[0].startswith("Environment")
            assert "Missing required fields:" in message
            assert "Please update your environments.yaml file" in message


class TestValidatorIntegration:
    """Integration tests combining both validation functions."""

    def test_validation_flow_invalid_to_error_message(self):
        """Test the typical flow from validation to error message generation."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.name = "dev"
        env.host = ""
        env.token = None
        env.http_path = "  "

        # Act - Validate
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert - Validation failed
        assert is_valid is False
        assert len(missing_fields) == 3

        # Act - Generate error message
        error_message = get_validation_error_message(env.name, missing_fields)

        # Assert - Error message is complete
        assert "Environment 'dev'" in error_message
        assert all(field in error_message for field in ['host', 'token', 'http_path'])

    def test_validation_flow_partial_credentials(self):
        """Test validation flow with partially complete credentials."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.name = "production"
        env.host = "prod.cloud.databricks.com"
        env.token = ""  # Missing token
        env.http_path = "/sql/1.0/warehouses/prod123"

        # Act - Validate
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert - Only token is missing
        assert is_valid is False
        assert missing_fields == ['token']

        # Act - Generate error message
        error_message = get_validation_error_message(env.name, missing_fields)

        # Assert - Message mentions only the missing field
        assert "Environment 'production'" in error_message
        assert "Missing required fields: token" in error_message

    def test_validation_flow_valid_credentials_no_error_message_needed(self):
        """Test that valid credentials don't require error message generation."""
        # Arrange
        env = Mock(spec=EnvironmentConfig)
        env.name = "staging"
        env.host = "staging.cloud.databricks.com"
        env.token = "dapi_valid_token"
        env.http_path = "/sql/1.0/warehouses/staging456"

        # Act
        is_valid, missing_fields = validate_credentials_complete(env)

        # Assert - No error message needed
        assert is_valid is True
        assert missing_fields is None

    @pytest.mark.parametrize("env_name,missing_fields", [
        ("dev", ["host"]),
        ("prod", ["token"]),
        ("staging", ["http_path"]),
        ("test", ["host", "token"]),
        ("qa", ["host", "http_path"]),
        ("uat", ["token", "http_path"]),
        ("local", ["host", "token", "http_path"]),
    ])
    def test_error_message_generation_parametrized(self, env_name: str, missing_fields: List[str]):
        """Parametrized test for error message generation with various combinations."""
        # Act
        message = get_validation_error_message(env_name, missing_fields)

        # Assert
        assert f"Environment '{env_name}'" in message
        for field in missing_fields:
            assert field in message
