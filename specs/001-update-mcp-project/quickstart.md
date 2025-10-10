# Quickstart Guide: Multi-Environment Configuration

**Feature**: 001-update-mcp-project
**Date**: 2025-10-09

## Overview

This guide shows how to configure and use multiple Databricks environments with the MCP server.

---

## For Existing Users (Backward Compatibility)

If you're already using the MCP server with a `.env` file, **nothing changes**. Your existing setup will continue to work:

```bash
# Your existing .env file works as-is
DATABRICKS_HOST=my-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi_your_token_here
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your_warehouse_id
```

The server will automatically detect and use your `.env` configuration.

---

## Setting Up Multi-Environment Configuration

### Step 1: Create environments.yaml

Create a file named `environments.yaml` in your project root:

```yaml
default: development

environments:
  development:
    name: development
    host: dev-workspace.cloud.databricks.com
    token: dapi_dev_token_123
    http_path: /sql/1.0/warehouses/dev_warehouse_id
    description: "Development environment for testing"
    tags:
      - dev
      - testing

  production:
    name: production
    host: prod-workspace.cloud.databricks.com
    token: dapi_prod_token_456
    http_path: /sql/1.0/warehouses/prod_warehouse_id
    description: "Production environment"
    tags:
      - production
      - critical
```

### Step 2: Secure Your Configuration

Add `environments.yaml` to `.gitignore`:

```bash
echo "environments.yaml" >> .gitignore
```

### Step 3: Create a Template (Optional)

Create `environments.yaml.template` with placeholder values for documentation:

```yaml
default: development

environments:
  development:
    name: development
    host: your-dev-workspace.cloud.databricks.com
    token: dapi_your_dev_token_here
    http_path: /sql/1.0/warehouses/your_dev_warehouse_id
    description: "Development environment"
    tags:
      - dev

  production:
    name: production
    host: your-prod-workspace.cloud.databricks.com
    token: dapi_your_prod_token_here
    http_path: /sql/1.0/warehouses/your_prod_warehouse_id
    description: "Production environment"
    tags:
      - production
```

**Commit the template** (not the real `environments.yaml`):

```bash
git add environments.yaml.template
git commit -m "Add environment configuration template"
```

---

## Using the Environment Management Tools

### Starting the Server

```bash
python main.py
```

You'll see logs indicating which configuration was loaded:

```
INFO - Configuration loaded: environments.yaml (2 environments)
INFO - Active environment set to: development
```

### List Available Environments

Use the `list_environments` MCP tool:

**Input**: None

**Output**:
```markdown
| Environment | Host | Description | Tags | Status |
|-------------|------|-------------|------|--------|
| development | dev-workspace.cloud.databricks.com | Development environment for testing | dev, testing | ACTIVE |
| production | prod-workspace.cloud.databricks.com | Production environment | production, critical | - |
```

### Switch to a Different Environment

Use the `switch_environment` MCP tool:

**Input**: `name: "production"`

**Output**:
```
✓ Switched to environment: production
Host: prod-workspace.cloud.databricks.com
Description: Production environment
Tags: production, critical
```

The server logs will show:
```
INFO - Environment switched: development → production
```

### Check Current Environment

Use the `get_current_environment` MCP tool:

**Input**: None

**Output**:
```
Current environment: production
Host: prod-workspace.cloud.databricks.com
Description: Production environment
Tags: production, critical
Activated at: 2025-10-09T15:30:45Z
```

---

## Common Use Cases

### Use Case 1: Testing Queries in Dev Before Running in Prod

```
1. Start server (automatically uses default environment: development)

2. Run your query using run_sql_query:
   → Uses development environment credentials

3. Verify results look correct

4. Switch to production:
   switch_environment("production")

5. Run the same query:
   → Now uses production environment credentials
```

### Use Case 2: Managing Multiple Client Environments

Create an `environments.yaml` with multiple client configs:

```yaml
default: client-acme

environments:
  client-acme:
    name: client-acme
    host: acme-workspace.cloud.databricks.com
    token: dapi_acme_token
    http_path: /sql/1.0/warehouses/acme_warehouse
    description: "ACME Corp workspace"
    tags:
      - client
      - acme

  client-globex:
    name: client-globex
    host: globex-workspace.cloud.databricks.com
    token: dapi_globex_token
    http_path: /sql/1.0/warehouses/globex_warehouse
    description: "Globex Corporation workspace"
    tags:
      - client
      - globex
```

Switch between clients as needed:
```
switch_environment("client-globex")
→ All subsequent operations use Globex credentials
```

### Use Case 3: Automatic Configuration Reload

If you edit `environments.yaml` while the server is running:

**Before**:
```yaml
default: dev

environments:
  dev:
    name: dev
    host: old-dev-host.cloud.databricks.com
    token: dapi_old_token
    http_path: /sql/1.0/warehouses/old_warehouse
```

**After** (edit the file):
```yaml
default: dev

environments:
  dev:
    name: dev
    host: new-dev-host.cloud.databricks.com  # Changed
    token: dapi_new_token                     # Changed
    http_path: /sql/1.0/warehouses/new_warehouse  # Changed

  staging:  # New environment added
    name: staging
    host: staging-host.cloud.databricks.com
    token: dapi_staging_token
    http_path: /sql/1.0/warehouses/staging_warehouse
```

**Server automatically detects and reloads**:
```
WARNING - Configuration file changed, reloading: environments.yaml
INFO - Configuration loaded: environments.yaml (2 environments)
```

The next MCP tool call will use the updated credentials.

