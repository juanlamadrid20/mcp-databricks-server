from typing import Dict, Any
from databricks.sql import connect
from databricks.sql.client import Connection
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import (
    AutoScale,
    DataSecurityMode,
    Kind
)
from mcp.server.fastmcp import FastMCP
import requests
import logging
import sys
import os
from pathlib import Path
from threading import Thread, Event
import signal
import subprocess
import json

# CRITICAL FIX: Set working directory to the script's directory
# This ensures environments.yaml can be found regardless of where the script is run from
script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)

# CRITICAL FIX: Remove all existing handlers and force everything to stderr
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure logging to stderr ONLY
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Import environment management
from config.manager import EnvironmentManager
from tools.switch_environment import switch_environment
from tools.get_current_environment import get_current_environment

# Initialize environment manager as None - will be lazily loaded
env_manager = None

# Initialize WorkspaceClient with error handling
# Note: WorkspaceClient will be lazily initialized when needed
w = None

# Set up the MCP server
mcp = FastMCP("Databricks API Explorer")


def run_with_timeout(func, timeout_seconds=5):
    """
    Run a function with a timeout to prevent hanging on authentication.
    
    Args:
        func: Callable to execute
        timeout_seconds: Maximum seconds to wait before timing out
        
    Returns:
        Result of the function call
        
    Raises:
        TimeoutError: If function doesn't complete within timeout
        Exception: Any exception raised by the function
    """
    result = [None]
    error = [None]
    done = Event()
    
    def wrapper():
        try:
            result[0] = func()
        except Exception as e:
            error[0] = e
        finally:
            done.set()
    
    thread = Thread(target=wrapper, daemon=True)
    thread.start()
    
    if done.wait(timeout_seconds):
        if error[0]:
            raise error[0]
        return result[0]
    else:
        raise TimeoutError(
            f"Operation timed out after {timeout_seconds} seconds. "
            f"This likely indicates an authentication issue requiring interactive login. "
            f"Please run: databricks auth login --profile <your-profile>"
        )


