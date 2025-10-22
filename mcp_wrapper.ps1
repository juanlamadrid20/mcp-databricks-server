# PowerShell wrapper for MCP Databricks Server on Windows

# Change to the script's directory
Set-Location -Path $PSScriptRoot

# Define log file path
$logFile = "$env:TEMP\mcp-databricks-error.log"

# Log startup with timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"=== MCP Server Starting at $timestamp ===" | Out-File -FilePath $logFile -Append

# Run the Python server
# Stdout goes to Claude (via standard output)
# Stderr is redirected to log file
$pythonPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$mainScript = Join-Path $PSScriptRoot "main.py"

try {
    & $pythonPath $mainScript 2>> $logFile
} catch {
    $errorMsg = "Error running MCP server: $_"
    $errorMsg | Out-File -FilePath $logFile -Append
    Write-Error $errorMsg
    exit 1
}

