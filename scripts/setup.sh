#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/Scripts/python.exe"

if [ -n "${PYTHON_BIN:-}" ]; then
  PYTHON_CMD=("$PYTHON_BIN")
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=(python)
elif command -v py >/dev/null 2>&1; then
  PYTHON_CMD=(py -3)
else
  echo "No se encontro Python en PATH. Instala Python 3.12+ o define PYTHON_BIN."
  exit 1
fi

echo "==> Creando entorno virtual..."
"${PYTHON_CMD[@]}" -m venv "$ROOT_DIR/.venv"

echo "==> Instalando dependencias..."
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r "$ROOT_DIR/requirements.txt"

if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "==> Creando archivo .env desde .env.example..."
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
else
  echo "==> Archivo .env ya existe, se conserva."
fi

echo "==> Ejecutando migraciones..."
cd "$ROOT_DIR/backend"
"$VENV_PYTHON" manage.py migrate

echo
echo "Listo. Siguientes pasos:"
echo "1. bash scripts/create_superuser.sh"
echo "2. bash scripts/run_backend.sh"
echo "3. En otra terminal: bash scripts/run_frontend.sh"
