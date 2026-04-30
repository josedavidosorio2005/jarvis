$ErrorActionPreference = "Stop"

Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
py -m venv .venv

Write-Host "Instalando dependencias..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Listo. Ejecuta .\run.ps1 para iniciar Jarvis." -ForegroundColor Green
