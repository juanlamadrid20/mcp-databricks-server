# Research: Multi-Environment Configuration Support

**Feature**: 001-update-mcp-project
**Date**: 2025-10-09

## Overview

This document consolidates research findings for implementing multi-environment configuration support in the MCP Databricks server.

## Technical Decisions

### 1. File Watching Library

**Decision**: Use `watchdog` library (version >=3.0.0)

**Rationale**:
- Cross-platform support (Linux, macOS, Windows)
- Actively maintained with regular updates
- Simple, clean API for monitoring file system events
- Widely used in Python ecosystem (60M+ downloads/month)
- Built-in event handlers and observer patterns
- No external system dependencies

**Implementation approach**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('environments.yaml'):
            reload_configuration()
```

**Alternatives considered**:
- **inotify**: Linux-only, not portable
- **Custom polling**: Inefficient, CPU overhead, complexity
- **pyinotify**: Deprecated, Linux-only
- **Manual reload command**: Doesn't meet auto-reload requirement

**Dependencies**: Add `watchdog>=3.0.0` to requirements.txt

---

### 2. Configuration File Format

**Decision**: YAML format for multi-environment configuration

**File structure**:
```yaml
default: field-eng-west

environments:
  field-eng-west:
    host: e2-demo-field-eng.cloud.databricks.com
    token: dapi_your_token_here_1
    http_path: /sql/1.0/warehouses/4b9b953939869799
    description: "Field Engineering West demo environment"
    tags:
      - demo
      - west

  field-eng-west-dev:
    host: dbc-876e9c34-9f7d.cloud.databricks.com
    token: dapi_your_token_here_2
    http_path: /sql/1.0/warehouses/ea5487ea1c4a4495
    description: "Field Engineering West dev environment"
    tags:
      - dev
```

**Rationale**:
- Human-readable and editable
- Supports comments for documentation
- Nested structure ideal for multiple environments
- Native support in Python via PyYAML
- Industry standard for configuration in DevOps
- Similar to Docker Compose, Kubernetes configs

**Validation rules**:
- `default` field is required for multi-environment configs
- Each environment must have `host`, `token`, and `http_path`
- Environment names must be unique
- `description` and `tags` are optional

**Alternatives considered**:
- **JSON**: No comment support, less human-friendly, more verbose
- **TOML**: Less familiar for environment configs, more complex parsing
- **Multiple .env files**: Harder to manage default, no central config
- **INI files**: Limited nesting, outdated format

**Dependencies**: Add `pyyaml>=6.0.0` to requirements.txt

---

### 3. Testing Framework

**Decision**: pytest with fixtures and parametrized tests

**Test structure**:
```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_loader.py       # Config loading logic
│   ├── test_manager.py      # Environment switching
│   ├── test_validator.py    # Validation rules
│   └── test_watcher.py      # File monitoring
├── integration/             # End-to-end scenarios
│   ├── test_environment_switching.py
│   └── test_backward_compatibility.py
└── fixtures/               # Test data
    ├── test_environments.yaml
    ├── test_invalid.yaml
    └── test.env
```

**Rationale**:
- Already in Python ecosystem (compatible with current setup)
- Powerful fixture system for test data management
- Parametrized tests reduce duplication
- Good mocking capabilities (pytest-mock)
- Clear, readable test output
- Widely adopted standard

**Key testing patterns**:
- Use `tmp_path` fixture for file-based tests
- Mock file watcher events for unit tests
- Use real YAML files in fixtures for integration tests
- Parametrize tests for multiple environment scenarios

**Dependencies**: Add `pytest>=7.0.0`, `pytest-mock>=3.10.0` to requirements.txt (dev dependencies)

---

### 4. Credential Storage Security

**Decision**: Continue file-based storage with gitignore protection

**Security measures**:
- Add `environments.yaml` to `.gitignore`
- Keep `.env` in `.gitignore`
- Document in README to never commit credentials
- Log warnings if credential files have loose permissions (optional enhancement)

**Rationale**:
- Meets "standard practices" requirement from spec
- Maintains current security posture
- No additional complexity
- External vault integration explicitly out of scope
- Users can layer additional security (file encryption, vault mount) if needed

**Best practices documentation needed**:
- Example `environments.yaml.template` with placeholder values
- README section on secure credential management
- Warning in logs if running with example/default credentials

**Alternatives considered**:
- **HashiCorp Vault**: Out of scope per specification
- **AWS Secrets Manager**: Out of scope per specification
- **Environment variables only**: Doesn't support rich metadata, harder to manage multiple envs

---

### 5. Environment Switching Mechanism

**Decision**: Singleton EnvironmentManager with in-memory state

**Design pattern**:
```python
class EnvironmentManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.active_environment = None
        self.configurations = {}
