# PowerShell script to create Django superuser

$RootDir = Split-Path -Path $PSScriptRoot -Parent
$VenvPython = Join-Path -Path $RootDir -ChildPath ".venv\Scripts\python.exe"

if (-not (Test-Path -Path $VenvPython)) {
    Write-Error "No se encontro el entorno virtual. Por favor corre primero: scripts\setup.ps1"
    exit 1
}

$BackendDir = Join-Path -Path $RootDir -ChildPath "backend"
Set-Location -Path $BackendDir
& $VenvPython manage.py createsuperuser
Set-Location -Path $RootDir
