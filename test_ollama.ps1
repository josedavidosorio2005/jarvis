$ErrorActionPreference = "Stop"

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Ollama no esta instalado o no esta en PATH." -ForegroundColor Red
    exit 1
}

$response = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:11434/api/chat" `
    -ContentType "application/json" `
    -Body (@{
        model = "deepseek-r1:8b"
        stream = $false
        messages = @(
            @{ role = "user"; content = "Responde solo: ollama funcionando" }
        )
    } | ConvertTo-Json -Depth 5)

$response.message.content
