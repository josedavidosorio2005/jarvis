$ErrorActionPreference = "Stop"

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Ollama no esta instalado o no esta en PATH." -ForegroundColor Yellow
    Write-Host "Instalalo desde: https://ollama.com/download/windows"
    Write-Host "Luego cierra y abre PowerShell, y ejecuta este script otra vez."
    exit 1
}

Write-Host "Descargando modelo DeepSeek para Ollama..." -ForegroundColor Cyan
ollama pull deepseek-r1:8b

Write-Host ""
Write-Host "Listo. Jarvis usara Ollama si OpenAI falla por limite, cuota o API key." -ForegroundColor Green