def get_token_from_cli(profile: str) -> str:
    """
    Get authentication token from Databricks CLI.
    
    This is more reliable than trying to extract from WorkspaceClient
    as it directly uses the CLI's authentication mechanism.
    
    Args:
        profile: The Databricks CLI profile name
        
    Returns:
        Access token string
        
    Raises:
        ValueError: If unable to get token from CLI
    """
    try:
        logger.info(f"Getting token from CLI for profile: {profile}")
        
        # Check for environment variable first (allows platform-specific config)
        databricks_cmd = os.getenv("DATABRICKS_CLI_PATH")
        
        if not databricks_cmd:
            # Try to find databricks CLI in common locations (cross-platform)
            databricks_paths = [
                "databricks",  # Try PATH first (works on all platforms)
            ]
            
            # Add platform-specific paths
            import platform
            if platform.system() == "Windows":
                # Windows-specific locations
                username = os.getenv("USERNAME", "")
                if username:
                    databricks_paths.extend([
                        rf"C:\Users\{username}\AppData\Local\Microsoft\WinGet\Packages\Databricks.DatabricksCLI_Microsoft.Winget.Source_8wekyb3d8bbwe\databricks.exe",
                    ])
            elif platform.system() == "Darwin":  # macOS
                # macOS-specific locations (Homebrew)
                databricks_paths.extend([
                    "/usr/local/bin/databricks",
                    "/opt/homebrew/bin/databricks",
                    os.path.expanduser("~/.local/bin/databricks"),
                ])
            else:  # Linux
                databricks_paths.extend([
                    "/usr/local/bin/databricks",
                    "/usr/bin/databricks",
                    os.path.expanduser("~/.local/bin/databricks"),
                ])
            
            # Find first working databricks CLI
            for path in databricks_paths:
                try:
                    test_result = subprocess.run(
                        [path, "--version"],
                        capture_output=True,
                        timeout=2
                    )
                    if test_result.returncode == 0:
                        databricks_cmd = path
                        logger.info(f"Found databricks CLI at: {path}")
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            if not databricks_cmd:
                raise FileNotFoundError(
                    "Databricks CLI not found. Please either:\n"
                    "1. Install databricks CLI and ensure it's in PATH, or\n"
                    "2. Set DATABRICKS_CLI_PATH environment variable in mcp.json"
                )
        else:
            logger.info(f"Using databricks CLI from DATABRICKS_CLI_PATH env var: {databricks_cmd}")
        
        result = subprocess.run(
            [databricks_cmd, "auth", "token", "--profile", profile],
            capture_output=True,
            text=True,
            timeout=10  # Increased from 5 to 10 seconds
        )
        
        if result.returncode != 0:
            logger.error(f"CLI returned error code {result.returncode}: {result.stderr}")
            raise ValueError(f"CLI returned error: {result.stderr}")
        
        # Parse JSON output
        logger.debug(f"Parsing CLI output (length: {len(result.stdout)} bytes)")
        token_data = json.loads(result.stdout)
        access_token = token_data.get("access_token")
        
        if not access_token:
            logger.error("No access_token found in CLI response")
            raise ValueError("No access_token in CLI response")
        
        logger.info(f"Successfully obtained token from CLI for profile: {profile}")
        return access_token
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"Databricks CLI command timed out after 10 seconds for profile: {profile}")
        raise TimeoutError(
            f"Databricks CLI timed out getting token for profile '{profile}'. "
            f"This may indicate expired credentials. "
            f"Please run: databricks auth login --profile {profile}"
        )
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse CLI JSON output: {e}. Output was: {result.stdout[:200]}")
        raise ValueError(f"Failed to parse CLI output: {e}")
    except FileNotFoundError as e:
        logger.error(f"Databricks CLI command not found - is it installed and in PATH?")
        raise ValueError(f"Databricks CLI not found. Please ensure 'databricks' command is in PATH")
    except Exception as e:
        logger.error(f"Unexpected error getting token from CLI: {type(e).__name__}: {e}")
        raise ValueError(f"Failed to get token from CLI: {e}")


def get_env_manager() -> EnvironmentManager:
    """Get or initialize the environment manager lazily."""
    global env_manager
    if env_manager is None:
        env_manager = EnvironmentManager()
        try:
            env_manager.load_configuration()
            env_manager.set_active_to_default()
            logger.info("Environment manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize environment manager: {e}")
            raise
    return env_manager


# Helper function to get a Databricks SQL connection
def get_databricks_connection() -> Connection:
    """Create and return a Databricks SQL connection using active environment.
    
    Supports both token-based and profile-based authentication:
    - Token-based: Uses access_token parameter
    - Profile-based: Uses Databricks SDK's unified auth (reads from ~/.databrickscfg)
    """
    try:
        credentials = get_env_manager().get_active_credentials()

        if not credentials:
            raise ValueError("No active environment configured")

        # Profile-based authentication
        if 'profile' in credentials:
            logger.info(f"Connecting to SQL warehouse using profile: {credentials['profile']}")
            try:
                # Get token directly from Databricks CLI (fast and reliable)
                access_token = get_token_from_cli(credentials['profile'])
                
            except TimeoutError as e:
                logger.error(f"Authentication timed out for profile: {credentials['profile']}")
                raise ValueError(
                    f"Authentication timed out for profile '{credentials['profile']}'. "
                    f"This usually means the token has expired or authentication is configured for interactive mode.\n"
                    f"Please run: databricks auth login --profile {credentials['profile']}"
                )
            except Exception as e:
                logger.error(f"Failed to get token from CLI: {e}")
                raise ValueError(
                    f"Failed to authenticate using profile '{credentials['profile']}'. "
                    f"Error: {str(e)}\n"
                    f"Ensure your profile is properly configured in ~/.databrickscfg and "
                    f"run 'databricks auth login --profile {credentials['profile']}' if needed."
                )
            
            return connect(
                server_hostname=credentials['host'],
                http_path=credentials['http_path'],
                access_token=access_token
            )
        
        # Token-based authentication (legacy)
        else:
            logger.info("Connecting to SQL warehouse using token authentication")
            return connect(
                server_hostname=credentials['host'],
                http_path=credentials['http_path'],
                access_token=credentials['token']
            )
    except Exception as e:
        active_env = get_env_manager().get_active_environment_name()
        logger.error(f"Failed to connect to Databricks: {e}")
        raise ValueError(
            f"Error: Failed to connect to Databricks.\n"
            f"Current environment: {active_env}\n"
            f"Details: {str(e)}\n\n"
            f"Please check your credentials or switch to a different environment."
        )