---

## Migration from .env to environments.yaml

### Option 1: Keep Using .env

No action needed. Your `.env` file continues to work.

### Option 2: Migrate to Multi-Environment

**Step 1**: Copy your current `.env` credentials:

```bash
# .env
DATABRICKS_HOST=my-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi_my_token_123
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/my_warehouse
```

**Step 2**: Create `environments.yaml` with your current config as the default:

```yaml
default: production

environments:
  production:
    name: production
    host: my-workspace.cloud.databricks.com
    token: dapi_my_token_123
    http_path: /sql/1.0/warehouses/my_warehouse
    description: "Migrated from .env"
```

**Step 3**: Test the new configuration:

```bash
python main.py
# Should log: "Configuration loaded: environments.yaml (1 environments)"
```

**Step 4** (optional): Keep `.env` as a backup or delete it:

```bash
# Option A: Rename as backup
mv .env .env.backup

# Option B: Delete it
rm .env
```

**Step 5**: Add more environments as needed:

```yaml
default: production

environments:
  production:
    name: production
    host: my-workspace.cloud.databricks.com
    token: dapi_my_token_123
    http_path: /sql/1.0/warehouses/my_warehouse
    description: "Production (migrated from .env)"

  development:  # New!
    name: development
    host: dev-workspace.cloud.databricks.com
    token: dapi_dev_token_456
    http_path: /sql/1.0/warehouses/dev_warehouse
    description: "Development environment"
```

---

## Troubleshooting

### Error: "No default environment specified"

**Problem**: Your `environments.yaml` is missing the `default` field.

**Solution**: Add `default: <environment-name>` at the top:

```yaml
default: development  # Add this line

environments:
  development:
    # ...
```

### Error: "Environment 'X' not found"

**Problem**: You tried to switch to an environment that doesn't exist.

**Solution**: List available environments first:

```
list_environments()
→ Shows: development, production

switch_environment("development")  # Use one from the list
```

### Error: "Invalid credentials"

**Problem**: One of your environments has incomplete or invalid credentials.

**Solution**: Check that each environment has all required fields:

```yaml
environments:
  my-env:
    name: my-env
    host: workspace.cloud.databricks.com      # Required
    token: dapi_token_here                    # Required, must start with "dapi"
    http_path: /sql/1.0/warehouses/id         # Required, must match pattern
    description: "Optional description"       # Optional
    tags: [optional, tags]                    # Optional
```

### Warning: "Configuration file changed, reloading"

**Not an error!** This means the server detected that you edited `environments.yaml` and automatically reloaded it. Your changes are now active.

### Server Uses .env Instead of environments.yaml

**Problem**: Both files exist, but you want to use `environments.yaml`.

**Solution**: The server prefers `environments.yaml` over `.env`. If it's using `.env`, check:

1. Is `environments.yaml` in the correct directory (project root)?
2. Is `environments.yaml` valid YAML? (Check for syntax errors)
3. Check server logs for parsing errors

---

## Security Best Practices

### 1. Never Commit Credentials

**Add to `.gitignore`**:
```
.env
environments.yaml
```

**Commit only templates**:
```
environments.yaml.template
```

### 2. Use Template Files for Documentation

Create `environments.yaml.template` with placeholders:

```yaml
default: development

environments:
  development:
    name: development
    host: YOUR_DEV_HOST_HERE
    token: YOUR_DEV_TOKEN_HERE
    http_path: YOUR_DEV_HTTP_PATH_HERE
    description: "Development environment"

  production:
    name: production
    host: YOUR_PROD_HOST_HERE
    token: YOUR_PROD_TOKEN_HERE
    http_path: YOUR_PROD_HTTP_PATH_HERE
    description: "Production environment"
```

### 3. File Permissions

Restrict access to configuration files:

```bash
chmod 600 environments.yaml
chmod 600 .env
```

### 4. Token Rotation

When rotating tokens:

1. Edit `environments.yaml` with new token
2. Server auto-reloads (no restart needed)
3. Next MCP tool call uses new credentials

---

## Example Workflows

### Workflow: Daily Development

```
Morning:
1. Start server → Auto-loads development environment
2. Run queries, test jobs, explore data
3. All operations use development credentials

Afternoon (deploy to production):
1. switch_environment("production")
2. Run production queries/jobs
3. All operations now use production credentials

End of day:
1. Server still running
2. Tomorrow it remembers last active environment
   OR auto-resets to default (development) on restart
```

### Workflow: Multi-Client Support

```
Client A meeting:
1. switch_environment("client-a")
2. Run analysis queries
3. Generate reports

Client B meeting:
1. switch_environment("client-b")
2. Run same analysis
3. Generate reports with different data source
```

### Workflow: Configuration Updates

```
Need to add a new environment:
1. Edit environments.yaml (add new environment)
2. Save file
3. Server auto-detects change and reloads
4. New environment immediately available
5. list_environments() shows new environment
6. switch_environment("new-env") works
```

---

## Next Steps

- Read [data-model.md](./data-model.md) for detailed entity definitions
- Read [contracts/mcp-tools.md](./contracts/mcp-tools.md) for complete API documentation
- Run `/speckit.tasks` to generate implementation tasks

---

## Getting Help

If you encounter issues:

1. Check server logs for detailed error messages
2. Verify your `environments.yaml` syntax (use a YAML validator)
3. Ensure all required fields are present
4. Test with `list_environments()` to see if configuration loaded correctly
5. Try switching back to default environment: `switch_environment("default-env-name")`
