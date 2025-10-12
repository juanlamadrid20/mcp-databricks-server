# Data Model: Multi-Environment Configuration Support

**Feature**: 001-update-mcp-project
**Date**: 2025-10-09

## Overview

This document defines the data structures and relationships for managing multiple Databricks environment configurations.

## Entity Definitions

### EnvironmentConfig

Represents a single Databricks environment's connection credentials and metadata.

**Fields**:

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `name` | `str` | Yes | Unique identifier for the environment | Alphanumeric, hyphens, underscores only. Max 50 chars |
| `host` | `str` | Yes | Databricks workspace hostname | Valid hostname format (no https:// prefix) |
| `token` | `str` | Yes | Databricks personal access token | Non-empty string, starts with 'dapi' |
| `http_path` | `str` | Yes | SQL warehouse HTTP path | Format: `/sql/1.0/warehouses/{id}` |
| `description` | `str` | No | Human-readable description | Max 200 chars |
| `tags` | `List[str]` | No | Category tags for organization | Each tag max 30 chars, alphanumeric |

**Python Model** (using Pydantic):

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re

class EnvironmentConfig(BaseModel):
    """Configuration for a single Databricks environment."""

    name: str = Field(..., min_length=1, max_length=50)
    host: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    http_path: str = Field(..., pattern=r"^/sql/1\.0/warehouses/.+$")
    description: Optional[str] = Field(None, max_length=200)
    tags: Optional[List[str]] = Field(default_factory=list)

    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Name must contain only alphanumeric characters, hyphens, and underscores')
        return v

    @validator('host')
    def validate_host(cls, v):
        if v.startswith('http://') or v.startswith('https://'):
            raise ValueError('Host should not include protocol (http:// or https://)')
        return v

    @validator('token')
    def validate_token(cls, v):
        if not v.startswith('dapi'):
            raise ValueError('Token should start with "dapi"')
        return v

    @validator('tags')
    def validate_tags(cls, v):
        for tag in v:
            if len(tag) > 30:
                raise ValueError(f'Tag "{tag}" exceeds 30 character limit')
            if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                raise ValueError(f'Tag "{tag}" contains invalid characters')
        return v

    class Config:
        # Don't expose token in string representation
        fields = {'token': {'repr': False}}
```

**Example**:

```python
env = EnvironmentConfig(
    name="field-eng-west",
    host="e2-demo-field-eng.cloud.databricks.com",
    token="dapi_your_token_here",
    http_path="/sql/1.0/warehouses/4b9b953939869799",
    description="Field Engineering West demo environment",
    tags=["demo", "west"]
)
```

---

### EnvironmentsConfiguration

Container for all environment configurations with default selection.

**Fields**:

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `default` | `str` | Yes (multi-env only) | Name of the default environment | Must match an existing environment name |
| `environments` | `Dict[str, EnvironmentConfig]` | Yes | Map of environment name to configuration | At least 1 environment required |

**Python Model**:

```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Dict

class EnvironmentsConfiguration(BaseModel):
    """Container for all environment configurations."""

    default: str = Field(..., description="Default environment name")
    environments: Dict[str, EnvironmentConfig] = Field(..., min_items=1)

    @root_validator
    def validate_default_exists(cls, values):
        default = values.get('default')
        environments = values.get('environments', {})

        if default not in environments:
            available = ', '.join(environments.keys())
            raise ValueError(
                f'Default environment "{default}" not found. '
                f'Available environments: {available}'
            )

        return values

    @validator('environments')
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
```

**YAML Representation**:

```yaml
default: field-eng-west

environments:
  field-eng-west:
    name: field-eng-west
    host: e2-demo-field-eng.cloud.databricks.com
    token: dapi_your_token_here_1
    http_path: /sql/1.0/warehouses/4b9b953939869799
    description: "Field Engineering West demo environment"
    tags:
      - demo
      - west

  aithon:
    name: aithon
    host: dbc-876e9c34-9f7d.cloud.databricks.com
    token: dapi_your_token_here_2
    http_path: /sql/1.0/warehouses/ea5487ea1c4a4495
    description: "Aithon production environment"
    tags:
      - production
```

**Loading from YAML**:

```python
import yaml

def load_environments_config(file_path: str) -> EnvironmentsConfiguration:
    """Load and validate environments configuration from YAML file."""
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    # Parse environment configs
    env_configs = {}
    for name, env_data in data.get('environments', {}).items():
        env_data['name'] = name  # Ensure name is set
        env_configs[name] = EnvironmentConfig(**env_data)

    # Create configuration object
    return EnvironmentsConfiguration(
        default=data.get('default'),
        environments=env_configs
    )
```

---

### ActiveEnvironment

Runtime state tracking the currently active environment.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Name of the active environment |
| `config` | `EnvironmentConfig` | Yes | The active environment's configuration |
| `activated_at` | `datetime` | Yes | Timestamp when this environment was activated |

**Python Model**:

```python
from datetime import datetime
from pydantic import BaseModel, Field

class ActiveEnvironment(BaseModel):
    """Represents the currently active environment."""

    name: str
    config: EnvironmentConfig
    activated_at: datetime = Field(default_factory=datetime.now)

    def get_credentials(self) -> Dict[str, str]:
        """Get credentials for Databricks connection."""
        return {
            'host': self.config.host,
            'token': self.config.token,
            'http_path': self.config.http_path
        }

    def to_summary(self) -> str:
        """Get a summary string for logging."""
        return (
            f"Environment: {self.name}\n"
            f"Host: {self.config.host}\n"
            f"Description: {self.config.description or 'N/A'}\n"
            f"Activated: {self.activated_at.isoformat()}"
        )
```

---

## State Transitions

### Environment Lifecycle

```
┌─────────────────┐
│  Server Start   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load Config     │ ← File watcher detects change
│ (YAML or .env)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Validate Config │
│ - Default exists│
│ - All required  │
│   fields present│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Set Active to   │
│ Default Env     │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ ACTIVE │ ←──────────────┐
    └───┬────┘                │
        │                     │
        │ switch_environment() │
        │                     │
        ▼                     │
┌─────────────────┐          │
│ Validate Switch │          │
│ - Env exists?   │          │
│ - Complete      │          │
│   credentials?  │          │
└────────┬────────┘          │
         │                   │
      [Valid]               │
         │                   │
         ▼                   │
┌─────────────────┐          │
│ Update Active   │          │
│ Log Switch      │──────────┘
└─────────────────┘
```

### Configuration Reload Flow

```
┌─────────────────┐
│ File Modified   │
│ Event Detected  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Parse New       │
│ Configuration   │
└────────┬────────┘
         │
      [Valid?]
         │
    ┌────┴────┐
    │         │
  [Yes]     [No]
    │         │
    │         ▼
    │    ┌─────────────────┐
    │    │ Log Error       │
    │    │ Keep Current    │
    │    │ Configuration   │
    │    └─────────────────┘
    │
    ▼
┌─────────────────┐
│ Update Config   │
│ in Memory       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check if Active │
│ Env Still Exists│
└────────┬────────┘
         │
    [Exists?]
         │
    ┌────┴────┐
    │         │
  [Yes]     [No]
    │         │
    │         ▼
    │    ┌─────────────────┐
    │    │ Reset to Default│
    │    │ Log Warning     │
    │    └─────────────────┘
    │
    ▼
┌─────────────────┐
│ Log Reload      │
│ Success         │
└─────────────────┘
```

---

## Relationships

```
EnvironmentsConfiguration
    │
    ├── default: str ───────────┐
    │                           │
    └── environments: Dict      │
            │                   │
            ├── "env1": EnvironmentConfig
            ├── "env2": EnvironmentConfig
            └── "env3": EnvironmentConfig
                        │
                        │ (referenced by)
                        │
                        ▼
                ActiveEnvironment
                    ├── name: str
                    ├── config: EnvironmentConfig
                    └── activated_at: datetime
```

**Invariants**:
1. `ActiveEnvironment.name` must always exist in `EnvironmentsConfiguration.environments`
2. `EnvironmentsConfiguration.default` must always exist in `EnvironmentsConfiguration.environments`
3. Environment names in the dictionary keys must match the `EnvironmentConfig.name` field
4. At least one environment must be configured

---

## Data Persistence

### File Format (YAML)

**Location**: `/path/to/project/environments.yaml`

**Structure**:
```yaml
default: <environment-name>

environments:
  <env-name-1>:
    name: <env-name-1>
    host: <databricks-host>
    token: <access-token>
    http_path: <warehouse-path>
    description: <optional-description>
    tags:
      - <tag1>
      - <tag2>

  <env-name-2>:
    # ... same structure
```

**Security**:
- File must be in `.gitignore`
- File permissions should be readable only by owner (chmod 600)
- Never log token values

### Legacy Format (.env)

**Location**: `/path/to/project/.env`

**Structure**:
```
DATABRICKS_HOST=<databricks-host>
DATABRICKS_TOKEN=<access-token>
DATABRICKS_HTTP_PATH=<warehouse-path>
```

**Backward Compatibility**:
- If `environments.yaml` doesn't exist, fall back to `.env`
- Create implicit `EnvironmentConfig` with name "default"
- No description or tags for legacy configs

---

## Validation Rules Summary

### EnvironmentConfig Validation
- ✅ Name: alphanumeric, hyphens, underscores only (1-50 chars)
- ✅ Host: valid hostname, no protocol prefix
- ✅ Token: non-empty, starts with "dapi"
- ✅ HTTP Path: matches pattern `/sql/1.0/warehouses/{id}`
- ✅ Description: optional, max 200 chars
- ✅ Tags: optional, each tag 1-30 chars, alphanumeric

### EnvironmentsConfiguration Validation
- ✅ Default environment must exist in environments dict
- ✅ At least one environment must be configured
- ✅ Environment names must match dictionary keys
- ✅ No duplicate environment names

### Runtime Validation (on switch)
- ✅ Target environment exists
- ✅ Target environment has all required fields
- ✅ Log switch operation

---

## Examples

### Example 1: Multi-Environment Configuration

```yaml
default: dev

environments:
  dev:
    name: dev
    host: dev-workspace.cloud.databricks.com
    token: dapi_dev_token_123
    http_path: /sql/1.0/warehouses/dev_warehouse
    description: "Development environment"
    tags:
      - development
      - testing

  staging:
    name: staging
    host: staging-workspace.cloud.databricks.com
    token: dapi_staging_token_456
    http_path: /sql/1.0/warehouses/staging_warehouse
    description: "Staging environment"
    tags:
      - staging
      - pre-production

  prod:
    name: prod
    host: prod-workspace.cloud.databricks.com
    token: dapi_prod_token_789
    http_path: /sql/1.0/warehouses/prod_warehouse
    description: "Production environment"
    tags:
      - production
      - critical
```

### Example 2: Minimal Configuration

```yaml
default: main

environments:
  main:
    name: main
    host: my-workspace.cloud.databricks.com
    token: dapi_token_abc123
    http_path: /sql/1.0/warehouses/main_warehouse
```

### Example 3: Migration from .env

**Before** (`.env`):
```
DATABRICKS_HOST=my-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi_token_abc123
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/main_warehouse
```

**After** (`environments.yaml`):
```yaml
default: production

environments:
  production:
    name: production
    host: my-workspace.cloud.databricks.com
    token: dapi_token_abc123
    http_path: /sql/1.0/warehouses/main_warehouse
    description: "Migrated from legacy .env configuration"
```

---

## Next Steps

See [contracts/](./contracts/) for MCP tool API definitions and [quickstart.md](./quickstart.md) for usage examples.
