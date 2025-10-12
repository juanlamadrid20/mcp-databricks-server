# Implementation Plan: Multi-Environment Configuration Support

**Branch**: `001-update-mcp-project` | **Date**: 2025-10-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-update-mcp-project/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enable MCP Databricks server to support multiple environment configurations, allowing developers to switch between different Databricks workspaces (dev, staging, production, client environments) without manually editing configuration files. The system will monitor configuration changes, validate credentials, provide environment listing capabilities, and maintain backward compatibility with existing single-environment `.env` setups.

## Technical Context

**Language/Version**: Python 3.7+
**Primary Dependencies**: FastMCP (mcp>=0.1.0), python-dotenv>=1.0.0, databricks-sql-connector>=2.4.0, databricks-sdk>=0.18.0, watchdog (NEEDS RESEARCH: file watching library)
**Storage**: File-based configuration (YAML format - NEEDS RESEARCH: best practices for multi-env config structure)
**Testing**: pytest (NEEDS RESEARCH: current testing setup)
**Target Platform**: Server-side Python application (CLI/MCP server)
**Project Type**: Single project (MCP server application)
**Performance Goals**: <5s environment switch, <1s config listing, file reload <2s
**Constraints**: <1s error response time, must not disrupt active connections during reload
**Scale/Scope**: Support 10+ environments, single user/session, no concurrent multi-env access

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: No constitution file found with defined principles. Proceeding with standard software engineering best practices:

- ✅ **Backward Compatibility**: Existing `.env` configurations must continue to work
- ✅ **Fail-Fast**: Invalid states (missing default, bad credentials) must fail immediately with clear errors
- ✅ **Testability**: All components must be independently testable
- ✅ **Observability**: Logging for debugging and audit trails required
- ✅ **Simplicity**: Use existing Python ecosystem tools, avoid custom frameworks

**Status**: PASS - No violations identified

## Project Structure

### Documentation (this feature)

```
specs/001-update-mcp-project/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
mcp-databricks-server/
├── main.py                      # Entry point, MCP server initialization
├── config/                      # NEW: Environment configuration management
│   ├── __init__.py
│   ├── loader.py                # Load and parse environment configs
│   ├── manager.py               # Environment switching logic
│   ├── validator.py             # Credential validation
│   └── watcher.py               # File change monitoring
├── models/                      # NEW: Data models
│   ├── __init__.py
│   └── environment.py           # Environment configuration model
├── tools/                       # NEW: Environment management MCP tools
│   ├── __init__.py
│   ├── list_environments.py     # List configured environments
│   ├── switch_environment.py    # Switch active environment
│   └── get_current_environment.py  # Get current environment
├── utils/                       # NEW: Shared utilities
│   ├── __init__.py
│   └── logger.py                # Logging configuration
├── .env                         # Existing single-env config (backward compat)
├── environments.yaml            # NEW: Multi-environment configuration file
├── requirements.txt             # Update with new dependencies
└── tests/                       # NEW: Test suite
    ├── __init__.py
    ├── unit/
    │   ├── test_loader.py
    │   ├── test_manager.py
    │   ├── test_validator.py
    │   └── test_watcher.py
    ├── integration/
    │   ├── test_environment_switching.py
    │   └── test_backward_compatibility.py
    └── fixtures/
        ├── test_environments.yaml
        └── test.env
```

**Structure Decision**: Single project structure selected. This is a server-side application with no frontend/backend separation. The new environment management functionality will be organized into focused modules (config, models, tools, utils) that integrate with the existing MCP server in `main.py`.

## Complexity Tracking

*No constitutional violations requiring justification.*

## Phase 0: Research & Technical Decisions

### Research Tasks

1. **File watching library selection**
   - **Decision**: Use `watchdog` library for cross-platform file system monitoring
   - **Rationale**: Industry-standard Python library, cross-platform support, actively maintained, simple API
   - **Alternatives considered**:
     - `inotify` (Linux-only, not cross-platform)
     - Custom polling (less efficient, more complex)
     - Manual reload command (doesn't meet auto-reload requirement from clarifications)

2. **Configuration file format**
   - **Decision**: Use YAML for multi-environment configuration
   - **Rationale**: Human-readable, supports nested structures, comments, widely used in DevOps
   - **Alternatives considered**:
     - JSON (no comments, less human-friendly)
     - TOML (less familiar for env configs)
     - Multiple .env files (harder to manage default environment)

3. **Testing framework and structure**
   - **Decision**: Use pytest with fixtures for test data, separate unit/integration tests
   - **Rationale**: Python standard, good mocking support, fixture system ideal for test environments
   - **Alternatives considered**: unittest (more verbose, less flexible)

4. **Credential storage security**
   - **Decision**: Continue using file-based storage (.env for single, YAML for multi), keep files out of source control
   - **Rationale**: Meets "standard practices" requirement, maintains current security posture, out-of-scope for vault integration per spec
   - **Alternatives considered**: External vault systems (explicitly out of scope)

5. **Environment switching mechanism**
   - **Decision**: Use singleton pattern for EnvironmentManager with in-memory active environment state
   - **Rationale**: Single user/session assumption, fast switching, no persistence needed
   - **Alternatives considered**: Database state (over-engineering for single-session use case)

6. **Backward compatibility strategy**
   - **Decision**: Check for `environments.yaml` first, fallback to `.env` if not found
   - **Rationale**: Zero-config migration for existing users, clear upgrade path
   - **Alternatives considered**: Forced migration (breaks existing setups)

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions.

**Key Entities**:
- **EnvironmentConfig**: Represents a single environment's Databricks credentials and metadata
- **EnvironmentsConfiguration**: Container for all environments with default selection
- **ActiveEnvironment**: Runtime state tracking currently selected environment

### API Contracts

See [contracts/](./contracts/) directory for complete MCP tool definitions.

**New MCP Tools**:
1. `list_environments()` - Returns all configured environment names and metadata
2. `switch_environment(name: str)` - Changes the active environment
3. `get_current_environment()` - Returns the currently active environment name

**Modified Behavior**:
- All existing MCP tools (`run_sql_query`, `list_jobs`, `get_job_status`, etc.) will read credentials from the active environment instead of directly from environment variables

### Integration Points

1. **main.py modifications**:
   - Initialize EnvironmentManager on startup
   - Start configuration file watcher
   - Register new environment management MCP tools
   - Modify existing tools to use active environment credentials

2. **Configuration loading flow**:
   - On startup: Load environments.yaml OR fallback to .env
   - Validate default environment exists
   - Set active environment to default
   - Start file watcher for auto-reload

3. **Environment switching flow**:
   - Validate environment exists
   - Validate credentials are complete
   - Update active environment
   - Log the switch operation

## Phase 2: Implementation Tasks

See [tasks.md](./tasks.md) - NOT created by this `/speckit.plan` command. Use `/speckit.tasks` to generate the dependency-ordered implementation tasks.