def get_workspace_client() -> WorkspaceClient:
    """Get or initialize WorkspaceClient with active environment credentials.
    
    Supports both token-based and profile-based authentication:
    - Token-based: Explicitly provides host and token
    - Profile-based: Uses profile name, SDK auto-detects auth from ~/.databrickscfg
    """
    global w

    try:
        credentials = get_env_manager().get_active_credentials()

        if not credentials:
            raise ValueError("No active environment configured")

        # Profile-based authentication
        if 'profile' in credentials:
            logger.info(f"Initializing WorkspaceClient using profile: {credentials['profile']}")
            try:
                def init_client():
                    return WorkspaceClient(profile=credentials['profile'])
                
                # Run with timeout to detect hanging authentication
                w = run_with_timeout(init_client, timeout_seconds=3)
            except TimeoutError as e:
                logger.error(f"WorkspaceClient initialization timed out for profile: {credentials['profile']}")
                raise ValueError(
                    f"Authentication timed out for profile '{credentials['profile']}'. "
                    f"Please run: databricks auth login --profile {credentials['profile']}"
                )
        
        # Token-based authentication (legacy)
        else:
            logger.info("Initializing WorkspaceClient using token authentication")
            w = WorkspaceClient(
                host=f"https://{credentials['host']}",
                token=credentials['token']
            )
        
        return w
    except Exception as e:
        active_env = get_env_manager().get_active_environment_name()
        logger.error(f"Failed to initialize WorkspaceClient: {e}")
        raise ValueError(
            f"Error: Failed to initialize Databricks WorkspaceClient.\n"
            f"Current environment: {active_env}\n"
            f"Details: {str(e)}"
        )


