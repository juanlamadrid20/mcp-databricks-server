# Databricks MCP Server

A Model Context Protocol (MCP) server that connects to Databricks API, allowing LLMs to run SQL queries, list jobs, and get job status.

## Features

- **Multi-Environment Support**: Manage multiple Databricks environments (dev, staging, prod)
- **Flexible Authentication**: Support for both profile-based (CLI) and token-based authentication
- **SQL Queries**: Run SQL queries on Databricks SQL warehouses
- **Job Management**: List, monitor, and get details about Databricks jobs
- **Cluster Management**: Create, delete, and monitor Databricks clusters
- **Environment Switching**: Dynamically switch between configured environments

## Prerequisites

- Python 3.7+
- Databricks workspace with:
  - Personal access token
  - SQL warehouse endpoint
  - Permissions to run queries and access jobs

## Setup

1. Clone this repository
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

This server supports two authentication methods:

#### Option 1: Profile-Based Authentication (Recommended)

Uses your existing Databricks CLI configuration (`~/.databrickscfg`). This method supports multiple authentication types including OAuth, Azure CLI, and Personal Access Tokens.

1. **Set up Databricks CLI profiles** (if not already done):
   ```bash
   databricks configure --profile dev
   databricks configure --profile staging
   databricks configure --profile production
   ```

2. **Create `environments.yaml`** from the template:
   ```bash
   cp environments.yaml.template environments.yaml
   ```

3. **Edit `environments.yaml`** to reference your profiles:
   ```yaml
   default: development

   environments:
     development:
       name: development
       profile: dev  # References [dev] in ~/.databrickscfg
       host: your-dev-workspace.cloud.databricks.com
       http_path: /sql/1.0/warehouses/your-warehouse-id
       description: "Development environment"
       tags: [dev, cli-auth]
     
     staging:
       name: staging
       profile: staging  # References [staging] in ~/.databrickscfg
       host: your-staging-workspace.cloud.databricks.com
       http_path: /sql/1.0/warehouses/your-warehouse-id
       description: "Staging environment"
       tags: [staging, cli-auth]
   ```

#### Option 2: Token-Based Authentication (Legacy)

Directly embed Personal Access Tokens in the configuration file.

1. **Create `environments.yaml`** from the template:
   ```bash
   cp environments.yaml.template environments.yaml
   ```

2. **Edit `environments.yaml`** with your tokens:
   ```yaml
   default: development

   environments:
     development:
       name: development
       token: dapi_your_dev_token_here
       host: your-dev-workspace.cloud.databricks.com
       http_path: /sql/1.0/warehouses/your-warehouse-id
       description: "Development environment"
       tags: [dev]
   ```

**Note**: Each environment must use EITHER `profile` OR `token`, not both.

#### Legacy .env File Support

For backward compatibility, single-environment configuration using `.env` file is still supported:
```bash
DATABRICKS_HOST=your-databricks-instance.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
```

### Testing Your Configuration

Test your connection (optional but recommended):
```bash
python test_connection.py
```

### Obtaining Databricks Credentials

1. **Host**: Your Databricks instance URL (e.g., `your-instance.cloud.databricks.com`)
2. **Token**: Create a personal access token in Databricks:
   - Go to User Settings (click your username in the top right)
   - Select "Developer" tab
   - Click "Manage" under "Access tokens"
   - Generate a new token, and save it immediately
3. **HTTP Path**: For your SQL warehouse:
   - Go to SQL Warehouses in Databricks
   - Select your warehouse
   - Find the connection details and copy the HTTP Path

## Running the Server

Start the MCP server:
```
python main.py
```

You can test the MCP server using the inspector by running 

```
npx @modelcontextprotocol/inspector python3 main.py
```

## Available MCP Tools

### Environment Management
1. **mcp_get_current_environment()** - Get the currently active Databricks environment
2. **mcp_switch_environment(name: str)** - Switch to a different configured environment

### SQL & Data
3. **run_sql_query(sql: str)** - Execute SQL queries on your Databricks SQL warehouse

### Jobs
4. **list_jobs()** - List all Databricks jobs in your workspace
5. **get_job_status(job_id: int)** - Get the status of a specific Databricks job by ID
6. **get_job_details(job_id: int)** - Get detailed information about a specific Databricks job

### Clusters
7. **create_cluster(...)** - Create a new Databricks cluster with specified configuration
8. **delete_cluster(cluster_id: str, confirm: bool)** - Delete a Databricks cluster
9. **list_clusters()** - List all Databricks clusters
10. **get_cluster_status(cluster_id: str)** - Get status and details of a specific cluster

## Example Usage with LLMs

When used with LLMs that support the MCP protocol, this server enables natural language interaction with your Databricks environment:

### Environment Management
- "What environment am I currently using?"
- "Switch to the staging environment"
- "Switch to production"

### Data & SQL
- "Show me all tables in the database"
- "Run a query to count records in the customer table"
- "Get the top 10 customers by revenue"

### Jobs & Clusters
- "List all my Databricks jobs"
- "Check the status of job #123"
- "Show me details about job #456"
- "List all clusters"
- "Create a new development cluster"

## Troubleshooting

### Connection Issues

- Ensure your Databricks host is correct and doesn't include `https://` prefix
- Check that your SQL warehouse is running and accessible
- Verify your personal access token has the necessary permissions
- Run the included test script: `python test_connection.py`

## Authentication Methods Comparison

| Feature | Profile-Based (CLI) | Token-Based |
|---------|---------------------|-------------|
| **Setup** | Use `databricks configure` | Manual token generation |
| **Security** | Tokens stored in `~/.databrickscfg` | Tokens in `environments.yaml` |
| **Auth Types** | OAuth, Azure CLI, PAT, etc. | Personal Access Token only |
| **Token Refresh** | Automatic (for OAuth) | Manual |
| **Multi-user** | Per-user config | Shared config |
| **Recommended For** | Development, personal use | CI/CD, shared environments |

## Security Considerations

- **Profile-based auth**: Tokens are stored in `~/.databrickscfg` (not in repo)
- **Token-based auth**: Tokens are in `environments.yaml` - **NEVER commit this file!**
- Add `environments.yaml` to `.gitignore` (already configured)
- Use appropriate permission scopes for your tokens
- Consider using OAuth or Azure CLI for enhanced security
- Profile-based auth supports automatic token refresh for OAuth
- Run this server in a secure environment

## Multi-Environment Best Practices

1. **Use profile-based auth** for local development
2. **Use token-based auth** for CI/CD pipelines and automation
3. **Separate environments** for dev, staging, and production
4. **Tag environments** appropriately for easy identification
5. **Never commit** `environments.yaml` to version control
6. **Rotate tokens** regularly for security
7. **Use least-privilege** access for each environment
