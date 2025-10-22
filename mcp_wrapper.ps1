# MCP Databricks Server Wrapper (PowerShell)
# Logs errors to $env:TEMP\mcp-databricks-error.log

$ErrorActionPreference = "Continue"
$logFile = Join-Path $env:TEMP "mcp-databricks-error.log"

# Log startup with timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"=== MCP Server Starting at $timestamp ===" | Out-File -Append -FilePath $logFile

try {
    # Change to script directory
    $scriptDir = $PSScriptRoot
    Set-Location $scriptDir
    "Working directory: $scriptDir" | Out-File -Append -FilePath $logFile
    
    # Validate .venv exists
    $pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        "ERROR: Python virtual environment not found at $pythonExe" | Out-File -Append -FilePath $logFile
        exit 1
    }
    
    # Validate main.py exists
    $mainPy = Join-Path $scriptDir "main.py"
    if (-not (Test-Path $mainPy)) {
        "ERROR: main.py not found at $mainPy" | Out-File -Append -FilePath $logFile
        exit 1
    }
    
    # Start Python server with stderr redirected to log
    "Starting Python server..." | Out-File -Append -FilePath $logFile
    & $pythonExe $mainPy 2>> $logFile
}
catch {
    $errorMsg = $_.Exception.Message
    "ERROR: $errorMsg" | Out-File -Append -FilePath $logFile
    exit 1
}