```

**Rationale**:
- Single user/session assumption from spec
- Fast access (in-memory, no I/O)
- No persistence needed (ephemeral session state)
- Simple, testable design
- Thread-safe for single-threaded MCP server

**State management**:
- Active environment stored in memory
- Lost on server restart (acceptable - use default on startup)
- Switch operation validates before updating state
- Logging on every switch for audit trail

**Alternatives considered**:
- **Database state**: Over-engineering for single-session use case
- **File-based state**: Unnecessary I/O, complexity
- **Global variables**: Harder to test, less encapsulated

---

### 6. Backward Compatibility Strategy

**Decision**: Auto-detect configuration type on startup

**Detection logic**:
1. Check if `environments.yaml` exists
2. If yes → Load multi-environment configuration
3. If no → Check for `.env` file
4. If `.env` exists → Create implicit single-environment config
5. If neither → Error: No configuration found

**Migration path**:
- Users can continue using `.env` indefinitely
- No forced migration
- To adopt multi-env: Create `environments.yaml`, keep `.env` as backup
- Server logs which configuration mode is active

**Rationale**:
- Zero breaking changes for existing users
- Clear, progressive enhancement path
- Explicit logging helps users understand configuration state
- Maintains all existing functionality

**Edge cases handled**:
- Both `.env` and `environments.yaml` exist → Prefer `environments.yaml`, log warning
- Empty `.env` file → Error: Invalid configuration
- Malformed `environments.yaml` → Error with clear message, suggest `.env` fallback

**Alternatives considered**:
- **Forced migration**: Breaks existing setups, poor user experience
- **Configuration flag**: Additional complexity, confusing
- **Two separate code paths**: Maintenance burden

---

## Dependencies Summary

### Production Dependencies
```
watchdog>=3.0.0          # File system monitoring
pyyaml>=6.0.0           # YAML configuration parsing
```

### Development Dependencies
```
pytest>=7.0.0            # Testing framework
pytest-mock>=3.10.0      # Mocking for tests
```

### Existing Dependencies (no changes)
```
fastapi>=0.95.0
uvicorn>=0.22.0
databricks-sql-connector>=2.4.0
databricks-sdk>=0.18.0
python-dotenv>=1.0.0
pydantic>=2.0.0
mcp>=0.1.0
pyarrow>=14.0.1
requests>=2.31.0
packaging>=23.0
```

---

## Integration Considerations

### 1. Logging Strategy

Use Python's built-in `logging` module with structured formatting:

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Log environment switches
logger.info(f"Environment switched: {old_env} → {new_env}")

# Log configuration reloads
logger.warning(f"Configuration reloaded from {config_file}")

# Log errors
logger.error(f"Failed to switch environment: {error_message}")
```

**Log levels**:
- INFO: Environment switches, successful config loads
- WARNING: Config file changes detected, fallback to .env
- ERROR: Invalid credentials, missing default, switch failures

### 2. Error Messages

Clear, actionable error messages for common scenarios:

```
❌ No default environment specified in environments.yaml
   → Add 'default: <env-name>' to the top of your environments.yaml file

❌ Environment 'staging' not found
   → Available environments: dev, prod

❌ Invalid credentials for environment 'prod'
   → Missing required field: http_path

❌ Failed to connect to Databricks with current credentials
   → Please check your token and host are correct
```

### 3. Performance Optimization

- Cache parsed YAML in memory (only reload on file change)
- Validate environment on switch, not on every tool call
- Use lazy loading for WorkspaceClient initialization
- Keep file watcher overhead minimal (single observer)

---

## Risk Mitigation

### Risk 1: Configuration Reload During Active Operation

**Mitigation**:
- File watcher triggers async reload
- Active operations continue with current environment
- New operations use reloaded configuration
- Log warning when reload occurs

### Risk 2: Invalid Configuration After Edit

**Mitigation**:
- Validate YAML on reload before applying
- If invalid, keep current configuration and log error
- Provide clear error message with line number if possible

### Risk 3: Credential Exposure

**Mitigation**:
- Never log credential values (mask in logs)
- Document security best practices in README
- Provide template file without real credentials

---

## Next Steps

See [data-model.md](./data-model.md) for entity definitions and [contracts/](./contracts/) for API contracts.
