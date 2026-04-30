$ErrorActionPreference = "Stop"

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    $knownPath = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path $knownPath) {
        $env:PATH = (Split-Path $knownPath) + ";" + $env:PATH
        $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    }
}

if (-not $ollama) {
    Write-Host "Ollama no esta instalado. Intentando instalar con winget..." -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "No encontre winget. Instala Ollama desde https://ollama.com/download/windows y ejecuta este script otra vez." -ForegroundColor Red
        exit 1
    }
    winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
    $knownPath = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path $knownPath) {
        $env:PATH = (Split-Path $knownPath) + ";" + $env:PATH
    }
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollama) {
        Write-Host "Ollama se instalo, pero no quedo disponible en PATH. Cierra y abre PowerShell." -ForegroundColor Red
        exit 1
    }
}

$configPath = Join-Path $PSScriptRoot "config.json"
$model = "llama3.2:3b"
$fastModel = "qwen2.5:0.5b"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    if ($config.ollama_model) {
        $model = [string]$config.ollama_model
    }
    if ($config.ollama_fast_model) {
        $fastModel = [string]$config.ollama_fast_model
    }
}

try {
    Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null
} catch {
    Write-Host "Arrancando servidor Ollama..." -ForegroundColor Cyan
    Start-Process -FilePath $ollama.Source -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

Write-Host "Descargando modelo local de Ollama: $model" -ForegroundColor Cyan
ollama pull $model
if ($fastModel -and $fastModel -ne $model) {
    Write-Host "Descargando modelo rapido de Ollama: $fastModel" -ForegroundColor Cyan
    ollama pull $fastModel
}

Write-Host "Probando modelo local..." -ForegroundColor Cyan
$body = @{
    model = $model
    messages = @(@{ role = "user"; content = "Responde solo: ok" })
    stream = $false
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 120 | Out-Null

Write-Host ""
Write-Host "Listo. Jarvis ya puede usar Ollama local con $model." -ForegroundColor Green
