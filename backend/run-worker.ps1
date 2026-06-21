$ErrorActionPreference = "Stop"
$BackendRoot = $PSScriptRoot
$VenvPython = Join-Path $BackendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtualenv tidak dijumpai. Jalankan: python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
}

Set-Location $BackendRoot
& $VenvPython -m app.worker @args