# Helper function for Databricks REST API requests
def databricks_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make a request to the Databricks REST API using active environment credentials.
    
    For profile-based authentication, retrieves the token from the SDK's auth provider.
    For token-based authentication, uses the provided token directly.
    """
    try:
        credentials = get_env_manager().get_active_credentials()

        if not credentials:
            raise ValueError("No active environment configured")

        # Get the access token based on authentication method
        if 'profile' in credentials:
            # Profile-based: Get token from Databricks CLI
            logger.info(f"Getting token from profile: {credentials['profile']}")
            try:
                token = get_token_from_cli(credentials['profile'])
            except Exception as e:
                logger.error(f"Failed to get token for API request: {e}")
                raise ValueError(f"Authentication failed for profile '{credentials['profile']}': {e}")
        else:
            # Token-based: Use provided token
            token = credentials['token']

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"https://{credentials['host']}/api/2.0/{endpoint}"

        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()
    except Exception as e:
        active_env = get_env_manager().get_active_environment_name()
        logger.error(f"Databricks API request failed: {e}")
        raise ValueError(
            f"Error: Failed to connect to Databricks API.\n"
            f"Current environment: {active_env}\n"
            f"Details: {str(e)}"
        )


# Helper function to generate cluster configuration
def get_cluster_config(
    cluster_name: str,
    spark_version: str,
    node_type: str,
    min_workers: int,
    max_workers: int,
    user_email: str,
    autotermination_minutes: int = 60,
    use_ml_runtime: bool = True,
    is_single_node: bool = False
) -> Dict[str, Any]:
    """Generate cluster configuration with validation."""
    if not all([cluster_name, spark_version, node_type, user_email]):
        raise ValueError("Missing required configuration parameters")

    return {
        "cluster_name": cluster_name,
        "spark_version": spark_version,
        "node_type_id": node_type,
        "driver_node_type_id": node_type,
        "autotermination_minutes": autotermination_minutes,
        "single_user_name": user_email,
        "data_security_mode": DataSecurityMode.DATA_SECURITY_MODE_AUTO,
        "use_ml_runtime": use_ml_runtime,
        "is_single_node": is_single_node,
        "kind": Kind.CLASSIC_PREVIEW,
        "autoscale": AutoScale(
            min_workers=min_workers,
            max_workers=max_workers
        ),
        "spark_conf": {
            "spark.speculation": "true"
        },
        "custom_tags": {
            "Project": "mcp-databricks-server"
        }
    }


# ============================================================================
# Environment Management Tools (NEW)
# ============================================================================

@mcp.tool()
def mcp_switch_environment(name: str) -> str:
    """
    Switch the active Databricks environment.

    Args:
        name: The name of the environment to switch to

    Returns:
        Success message with environment details
    """
    return switch_environment(name)


@mcp.tool()
def mcp_get_current_environment() -> str:
    """
    Get the currently active Databricks environment.

    Returns:
        Formatted string with current environment details
    """
    return get_current_environment()


# ============================================================================
# Existing MCP Tools (Modified to use environment manager)
# ============================================================================

@mcp.resource("schema://tables")
def get_schema() -> str:
    """Provide the list of tables in the Databricks SQL warehouse as a resource"""
    try:
        conn = get_databricks_connection()
        cursor = conn.cursor()
        tables = cursor.tables().fetchall()

        table_info = []
        for table in tables:
            table_info.append(f"Database: {table.TABLE_CAT}, Schema: {table.TABLE_SCHEM}, Table: {table.TABLE_NAME}")

        conn.close()
        return "\n".join(table_info)
    except Exception as e:
        return f"Error retrieving tables: {str(e)}"


@mcp.tool()
def run_sql_query(sql: str) -> str:
    """Execute SQL queries on Databricks SQL warehouse"""
    try:
        conn = get_databricks_connection()
        cursor = conn.cursor()
        result = cursor.execute(sql)

        if result.description:
            # Get column names
            columns = [col[0] for col in result.description]

            # Format the result as a table
            rows = result.fetchall()
            if not rows:
                conn.close()
                return "Query executed successfully. No results returned."

            # Format as markdown table
            table = "| " + " | ".join(columns) + " |\n"
            table += "| " + " | ".join(["---" for _ in columns]) + " |\n"

            for row in rows:
                table += "| " + " | ".join([str(cell) for cell in row]) + " |\n"

            conn.close()
            return table
        else:
            conn.close()
            return "Query executed successfully. No results returned."
    except Exception as e:
        return f"Error executing query: {str(e)}"


@mcp.tool()
def list_jobs() -> str:
    """List all Databricks jobs"""
    try:
        response = databricks_api_request("jobs/list")

        if not response.get("jobs"):
            return "No jobs found."

        jobs = response.get("jobs", [])

        # Format as markdown table
        table = "| Job ID | Job Name | Created By |\n"
        table += "| ------ | -------- | ---------- |\n"

        for job in jobs:
            job_id = job.get("job_id", "N/A")
            job_name = job.get("settings", {}).get("name", "N/A")
            created_by = job.get("created_by", "N/A")

            table += f"| {job_id} | {job_name} | {created_by} |\n"

        return table
    except Exception as e:
        return f"Error listing jobs: {str(e)}"


@mcp.tool()
def get_job_status(job_id: int) -> str:
    """Get the status of a specific Databricks job"""
    try:
        response = databricks_api_request("jobs/runs/list", data={"job_id": job_id})

        if not response.get("runs"):
            return f"No runs found for job ID {job_id}."

        runs = response.get("runs", [])

        # Format as markdown table
        table = "| Run ID | State | Start Time | End Time | Duration |\n"
        table += "| ------ | ----- | ---------- | -------- | -------- |\n"

        for run in runs:
            run_id = run.get("run_id", "N/A")
            state = run.get("state", {}).get("result_state", "N/A")

            # Convert timestamps to readable format if they exist
            start_time = run.get("start_time", 0)
            end_time = run.get("end_time", 0)

            if start_time and end_time:
                duration = f"{(end_time - start_time) / 1000:.2f}s"
            else:
                duration = "N/A"

            # Format timestamps
            import datetime
            start_time_str = datetime.datetime.fromtimestamp(start_time / 1000).strftime('%Y-%m-%d %H:%M:%S') if start_time else "N/A"
            end_time_str = datetime.datetime.fromtimestamp(end_time / 1000).strftime('%Y-%m-%d %H:%M:%S') if end_time else "N/A"

            table += f"| {run_id} | {state} | {start_time_str} | {end_time_str} | {duration} |\n"

        return table
    except Exception as e:
        return f"Error getting job status: {str(e)}"


@mcp.tool()
def get_job_details(job_id: int) -> str:
    """Get detailed information about a specific Databricks job"""
    try:
        response = databricks_api_request(f"jobs/get?job_id={job_id}", method="GET")

        # Format the job details
        job_name = response.get("settings", {}).get("name", "N/A")
        created_time = response.get("created_time", 0)

        # Convert timestamp to readable format
        import datetime
        created_time_str = datetime.datetime.fromtimestamp(created_time / 1000).strftime('%Y-%m-%d %H:%M:%S') if created_time else "N/A"

        # Get job tasks
        tasks = response.get("settings", {}).get("tasks", [])

        result = f"## Job Details: {job_name}\n\n"
        result += f"- **Job ID:** {job_id}\n"
        result += f"- **Created:** {created_time_str}\n"
        result += f"- **Creator:** {response.get('creator_user_name', 'N/A')}\n\n"

        if tasks:
            result += "### Tasks:\n\n"
            result += "| Task Key | Task Type | Description |\n"
            result += "| -------- | --------- | ----------- |\n"

            for task in tasks:
                task_key = task.get("task_key", "N/A")
                task_type = next(iter([k for k in task.keys() if k.endswith("_task")]), "N/A")
                description = task.get("description", "N/A")

                result += f"| {task_key} | {task_type} | {description} |\n"

        return result
    except Exception as e:
        return f"Error getting job details: {str(e)}"


@mcp.tool()
def create_cluster(
    cluster_name: str,
    spark_version: str,
    node_type: str,
    min_workers: int,
    max_workers: int,
    user_email: str,
    autotermination_minutes: int = 60,
    use_ml_runtime: bool = True,
    is_single_node: bool = False,
    wait_for_completion: bool = False
) -> str:
    """Create a Databricks cluster with the specified configuration"""
    try:
        w = get_workspace_client()

        # Generate cluster configuration
        config = get_cluster_config(
            cluster_name=cluster_name,
            spark_version=spark_version,
            node_type=node_type,
            min_workers=min_workers,
            max_workers=max_workers,
            user_email=user_email,
            autotermination_minutes=autotermination_minutes,
            use_ml_runtime=use_ml_runtime,
            is_single_node=is_single_node
        )

        if wait_for_completion:
            # Create cluster and wait for completion
            response = w.clusters.create_and_wait(**config)
            logger.info(f"Cluster created successfully: {response.cluster_id}")
            return f"Cluster '{cluster_name}' created successfully with ID: {response.cluster_id}"
        else:
            # Create cluster without waiting (non-blocking)
            response = w.clusters.create(**config)
            logger.info(f"Cluster creation initiated: {response.cluster_id}")
            return f"Cluster '{cluster_name}' creation initiated with ID: {response.cluster_id}"

    except Exception as e:
        logger.error(f"Failed to create cluster: {e}")
        return f"Error creating cluster: {str(e)}"


@mcp.tool()
def delete_cluster(cluster_id: str, confirm: bool = False) -> str:
    """Delete a Databricks cluster with confirmation"""
    try:
        w = get_workspace_client()

        if not confirm:
            return "Deletion not confirmed. Set confirm=True to proceed with cluster deletion."

        w.clusters.permanent_delete(cluster_id=cluster_id)
        logger.info(f"Cluster {cluster_id} deleted successfully")
        return f"Cluster {cluster_id} deleted successfully"
    except Exception as e:
        logger.error(f"Failed to delete cluster {cluster_id}: {e}")
        return f"Error deleting cluster {cluster_id}: {str(e)}"


@mcp.tool()
def list_clusters() -> str:
    """List all Databricks clusters"""
    try:
        w = get_workspace_client()
        clusters = w.clusters.list()

        if not clusters:
            return "No clusters found."

        # Format as markdown table
        table = "| Cluster ID | Cluster Name | State | Spark Version | Node Type | Workers |\n"
        table += "| ---------- | ------------ | ----- | ------------- | --------- | ------- |\n"

        for cluster in clusters:
            cluster_id = cluster.cluster_id or "N/A"
            cluster_name = cluster.cluster_name or "N/A"
            state = cluster.state.value if cluster.state else "N/A"
            spark_version = cluster.spark_version or "N/A"
            node_type = cluster.node_type_id or "N/A"
            workers = f"{cluster.num_workers}" if cluster.num_workers else "N/A"

            table += f"| {cluster_id} | {cluster_name} | {state} | {spark_version} | {node_type} | {workers} |\n"

        return table
    except Exception as e:
        logger.error(f"Failed to list clusters: {e}")
        return f"Error listing clusters: {str(e)}"


@mcp.tool()
def get_cluster_status(cluster_id: str) -> str:
    """Get the status and details of a specific Databricks cluster"""
    try:
        w = get_workspace_client()
        cluster = w.clusters.get(cluster_id)

        result = f"## Cluster Details: {cluster.cluster_name}\n\n"
        result += f"- **Cluster ID:** {cluster.cluster_id}\n"
        result += f"- **State:** {cluster.state.value if cluster.state else 'N/A'}\n"
        result += f"- **Spark Version:** {cluster.spark_version or 'N/A'}\n"
        result += f"- **Node Type:** {cluster.node_type_id or 'N/A'}\n"
        result += f"- **Driver Node Type:** {cluster.driver_node_type_id or 'N/A'}\n"
        result += f"- **Workers:** {cluster.num_workers or 'N/A'}\n"
        result += f"- **Auto-termination:** {cluster.autotermination_minutes or 'N/A'} minutes\n"
        result += f"- **Single User:** {cluster.single_user_name or 'N/A'}\n"
        result += f"- **Created:** {cluster.start_time or 'N/A'}\n"

        if cluster.autoscale:
            result += f"- **Auto-scaling:** Min: {cluster.autoscale.min_workers}, Max: {cluster.autoscale.max_workers}\n"

        return result
    except Exception as e:
        logger.error(f"Failed to get cluster status: {e}")
        return f"Error getting cluster status: {str(e)}"


if __name__ == "__main__":
    try:
        logger.info("Starting MCP server...")
        mcp.run()
    except Exception as e:
        logger.error(f"Fatal error starting MCP server: {e}", exc_info=True)
        sys.exit(1)