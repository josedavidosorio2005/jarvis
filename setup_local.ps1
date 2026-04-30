$ErrorActionPreference = "Stop"

Write-Host "=== Instalacion local completa de Jarvis ===" -ForegroundColor Cyan

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creando entorno Python e instalando dependencias..." -ForegroundColor Cyan
    & .\install.ps1
} else {
    Write-Host "Actualizando dependencias Python..." -ForegroundColor Cyan
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

Write-Host "Preparando Ollama y modelo local..." -ForegroundColor Cyan
& .\setup_ollama.ps1

Write-Host "Verificando Jarvis..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe .\verify_functions.py

Write-Host ""
Write-Host "Listo. Ejecuta Jarvis con:" -ForegroundColor Green
Write-Host "  .\run.ps1"
Write-Host ""
Write-Host "Modo voz:" -ForegroundColor Green
Write-Host "  .\run.ps1 --voice"
