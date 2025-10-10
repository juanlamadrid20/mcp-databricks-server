# Feature Specification: Multi-Environment Configuration Support

**Feature Branch**: `001-update-mcp-project`
**Created**: 2025-10-09
**Status**: Draft
**Input**: User description: "update MCP project to allow use of multiple env configurations. Currently in .env file I have 2 sets of environment variables, e.g. databricks_token. Update project to accomodate multiple environments for the respective mcp tools."

## Clarifications

### Session 2025-10-09

- Q: When a developer attempts to use MCP tools with invalid or expired Databricks credentials, what should happen? → A: Fail immediately with error message, require manual environment switch
- Q: When a developer modifies the environment configuration file while the MCP server is running, how should the system handle this? → A: Auto-reload configuration immediately when file changes detected
- Q: When the MCP server starts with multiple environments configured but no default specified and no environment explicitly selected, what should happen? → A: Fail to start with error requiring default configuration
- Q: What level of logging should be provided for environment-related operations (switching, loading, errors)? → A: Standard: Log errors, warnings, and environment switches

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Switch Between Databricks Environments (Priority: P1)

A developer needs to connect to different Databricks workspaces (e.g., development, staging, production, or different client environments) without manually editing the `.env` file each time they switch contexts.

**Why this priority**: This is the core functionality that enables the feature's value proposition. Without the ability to switch environments, the feature provides no benefit. This represents the minimum viable product (MVP).

**Independent Test**: Can be fully tested by configuring two environments (e.g., "dev" and "prod"), switching to each, and verifying that MCP tools connect to the correct Databricks workspace by running a simple SQL query and confirming the results match the expected environment.

**Acceptance Scenarios**:

1. **Given** multiple Databricks environments are configured with different credentials, **When** the developer selects an environment by name, **Then** all MCP tools use the credentials for that selected environment
2. **Given** the developer is connected to environment A, **When** they switch to environment B, **Then** subsequent MCP tool calls connect to environment B's Databricks workspace
3. **Given** no environment is explicitly selected, **When** MCP tools are invoked, **Then** a default environment is used automatically

---

### User Story 2 - Configure Multiple Environments (Priority: P2)

A developer needs to define and store credentials for multiple Databricks environments in a structured way that is easy to manage and doesn't require code changes.

**Why this priority**: This enables the setup and management of environments but isn't required for testing the core switching functionality (which could work with hardcoded test environments initially). However, it's essential for practical use.

**Independent Test**: Can be fully tested by creating a configuration with 3+ environments (each with distinct host, token, and HTTP path values), loading the configuration, and verifying that each environment's credentials are correctly stored and retrievable.

**Acceptance Scenarios**:

1. **Given** a configuration file or structure exists, **When** the developer adds a new environment with credentials (host, token, HTTP path), **Then** the environment is available for selection
2. **Given** multiple environments are configured, **When** the system loads the configuration, **Then** all environments are available and accessible
3. **Given** an environment configuration is updated, **When** the developer switches to that environment, **Then** the updated credentials are used

---

### User Story 3 - List and Verify Available Environments (Priority: P3)

A developer needs to see which environments are configured and verify which environment is currently active to avoid accidentally running operations against the wrong workspace.

**Why this priority**: This is a quality-of-life improvement that prevents errors but isn't required for the core switching functionality. Users could track the current environment manually initially.

**Independent Test**: Can be fully tested by configuring 3 environments, selecting one, listing all available environments, and verifying that the output shows all environment names and clearly indicates which one is currently active.

**Acceptance Scenarios**:

1. **Given** multiple environments are configured, **When** the developer requests a list of environments, **Then** all configured environment names are displayed
2. **Given** an environment is currently selected, **When** the developer requests the current environment, **Then** the active environment name is returned
3. **Given** environment configurations include optional metadata (description, workspace type), **When** the developer lists environments, **Then** the metadata is displayed alongside environment names

---

### Edge Cases

