# PowerShell Setup Script for Modulo de Venta
# This script sets up the Python virtual environment, installs dependencies, and runs migrations.

$ErrorActionPreference = "Stop"

# Get root directory of the project
$RootDir = Split-Path -Path $PSScriptRoot -Parent
$VenvDir = Join-Path -Path $RootDir -ChildPath ".venv"
$VenvPython = Join-Path -Path $VenvDir -ChildPath "Scripts\python.exe"

Write-Host "==> Verificando instalacion de Python..." -ForegroundColor Cyan
if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} else {
    Write-Error "No se encontro Python en el PATH. Por favor instala Python 3.10+ y asegurate de marcar 'Add Python to PATH'."
    exit 1
}

Write-Host "==> Creando entorno virtual en $VenvDir..." -ForegroundColor Cyan
if (-not (Test-Path -Path $VenvDir)) {
    Start-Process -FilePath $PythonCmd -ArgumentList "-m venv $VenvDir" -NoNewWindow -Wait
} else {
    Write-Host "El entorno virtual ya existe." -ForegroundColor Yellow
}

Write-Host "==> Instalando/actualizando dependencias..." -ForegroundColor Cyan
Start-Process -FilePath $VenvPython -ArgumentList "-m pip install --upgrade pip" -NoNewWindow -Wait
Start-Process -FilePath $VenvPython -ArgumentList "-m pip install -r `"$RootDir\requirements.txt`"" -NoNewWindow -Wait

$EnvFile = Join-Path -Path $RootDir -ChildPath ".env"
$EnvExampleFile = Join-Path -Path $RootDir -ChildPath ".env.example"

if (-not (Test-Path -Path $EnvFile)) {
    Write-Host "==> Creando archivo .env desde .env.example..." -ForegroundColor Cyan
    Copy-Item -Path $EnvExampleFile -Destination $EnvFile
} else {
    Write-Host "==> El archivo .env ya existe, se conserva." -ForegroundColor Yellow
}

Write-Host "==> Ejecutando migraciones de la base de datos..." -ForegroundColor Cyan
$BackendDir = Join-Path -Path $RootDir -ChildPath "backend"
Set-Location -Path $BackendDir
Start-Process -FilePath $VenvPython -ArgumentList "manage.py migrate" -NoNewWindow -Wait
Set-Location -Path $RootDir

Write-Host ""
Write-Host "¡Todo listo! Siguientes pasos:" -ForegroundColor Green
Write-Host "1. Ejecuta scripts\create_superuser.ps1 (para crear un usuario administrador)" -ForegroundColor Yellow
Write-Host "2. Ejecuta scripts\run_backend.ps1 (inicia el servidor local de Django)" -ForegroundColor Yellow
Write-Host "3. En otra terminal, ejecuta scripts\run_frontend.ps1 (inicia la app Flet)" -ForegroundColor Yellow
