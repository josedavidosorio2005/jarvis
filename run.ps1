$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "No existe .venv. Ejecutando instalacion primero..." -ForegroundColor Yellow
    & .\install.ps1
}

& .\.venv\Scripts\python.exe .\jarvis.py @args
