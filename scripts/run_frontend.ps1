# PowerShell script to run frontend application

$RootDir = Split-Path -Path $PSScriptRoot -Parent
$VenvPython = Join-Path -Path $RootDir -ChildPath ".venv\Scripts\python.exe"

if (-not (Test-Path -Path $VenvPython)) {
    Write-Error "No se encontro el entorno virtual. Por favor corre primero: scripts\setup.ps1"
    exit 1
}

Write-Host "Iniciando la Aplicacion Frontend Flet..." -ForegroundColor Green
& $VenvPython (Join-Path -Path $RootDir -ChildPath "frontend\main.py")
