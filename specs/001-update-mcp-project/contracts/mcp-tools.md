# MCP Tool Contracts: Environment Management

**Feature**: 001-update-mcp-project
**Date**: 2025-10-09

## Overview

This document defines the MCP tool contracts for environment management functionality.

---

## New MCP Tools

### 1. list_environments

**Description**: List all configured Databricks environments with their metadata.

**Parameters**: None

**Returns**: Markdown-formatted table with environment details

**Return Type**: `str`

**Example Output**:

```markdown
| Environment | Host | Description | Tags | Status |
|-------------|------|-------------|------|--------|
| field-eng-west | e2-demo-field-eng.cloud.databricks.com | Field Engineering West demo environment | demo, west | ACTIVE |
| aithon | dbc-876e9c34-9f7d.cloud.databricks.com | Aithon production environment | production | - |
```

**Python Signature**:

```python
@mcp.tool()
def list_environments() -> str:
    """
    List all configured Databricks environments.

    Returns a markdown table showing:
    - Environment name
    - Databricks host
    - Description (if available)
    - Tags (if available)
    - Status (ACTIVE for current environment)

    Example:
        >>> list_environments()
        | Environment | Host | Description | Tags | Status |
        |-------------|------|-------------|------|--------|
        | dev | dev.cloud.databricks.com | Dev environment | development | ACTIVE |
        | prod | prod.cloud.databricks.com | Production | production | - |

    Returns:
        Formatted markdown table as string
    """
```

**Error Scenarios**:

| Error Condition | Error Message | HTTP Status (if applicable) |
|----------------|---------------|----------------------------|
| No environments configured | "No environments configured. Please create an environments.yaml file." | N/A |
| Configuration file corrupted | "Error loading configuration: {error_details}" | N/A |

---

### 2. switch_environment

**Description**: Switch the active Databricks environment.

**Parameters**:

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `name` | `str` | Yes | Name of the environment to switch to | Must exist in configuration |

**Returns**: Success message with environment details

**Return Type**: `str`

**Example Output**:

```
✓ Switched to environment: aithon
Host: dbc-876e9c34-9f7d.cloud.databricks.com
Description: Aithon production environment
Tags: production
```

**Python Signature**:

```python
@mcp.tool()
def switch_environment(name: str) -> str:
    """
    Switch the active Databricks environment.

    Validates that the target environment exists and has complete credentials
    before switching. Logs the switch operation for audit trails.

    Args:
        name: The name of the environment to switch to

    Example:
        >>> switch_environment("production")
        ✓ Switched to environment: production
        Host: prod.cloud.databricks.com
        Description: Production environment
        Tags: production, critical

    Returns:
        Success message with environment details

    Raises:
        ValueError: If environment doesn't exist or has invalid credentials
    """
```

**Error Scenarios**:

| Error Condition | Error Message | Example |
|----------------|---------------|---------|
| Environment doesn't exist | "Environment '{name}' not found. Available environments: {list}" | "Environment 'staging' not found. Available environments: dev, prod" |
| Missing credentials | "Environment '{name}' has incomplete credentials. Missing: {fields}" | "Environment 'dev' has incomplete credentials. Missing: http_path" |
| Invalid credentials format | "Environment '{name}' has invalid credentials: {validation_error}" | "Environment 'prod' has invalid credentials: token must start with 'dapi'" |
| Configuration not loaded | "No configuration loaded. Please check environments.yaml or .env file." | N/A |

---

### 3. get_current_environment

**Description**: Get the currently active Databricks environment.

**Parameters**: None

**Returns**: Environment name and details

**Return Type**: `str`

**Example Output**:

```
Current environment: field-eng-west
Host: e2-demo-field-eng.cloud.databricks.com
Description: Field Engineering West demo environment
Tags: demo, west
Activated at: 2025-10-09T14:23:45Z
```

**Python Signature**:

```python
@mcp.tool()
def get_current_environment() -> str:
    """
    Get the currently active Databricks environment.

    Returns detailed information about the active environment including
    when it was activated.

    Example:
        >>> get_current_environment()
        Current environment: dev
        Host: dev.cloud.databricks.com
        Description: Development environment
        Tags: development, testing
        Activated at: 2025-10-09T10:30:00Z

    Returns:
        Formatted string with current environment details

    Raises:
        RuntimeError: If no environment is active (should not happen in normal operation)
    """
```

**Error Scenarios**:

| Error Condition | Error Message |
|----------------|---------------|
| No active environment | "No active environment set. This should not happen. Please restart the server." |

---

## Modified MCP Tools

The following existing MCP tools will be modified to use the active environment's credentials instead of reading directly from environment variables:

### Affected Tools

1. `run_sql_query(sql: str)`
2. `list_jobs()`
3. `get_job_status(job_id: int)`
4. `get_job_details(job_id: int)`
5. `create_cluster(...)`
6. `delete_cluster(cluster_id: str, confirm: bool)`
7. `list_clusters()`
8. `get_cluster_status(cluster_id: str)`

### Changes Required

**Before** (current implementation in main.py):

```python
# Global credentials from environment variables
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")

def get_databricks_connection() -> Connection:
    """Create and return a Databricks SQL connection"""
    if not all([DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_HTTP_PATH]):
        raise ValueError("Missing required Databricks connection details in .env file")

    return connect(
        server_hostname=DATABRICKS_HOST,
        http_path=DATABRICKS_HTTP_PATH,
        access_token=DATABRICKS_TOKEN
    )
```

**After** (using environment manager):