- What happens when a developer tries to switch to an environment that doesn't exist in the configuration?
- What happens when required credentials (host, token, HTTP path) are missing for a configured environment?
- How does the system handle the transition from the old single-environment `.env` file to the new multi-environment configuration?
- When environment credentials are invalid or expired, the system fails immediately with a clear error message and requires manual environment switch (no automatic retry or fallback)
- What happens if two environments have the same name?
- When no default environment is specified in a multi-environment configuration, the MCP server fails to start with an error message requiring the developer to configure a default environment

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support defining multiple Databricks environment configurations, each containing at minimum: host, token, and HTTP path
- **FR-002**: System MUST allow switching between configured environments by name
- **FR-003**: System MUST apply the selected environment's credentials to all MCP tools (SQL queries, job operations, cluster operations)
- **FR-004**: System MUST require a default environment to be specified in multi-environment configurations and fail to start if no default is configured
- **FR-005**: System MUST validate that required credentials exist for an environment before allowing it to be selected
- **FR-006**: System MUST provide a way to list all configured environment names
- **FR-007**: System MUST provide a way to identify which environment is currently active
- **FR-008**: System MUST maintain environment configurations in a file-based format that doesn't require code changes to add/modify environments
- **FR-009**: System MUST continue to function with existing single-environment `.env` configurations (backward compatibility)
- **FR-010**: System MUST prevent switching to an environment that doesn't exist or has incomplete credentials
- **FR-011**: Users MUST be able to add environment-specific metadata such as descriptions or tags
- **FR-012**: System MUST ensure environment names are unique within a configuration
- **FR-013**: System MUST fail immediately with a clear error message when MCP tools encounter invalid or expired credentials, without automatic retry or fallback to other environments
- **FR-014**: System MUST monitor the configuration file for changes and automatically reload the configuration when modifications are detected
- **FR-015**: System MUST log errors, warnings, and environment switch operations to support troubleshooting and audit trails

### Key Entities *(include if feature involves data)*

- **Environment Configuration**: Represents a complete Databricks workspace connection setup, containing host URL, access token, HTTP path for SQL warehouse, optional name/description, and optional metadata. Multiple configurations can exist simultaneously.
- **Active Environment**: Represents the currently selected environment whose credentials are being used by all MCP tools. Only one environment can be active at a time per MCP server instance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can switch between environments in under 5 seconds without editing files
- **SC-002**: System supports at minimum 10 different environment configurations without performance degradation
- **SC-003**: 100% of existing MCP tools (SQL queries, job operations, cluster operations) work correctly after switching environments
- **SC-004**: Developers can successfully migrate from single-environment `.env` to multi-environment configuration without data loss
- **SC-005**: Invalid environment selection attempts provide clear error messages within 1 second
- **SC-006**: Environment listing operations return results within 1 second regardless of number of configured environments
- **SC-007**: All environment switches, configuration reloads, errors, and warnings are logged with timestamps and context for troubleshooting

## Assumptions *(mandatory)*

- Each Databricks environment requires the same three credential components: host, token, and HTTP path
- Environment configurations are monitored for file changes and automatically reloaded when modifications are detected
- The MCP server serves a single user/session at a time (no concurrent multi-environment access needed)
- Environment credentials are still stored securely (not in source control) using standard practices
- Multi-environment configurations require an explicitly configured default environment; single-environment `.env` configurations implicitly use that environment as default
- Environment switching does not require restarting the MCP server
- Configuration file format will be human-readable and editable (JSON, YAML, or similar structured format)

## Dependencies

- Existing MCP tool implementations must be refactored to read credentials from the active environment rather than directly from environment variables
- Environment configuration structure must be designed before implementation can begin

## Out of Scope

- Runtime environment creation/deletion through MCP tools (environments are pre-configured, not created on-the-fly)
- Multi-user or concurrent multi-environment access (multiple users using different environments simultaneously)
- Environment credential encryption beyond standard `.env` file security practices
- Automatic environment detection based on context or project directory
- Integration with external credential management systems (e.g., HashiCorp Vault, AWS Secrets Manager)
- Environment-specific configuration beyond Databricks credentials (e.g., different MCP tool behaviors per environment)
- GUI or web interface for managing environments
