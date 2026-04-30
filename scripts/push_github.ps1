$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

git status --short
$changes = git status --porcelain
if (-not $changes) {
    Write-Host "No hay cambios pendientes." -ForegroundColor Green
    exit 0
}

git add README.md requirements.txt install.ps1 setup_local.ps1 setup_ollama.ps1 run.ps1 jarvis.py gui.py jarvis_master.py verify_functions.py plugins scripts tests .github config.example.json
git commit -m "Profesionalizar Jarvis runtime, seguridad y empaquetado"
git push origin main
