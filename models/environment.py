"""
Data models for multi-environment configuration.

This module defines Pydantic models for managing multiple Databricks environment
configurations, including validation rules and helper methods.
"""

from datetime import datetime
from typing import Dict, List, Optional
import re

from pydantic import BaseModel, Field, field_validator, model_validator


class EnvironmentConfig(BaseModel):
    """Configuration for a single Databricks environment.
    
    Supports two authentication methods:
    1. Token-based: Provide 'token' parameter
    2. Profile-based: Provide 'profile' parameter (references ~/.databrickscfg)
    
    Exactly one authentication method must be specified.
    """

    name: str = Field(..., min_length=1, max_length=50)
    host: str = Field(..., min_length=1)
    
    # Authentication: either token OR profile (mutually exclusive)
    token: Optional[str] = Field(None, min_length=1)
    profile: Optional[str] = Field(None, min_length=1, max_length=100)
    
    http_path: str = Field(..., pattern=r"^/sql/1\.0/warehouses/.+$")
    description: Optional[str] = Field(None, max_length=200)
    tags: Optional[List[str]] = Field(default_factory=list)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate environment name contains only allowed characters."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                'Name must contain only alphanumeric characters, hyphens, and underscores'
            )
        return v

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        """Validate host doesn't include protocol prefix."""
        if v.startswith('http://') or v.startswith('https://'):
            raise ValueError('Host should not include protocol (http:// or https://)')
        return v

    @field_validator('token')
    @classmethod
    def validate_token(cls, v):
        """Validate token format if provided."""
        if v is not None and not v.startswith('dapi'):
            raise ValueError('Token should start with "dapi"')
        return v
    
    @field_validator('profile')
    @classmethod
    def validate_profile(cls, v):
        """Validate profile name contains only allowed characters."""
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                'Profile name must contain only alphanumeric characters, hyphens, and underscores'
            )
        return v
    
    @model_validator(mode='after')
    def validate_auth_method(self):
        """Ensure exactly one authentication method is specified."""
        has_token = self.token is not None
        has_profile = self.profile is not None
        
        if not has_token and not has_profile:
            raise ValueError(
                f"Environment '{self.name}': Either 'token' or 'profile' must be specified"
            )
        if has_token and has_profile:
            raise ValueError(
                f"Environment '{self.name}': Cannot specify both 'token' and 'profile'. "
                "Choose one authentication method."
            )
        return self

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate each tag meets requirements."""
        if v is None:
            return []
        for tag in v:
            if len(tag) > 30:
                raise ValueError(f'Tag "{tag}" exceeds 30 character limit')
            if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                raise ValueError(f'Tag "{tag}" contains invalid characters')
        return v

    model_config = {
        # Don't expose token in string representation
        'json_schema_extra': {
            'examples': [{
                'name': 'dev',
                'host': 'dev.cloud.databricks.com',
                'token': 'dapi_***',
                'http_path': '/sql/1.0/warehouses/abc123'
            }]
        }
    }


class EnvironmentsConfiguration(BaseModel):
    """Container for all environment configurations."""

    default: str = Field(..., description="Default environment name")
    environments: Dict[str, EnvironmentConfig] = Field(..., min_items=1)

    @model_validator(mode='after')
    def validate_default_exists(self):
        """Ensure default environment exists in environments dict."""
        if self.default not in self.environments:
            available = ', '.join(self.environments.keys())
            raise ValueError(
                f'Default environment "{self.default}" not found. '
                f'Available environments: {available}'
            )
        return self

    @field_validator('environments')
    @classmethod
    def validate_environment_names_match_keys(cls, v):
        """Ensure environment names match their dictionary keys."""
        for key, env in v.items():
            if env.name != key:
                raise ValueError(
                    f'Environment key "{key}" does not match environment name "{env.name}"'
                )
        return v

    def get_default_environment(self) -> EnvironmentConfig:
        """Get the default environment configuration."""
        return self.environments[self.default]

    def get_environment(self, name: str) -> Optional[EnvironmentConfig]:
        """Get an environment by name."""
        return self.environments.get(name)

    def list_environment_names(self) -> List[str]:
        """Get a list of all environment names."""
        return list(self.environments.keys())


class ActiveEnvironment(BaseModel):
    """Represents the currently active environment."""

    name: str
    config: EnvironmentConfig
    activated_at: datetime = Field(default_factory=datetime.now)

    def get_credentials(self) -> Dict[str, str]:
        """Get credentials for Databricks connection.
        
        Returns a dictionary containing connection details with either:
        - token-based auth: host, token, http_path
        - profile-based auth: host, profile, http_path
        """
        credentials = {
            'host': self.config.host,
            'http_path': self.config.http_path
        }
        
        if self.config.token:
            credentials['token'] = self.config.token
        elif self.config.profile:
            credentials['profile'] = self.config.profile
            
        return credentials

    def to_summary(self) -> str:
        """Get a summary string for logging."""
        return (
            f"Environment: {self.name}\n"
            f"Host: {self.config.host}\n"
            f"Description: {self.config.description or 'N/A'}\n"
            f"Activated: {self.activated_at.isoformat()}"
        )
