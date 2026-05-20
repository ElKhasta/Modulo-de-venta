# Manual de instalacion

## 1. Requisitos previos

- Git
- Python 3.12 recomendado
- `pip` actualizado
- Git Bash para Windows recomendado
- Alternativamente PowerShell, CMD o terminal equivalente

## 2. Clonar el repositorio

```bash
git clone https://github.com/ElKhasta/Modulo-de-venta.git
cd Modulo-de-venta
```

Si esta version se publica en una rama distinta a `main`, cambia a esa rama antes de instalar.

### Ejemplo para esta entrega publicada en `frontendThor`

```bash
git checkout frontendThor
```

## 3. Instalacion rapida con Git Bash

Desde Git Bash, la forma mas simple y repetible es usar los scripts incluidos:

```bash
bash scripts/setup.sh
```

Ese script hace lo siguiente:

- Crea `.venv`
- Instala dependencias
- Genera `.env` a partir de `.env.example` si no existe
- Ejecuta migraciones

## 4. Configurar variables de entorno

Despues de `bash scripts/setup.sh`, el archivo `.env` ya debe existir.

Si necesitas recrearlo manualmente en Git Bash:

```bash
cp .env.example .env
```

Luego ajusta las variables si lo necesitas.

### Configuracion minima para desarrollo local

```env
DJANGO_DEBUG=True
DB_ENGINE=sqlite
DB_NAME=db.sqlite3
API_BASE_URL=http://127.0.0.1:8000/api
```

### Si quieres usar PostgreSQL

```env
DB_ENGINE=postgresql
DB_NAME=modulo_venta
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

## 5. Crear superusuario

```bash
bash scripts/create_superuser.sh
```

## 6. Iniciar backend

```bash
bash scripts/run_backend.sh
```

El backend quedara en:

- [http://127.0.0.1:8000](http://127.0.0.1:8000)
- [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

## 7. Iniciar frontend

En otra terminal Git Bash, desde la raiz del proyecto:

```bash
bash scripts/run_frontend.sh
```

## 8. Probar login

Usa el superusuario creado con Django.

- Usuario: el que definiste con `createsuperuser`
- Contrasena: la que definiste al crear ese usuario

## 9. Probar endpoints desde Git Bash

### Login JWT

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"tu_password"}'
```

### Listar productos con token

```bash
TOKEN="PEGA_AQUI_EL_ACCESS_TOKEN"
curl http://127.0.0.1:8000/api/productos/ \
  -H "Authorization: Bearer $TOKEN"
```

## 10. Flujo recomendado de uso

1. Inicia sesion en el frontend.
2. Registra productos.
3. Registra clientes.
4. Crea ventas desde el modulo de ventas.
5. Consulta el dashboard para validar metricas y stock.

## 11. Alternativa manual en Git Bash

Si prefieres no usar scripts, tambien puedes hacerlo paso a paso:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

En otra terminal:

```bash
cd /c/Users/ernes/Modulo-de-venta
source .venv/Scripts/activate
python frontend/main.py
```

## 12. Errores comunes y solucion

### `python` no se reconoce

- Verifica que Python este instalado y agregado al PATH.
- En Windows, puedes reinstalar Python marcando la opcion `Add Python to PATH`.
- Si usas Git Bash y `python` no aparece, prueba `py -3.12` o reinstala Python habilitando PATH.

### `No module named django`

- Asegurate de activar el entorno virtual antes de instalar dependencias.
- Reinstala con `pip install -r requirements.txt`.
- Si usaste scripts, confirma que exista `C:/ruta/al/proyecto/.venv/Scripts/python.exe`.

### `Secret key` o `.env` faltante

- Verifica que exista `.env` en la raiz del proyecto.
- Si no existe, copia `.env.example` y ajusta valores.

### Error al conectar el frontend con la API

- Confirma que el backend este ejecutandose en `http://127.0.0.1:8000`.
- Revisa `API_BASE_URL` en `.env`.
- Si cambiaste el puerto del backend, actualiza `API_BASE_URL` y reinicia el frontend.

### Error de base de datos PostgreSQL

- Confirma que el servicio de PostgreSQL este activo.
- Revisa host, puerto, usuario y password en `.env`.

### Login invalido

- Verifica que el usuario exista en Django.
- Si no existe, crea uno con `python manage.py createsuperuser`.

## 13. Recomendaciones para otros desarrolladores

- Mantener el backend y frontend desacoplados por API.
- No volver a concentrar la UI en un solo archivo.
- Crear pruebas nuevas cada vez que se cambie la logica de ventas.
- Usar `.env.example` como contrato de configuracion compartido.
- Mantener los scripts de `scripts/` actualizados para que la instalacion desde Git Bash siga siendo reproducible.
