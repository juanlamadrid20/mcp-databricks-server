@echo off
REM MCP Databricks Server Wrapper (Windows Batch)
REM Logs errors to %TEMP%\mcp-databricks-error.log

echo === MCP Server Starting at %date% %time% === >> %TEMP%\mcp-databricks-error.log 2>&1

REM Change to script directory
cd /d "%~dp0"
echo Working directory: %CD%\ >> %TEMP%\mcp-databricks-error.log 2>&1

REM Validate .venv exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found at .venv\Scripts\python.exe >> %TEMP%\mcp-databricks-error.log 2>&1
    exit /b 1
)

REM Validate main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found >> %TEMP%\mcp-databricks-error.log 2>&1
    exit /b 1
)

REM Start Python server with stderr redirected to log
echo Starting Python server... >> %TEMP%\mcp-databricks-error.log 2>&1
.venv\Scripts\python.exe main.py 2>> %TEMP%\mcp-databricks-error.log

