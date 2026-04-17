#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/Scripts/python.exe"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "No se encontro $VENV_PYTHON. Ejecuta primero: bash scripts/setup.sh"
  exit 1
fi

cd "$ROOT_DIR"
"$VENV_PYTHON" frontend/main.py
