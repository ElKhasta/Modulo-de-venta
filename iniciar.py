# -*- coding: utf-8 -*-
"""
Vantti POS - Lanzador Unificado con Tunel HTTPS
================================================
Inicia Django + Cloudflare Tunnel + Flet en un solo comando.
El tunel de Cloudflare proporciona una URL https:// de confianza real,
sin certificados autofirmados ni advertencias en el navegador.

Uso:
    python iniciar.py

Los tres servidores se detienen al presionar Ctrl+C.
"""

import os
import sys
import time
import json
import signal
import socket
import subprocess
import threading
import urllib.request
import urllib.error
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TUNNEL_URL_FILE = BASE_DIR / ".tunnel_url"
CLOUDFLARED_EXE = BASE_DIR / "cloudflared.exe"
DJANGO_PORT = 8000
FLET_PORT = 8080
DJANGO_MANAGE = BASE_DIR / "backend" / "manage.py"
FLET_MAIN = BASE_DIR / "frontend" / "main.py"
VENV_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"
VENV_FLET = BASE_DIR / ".venv" / "Scripts" / "flet.exe"

# ─── Descarga cloudflared si no esta presente ─────────────────────────────────

CLOUDFLARED_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-windows-amd64.exe"
)

def download_cloudflared():
    if CLOUDFLARED_EXE.exists():
        return True
    print("[Tunel] Descargando cloudflared.exe (primera vez, ~30 MB)...")
    print("[Tunel] Por favor espera...")
    try:
        req = urllib.request.Request(
            CLOUDFLARED_URL,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=120) as r, \
             open(CLOUDFLARED_EXE, "wb") as f:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r[Tunel] Descargando... {pct}%", end="", flush=True)
        print("\n[Tunel] cloudflared.exe descargado correctamente.")
        return True
    except Exception as e:
        print("\n[Tunel] ERROR al descargar cloudflared: " + str(e))
        print("[Tunel] Sin tunel HTTPS, la camara no funcionara en celulares.")
        return False

# ─── Arrancar Django ──────────────────────────────────────────────────────────

def start_django():
    print("[Django] Iniciando servidor en puerto " + str(DJANGO_PORT) + "...")
    proc = subprocess.Popen(
        [str(VENV_PYTHON), str(DJANGO_MANAGE), "runserver", "0.0.0.0:" + str(DJANGO_PORT)],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # Esperar hasta que Django este listo
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            print("[Django] " + line)
        if "Starting development server" in line or "Quit the server" in line:
            break
    # Leer el resto en segundo plano
    threading.Thread(target=_drain, args=(proc.stdout, "[Django] "), daemon=True).start()
    return proc

# ─── Arrancar Cloudflare Tunnel ───────────────────────────────────────────────

def start_tunnel():
    """
    Inicia cloudflared quick tunnel apuntando a Django (puerto 8000).
    Lee la URL del tunnel de la salida de cloudflared y la escribe en .tunnel_url.
    Retorna (proceso, url_del_tunnel).
    """
    if not CLOUDFLARED_EXE.exists():
        return None, None

    print("[Tunel] Iniciando tunel HTTPS (Cloudflare)...")
    log_file = BASE_DIR / "cloudflared.log"
    if log_file.exists():
        try:
            log_file.unlink(missing_ok=True)
        except Exception:
            pass

    proc = subprocess.Popen(
        [str(CLOUDFLARED_EXE), "tunnel", "--url", f"http://127.0.0.1:{DJANGO_PORT}", "--logfile", str(log_file)],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    tunnel_url = None
    deadline = time.time() + 25  # max 25 segundos para obtener la URL

    while time.time() < deadline:
        if proc.poll() is not None:
            print("[Tunel] ERROR: cloudflared.exe termino inesperadamente.")
            break
        if log_file.exists():
            try:
                content = log_file.read_text(encoding="utf-8", errors="ignore")
                match = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", content)
                if match:
                    tunnel_url = match.group(0)
                    print("[Tunel] URL obtenida: " + tunnel_url)
                    break
            except Exception:
                pass
        time.sleep(0.5)

    if tunnel_url:
        TUNNEL_URL_FILE.write_text(tunnel_url, encoding="utf-8")
        print("[Tunel] URL guardada en .tunnel_url")
    else:
        print("[Tunel] Tiempo de espera agotado o error al obtener la URL.")
        TUNNEL_URL_FILE.write_text("", encoding="utf-8")

    # Iniciar un hilo para ir mostrando el log de cloudflared de forma limpia
    def tail_log():
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, 2)
                while proc.poll() is None:
                    line = f.readline()
                    if line:
                        print("[Tunel] " + line.rstrip())
                    else:
                        time.sleep(0.5)
        except Exception:
            pass

    threading.Thread(target=tail_log, daemon=True).start()
    return proc, tunnel_url

# ─── Arrancar Flet ────────────────────────────────────────────────────────────

def start_flet(tunnel_url):
    print("[Flet] Iniciando interfaz web en puerto " + str(FLET_PORT) + "...")
    if tunnel_url:
        print("[Flet] Escaner movil: " + tunnel_url + "/api/scanner/")

    env = os.environ.copy()
    if tunnel_url:
        env["VANTTI_TUNNEL_URL"] = tunnel_url

    proc = subprocess.Popen(
        [str(VENV_FLET), "run", str(FLET_MAIN), "--web",
         "--port", str(FLET_PORT), "--host", "0.0.0.0"],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    threading.Thread(target=_drain, args=(proc.stdout, "[Flet] "), daemon=True).start()
    return proc

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _drain(stream, prefix):
    """Lee una salida de proceso en segundo plano para evitar bloqueos."""
    try:
        for line in stream:
            line = line.rstrip()
            if line:
                print(prefix + line)
    except Exception:
        pass

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def wait_for_port(port, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    local_ip = get_local_ip()

    print("")
    print("=" * 56)
    print("  Vantti POS - Iniciando...")
    print("=" * 56)
    print("")

    # 1. Descargar cloudflared si no existe
    download_cloudflared()

    # 2. Iniciar Django
    django_proc = start_django()
    if not wait_for_port(DJANGO_PORT, timeout=20):
        print("[ERROR] Django no arranco en el tiempo esperado.")

    # 3. Iniciar tunel HTTPS
    tunnel_proc, tunnel_url = start_tunnel()

    # 4. Iniciar Flet
    flet_proc = start_flet(tunnel_url)
    if not wait_for_port(FLET_PORT, timeout=20):
        print("[ERROR] Flet no arranco en el tiempo esperado.")

    # 5. Mostrar resumen
    print("")
    print("=" * 56)
    print("  Vantti POS LISTO")
    print("=" * 56)
    print("  Escritorio : http://" + local_ip + ":" + str(FLET_PORT))
    print("  Celular    : http://" + local_ip + ":" + str(FLET_PORT))
    if tunnel_url:
        print("")
        print("  Escaner camara (HTTPS sin advertencias):")
        print("  " + tunnel_url + "/api/scanner/")
    print("")
    print("  Presiona Ctrl+C para detener todo.")
    print("=" * 56)
    print("")

    # 6. Esperar Ctrl+C y cerrar todo limpiamente
    procs = [p for p in [django_proc, tunnel_proc, flet_proc] if p]

    def shutdown(sig=None, frame=None):
        print("\n[Sistema] Deteniendo servidores...")
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        if TUNNEL_URL_FILE.exists():
            TUNNEL_URL_FILE.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Mantener vivo hasta que alguno de los procesos termine
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