```python
from config.manager import EnvironmentManager

# Initialize environment manager
env_manager = EnvironmentManager()

def get_databricks_connection() -> Connection:
    """Create and return a Databricks SQL connection using active environment"""
    credentials = env_manager.get_active_credentials()

    if not credentials:
        raise ValueError("No active environment configured")

    return connect(
        server_hostname=credentials['host'],
        http_path=credentials['http_path'],
        access_token=credentials['token']
    )
```

**Error Handling Enhancement**:

All modified tools will now include error handling for invalid/expired credentials as per clarification:

```python
@mcp.tool()
def run_sql_query(sql: str) -> str:
    """Execute SQL queries on Databricks SQL warehouse"""
    try:
        conn = get_databricks_connection()
        # ... existing logic
    except Exception as e:
        # Fail immediately per clarification requirement
        logger.error(f"Failed to connect to Databricks: {e}")
        return (
            f"Error: Failed to connect to Databricks.\n"
            f"Current environment: {env_manager.get_active_environment_name()}\n"
            f"Details: {str(e)}\n\n"
            f"Please check your credentials or switch to a different environment using switch_environment()."
        )
```

---

## Tool Registration

**Startup Sequence** (in `main.py`):

```python
from config.manager import EnvironmentManager
from config.watcher import ConfigWatcher
from tools.list_environments import list_environments
from tools.switch_environment import switch_environment
from tools.get_current_environment import get_current_environment

# 1. Initialize environment manager
env_manager = EnvironmentManager()
env_manager.load_configuration()  # Loads environments.yaml or falls back to .env
env_manager.set_active_to_default()

# 2. Start configuration file watcher
config_watcher = ConfigWatcher(env_manager)
config_watcher.start()

# 3. Initialize MCP server
mcp = FastMCP("Databricks API Explorer")

# 4. Register new environment management tools
mcp.tool()(list_environments)
mcp.tool()(switch_environment)
mcp.tool()(get_current_environment)

# 5. Register existing tools (modified to use env_manager)
# ... existing tool registrations

if __name__ == "__main__":
    mcp.run()
```

---

## Logging Requirements

All environment-related operations must be logged according to the specification:

### Log Format

```python
import logging

logger = logging.getLogger('databricks_mcp.environment')
logger.setLevel(logging.INFO)

# Add timestamp and context
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Log Events

| Event | Level | Format | Example |
|-------|-------|--------|---------|
| Environment switch | INFO | `Environment switched: {old} → {new}` | `Environment switched: dev → prod` |
| Configuration loaded | INFO | `Configuration loaded: {source} ({count} environments)` | `Configuration loaded: environments.yaml (3 environments)` |
| Configuration reloaded | WARNING | `Configuration file changed, reloading: {file}` | `Configuration file changed, reloading: environments.yaml` |
| Switch error | ERROR | `Failed to switch environment: {error}` | `Failed to switch environment: Environment 'staging' not found` |
| Invalid credentials | ERROR | `Invalid credentials for environment {name}: {error}` | `Invalid credentials for environment prod: Connection refused` |
| Missing default | ERROR | `No default environment specified in {file}` | `No default environment specified in environments.yaml` |
| Backward compat fallback | WARNING | `environments.yaml not found, using legacy .env configuration` | N/A |

**Security Note**: Never log credential values (tokens). Mask them in logs:

```python
# BAD
logger.info(f"Loaded environment with token: {token}")

# GOOD
logger.info(f"Loaded environment with token: {token[:8]}...")
```

---

## Testing Contracts

### Unit Test Examples

```python
import pytest
from tools.list_environments import list_environments
from tools.switch_environment import switch_environment
from config.manager import EnvironmentManager

def test_list_environments_returns_markdown_table():
    """Test that list_environments returns properly formatted markdown."""
    result = list_environments()
    assert "| Environment |" in result
    assert "| Host |" in result
    assert "|---|" in result or "|--" in result

def test_switch_environment_success():
    """Test successful environment switch."""
    result = switch_environment("prod")
    assert "✓ Switched to environment: prod" in result
    assert "Host:" in result

def test_switch_environment_not_found():
    """Test switch to non-existent environment fails gracefully."""
    with pytest.raises(ValueError, match="Environment 'nonexistent' not found"):
        switch_environment("nonexistent")

def test_get_current_environment_shows_active():
    """Test that get_current_environment returns active env details."""
    switch_environment("dev")
    result = get_current_environment()
    assert "Current environment: dev" in result
    assert "Activated at:" in result
```

### Integration Test Examples

```python
def test_end_to_end_environment_switching():
    """Test complete flow of listing, switching, and querying."""
    # 1. List environments
    envs = list_environments()
    assert "dev" in envs
    assert "prod" in envs

    # 2. Switch to dev
    switch_environment("dev")

    # 3. Verify current
    current = get_current_environment()
    assert "dev" in current

    # 4. Run a query (should use dev credentials)
    result = run_sql_query("SELECT 1 as test")
    assert "test" in result

    # 5. Switch to prod
    switch_environment("prod")

    # 6. Run same query (should use prod credentials)
    result = run_sql_query("SELECT 1 as test")
    assert "test" in result
```

---

## Performance Requirements

Per specification:

| Operation | Target | Notes |
|-----------|--------|-------|
| Environment switch | < 5 seconds | Includes validation and logging |
| List environments | < 1 second | Simple in-memory operation |
| Get current environment | < 100ms | Direct memory access |
| Configuration reload | < 2 seconds | File I/O + parsing + validation |
| Error response | < 1 second | Fast-fail on validation errors |

---

## Next Steps

See [quickstart.md](./quickstart.md) for usage examples and [../tasks.md](../tasks.md) for implementation tasks (generated by `/speckit.tasks`).
