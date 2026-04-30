$ErrorActionPreference = "Stop"

function Resolve-Python {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($version in @("-3.12", "-3.11", "-3")) {
            try {
                $check = & py $version --version 2>&1
                if ($LASTEXITCODE -eq 0) {
                    return ,@("py", $version)
                }
            } catch {
                continue
            }
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        try {
            $version = & $python.Source --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $version -notmatch "Microsoft Store") {
                return ,@($python.Source)
            }
        } catch {
            # Ignore Microsoft Store aliases and broken Python shims.
        }
    }

    $uvPython = Join-Path $env:APPDATA "uv\python"
    if (Test-Path $uvPython) {
        $candidate = Get-ChildItem $uvPython -Recurse -Filter python.exe -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($candidate) {
            return ,@($candidate.FullName)
        }
    }

    throw "No encontre Python utilizable. Instala Python 3.11+ desde python.org o ejecuta: winget install Python.Python.3.12"
}

$pythonCmd = Resolve-Python

Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
$pythonExe = $pythonCmd[0]
$pythonArgs = @()
if ($pythonCmd.Length -gt 1) {
    $pythonArgs = $pythonCmd[1..($pythonCmd.Length - 1)]
}
& $pythonExe @pythonArgs -m venv .venv

Write-Host "Instalando dependencias..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path ".\config.json") -and (Test-Path ".\config.example.json")) {
    Copy-Item ".\config.example.json" ".\config.json"
    Write-Host "config.json creado desde config.example.json" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Listo. Ejecuta .\run.ps1 para iniciar Jarvis." -ForegroundColor Green
