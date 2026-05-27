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

## 🚀 Inicio Rápido en Windows (Recomendado)

El proyecto incluye un iniciador unificado inteligente que arranca el backend de Django, el túnel seguro de Cloudflare (HTTPS para la cámara del celular) y el cliente web de Flet con **un solo comando**.

1. **Configurar el Cortafuegos (Solo la primera vez)**:
   Haz clic derecho sobre [abrir_puertos_firewall.bat](file:///C:/Users/ernes/.gemini/antigravity/scratch/Modulo-de-venta/abrir_puertos_firewall.bat) y selecciona **"Ejecutar como Administrador"**. Esto habilitará las conexiones locales desde tu celular.

2. **Iniciar todo el Sistema**:
   Abre una terminal en la raíz del proyecto y ejecuta:
   ```powershell
   python iniciar.py
   ```
   *Nota: La primera vez descargará `cloudflared.exe` (~30 MB) automáticamente.*

3. **Acceder a la Aplicación**:
   - **Escritorio (POS)**: Abre en tu navegador `http://localhost:8080` (o la dirección IP local que se imprima en pantalla).
   - **Celular (Escáner de Cámara)**: Escanea el código QR que se muestra en el menú *"Vincular Celular"* dentro de la sección de **Productos**, o ingresa a la URL segura `https://xxx.trycloudflare.com/api/scanner/` generada por el túnel.

---

La guía detallada de instalación manual está disponible en [docs/INSTALL.md](file:///C:/Users/ernes/.gemini/antigravity/scratch/Modulo-de-venta/docs/INSTALL.md).

