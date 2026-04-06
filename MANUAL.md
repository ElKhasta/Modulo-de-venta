# 📘 Manual de uso - Módulo de Venta

Este documento explica cómo instalar y usar el sistema paso a paso.

---

## 🧩 1. Descargar el proyecto

```bash
git clone https://github.com/ElKhasta/Modulo-de-venta.git
cd Modulo-de-venta/backend

## 2.  Forma rápida
bash setup.sh

## 3.Abrir sistema
http://127.0.0.1:8000/admin/

## 4. Iniciar sesión
Usuario:
admin

Contraseña:
admin12345

##5. Forma manual (alternativa)
python -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt

cp .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
