# Fix Databricks authentication for MCP server
# This script will help you re-authenticate with Databricks

Write-Host "=" * 70
Write-Host "Databricks Authentication Fix"
Write-Host "=" * 70

# Check if databricks CLI is installed
Write-Host "`nChecking Databricks CLI installation..."
try {
    $version = databricks --version 2>&1
    Write-Host "✅ Databricks CLI is installed: $version"
} catch {
    Write-Host "❌ Databricks CLI is not installed or not in PATH"
    Write-Host "Please install it: pip install databricks-cli"
    exit 1
}

# Re-authenticate with the profile
Write-Host "`nRe-authenticating with profile: anfdev"
Write-Host "This will open a browser window for authentication..."
Write-Host ""

databricks auth login --profile anfdev --host https://adb-7680471123400497.17.azuredatabricks.net

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Authentication successful!"
    Write-Host "You can now restart your MCP server and try again."
} else {
    Write-Host "`n❌ Authentication failed. Please check your credentials."
    exit 1
}

