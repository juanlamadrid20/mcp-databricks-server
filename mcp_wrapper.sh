#!/bin/bash

cd /Users/juan.lamadrid/dev/databricks-projects/mcp/mcp-databricks-server

# Redirect all stderr to log file
exec 2>> /tmp/mcp-databricks-error.log

# Log startup
echo "=== MCP Server Starting at $(date) ===" >&2

# Run the Python server - stdout goes to Claude, stderr goes to log
exec /Users/juan.lamadrid/dev/databricks-projects/mcp/mcp-databricks-server/.venv/bin/python main.py