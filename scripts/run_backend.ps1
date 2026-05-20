# PowerShell script to run backend server

$RootDir = Split-Path -Path $PSScriptRoot -Parent
$VenvPython = Join-Path -Path $RootDir -ChildPath ".venv\Scripts\python.exe"

if (-not (Test-Path -Path $VenvPython)) {
    Write-Error "No se encontro el entorno virtual. Por favor corre primero: scripts\setup.ps1"
    exit 1
}

$BackendDir = Join-Path -Path $RootDir -ChildPath "backend"
Set-Location -Path $BackendDir
Write-Host "Iniciando el Servidor Backend Django en http://127.0.0.1:8000 ..." -ForegroundColor Green
& $VenvPython manage.py runserver
Set-Location -Path $RootDir
