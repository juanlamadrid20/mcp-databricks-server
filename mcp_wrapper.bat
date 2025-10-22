@echo off
REM Batch wrapper for MCP Databricks Server on Windows

REM Define log file path
set LOG_FILE=%TEMP%\mcp-databricks-error.log

REM Log startup with timestamp
echo === MCP Server Starting at %date% %time% === >> "%LOG_FILE%" 2>&1
echo Working directory: %~dp0 >> "%LOG_FILE%" 2>&1

REM Change to the script's directory
cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Failed to change to directory %~dp0 >> "%LOG_FILE%" 2>&1
    exit /b 1
)

REM Check if python.exe exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Python executable not found at .venv\Scripts\python.exe >> "%LOG_FILE%" 2>&1
    echo Current directory: %CD% >> "%LOG_FILE%" 2>&1
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found in %CD% >> "%LOG_FILE%" 2>&1
    exit /b 1
)

REM Run the Python server
REM Stdout goes to Claude (via standard output)
REM Stderr is redirected to log file
echo Starting Python server... >> "%LOG_FILE%" 2>&1
".venv\Scripts\python.exe" "main.py" 2>> "%LOG_FILE%"

