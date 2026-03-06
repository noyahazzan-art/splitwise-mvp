# Splitwise MVP — Start server
# Port 8001 (Agent uses 8080)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Activate venv if exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    .\.venv\Scripts\Activate.ps1
}

Write-Host "=== Splitwise MVP ===" -ForegroundColor Cyan
Write-Host "API: http://localhost:8001"
Write-Host "Docs: http://localhost:8001/docs"
Write-Host ""

uvicorn app.main:app --reload --port 8001
