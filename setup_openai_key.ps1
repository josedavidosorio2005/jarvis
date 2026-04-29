param(
    [Parameter(Mandatory = $true)]
    [string]$ApiKey
)

$ErrorActionPreference = "Stop"
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $ApiKey, "User")
Write-Host "OPENAI_API_KEY guardada para tu usuario de Windows. Cierra y abre PowerShell para usarla." -ForegroundColor Green
