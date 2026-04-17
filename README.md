# Modulo de Venta

Sistema POS construido con Django REST Framework y Flet, orientado a ventas, clientes, productos y registro de operaciones en una sola aplicacion.

## Que incluye

- Backend Django con API REST protegida por JWT
- Frontend Flet con login, dashboard y modulos de productos, clientes y ventas
- Persistencia real en base de datos
- Estructura modular para mantenimiento y despliegue
- Configuracion por `.env`

## Estructura principal

```text
Modulo-de-venta/
|-- backend/
|   |-- api/
|   |-- core/
|   `-- manage.py
|-- frontend/
|   |-- app/
|   `-- main.py
|-- scripts/
|   |-- setup.sh
|   |-- create_superuser.sh
|   |-- run_backend.sh
|   `-- run_frontend.sh
|-- docs/
|   `-- INSTALL.md
|-- .env.example
`-- requirements.txt
```

## Endpoints principales

- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`
- `GET /api/dashboard/summary/`
- `GET|POST|PUT|DELETE /api/productos/`
- `GET|POST|PUT|DELETE /api/clientes/`
- `GET|POST|PUT|DELETE /api/ventas/`

## Inicio rapido desde Git Bash

1. Clona el repositorio.
2. Cambiate a la rama donde este publicada esta version.
3. Ejecuta `bash scripts/setup.sh`.
4. Crea un superusuario con `bash scripts/create_superuser.sh`.
5. Inicia backend con `bash scripts/run_backend.sh`.
6. En otra terminal Git Bash, inicia frontend con `bash scripts/run_frontend.sh`.

La guia completa esta en `docs/INSTALL.md`.
