$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "No existe .venv. Ejecutando install.ps1..." -ForegroundColor Yellow
    & (Join-Path $root "install.ps1")
}

Write-Host "Verificando proyecto..." -ForegroundColor Cyan
& $python (Join-Path $root "verify_functions.py")

Write-Host "Construyendo Jarvis.exe con PyInstaller..." -ForegroundColor Cyan
& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --name "Jarvis" `
    --hidden-import "speech_recognition" `
    --hidden-import "voice_listener_py" `
    --add-data "$root\config.example.json;." `
    --add-data "$root\plugins;plugins" `
    --add-data "$root\voice_listener_py.py;." `
    "$root\jarvis_master.py"

$dist = Join-Path $root "dist\Jarvis"
$package = Join-Path $root "Jarvis_Portable"
if (Test-Path $package) {
    Remove-Item $package -Recurse -Force
}
New-Item -ItemType Directory -Path $package | Out-Null
Copy-Item "$dist\*" $package -Recurse -Force
Copy-Item (Join-Path $root "README.md") $package -Force
Copy-Item (Join-Path $root "config.example.json") $package -Force

Write-Host ""
Write-Host "Paquete listo en: $package" -ForegroundColor Green
Write-Host "Ejecutable: $(Join-Path $package 'Jarvis.exe')" -ForegroundColor Green
