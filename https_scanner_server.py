# -*- coding: utf-8 -*-
"""
Servidor HTTPS para el escaner de camara de Vantti POS.

- Sirve la pagina del escaner sobre HTTPS (puerto 8443)
- Recibe los codigos escaneados y los reenv?a a Django internamente
  (evitando el error mixed-content del navegador)
- Compatible con Windows (sin emojis ni caracteres especiales en stdout)
"""
import ssl
import json
import os
import sys
import socket
import datetime
import ipaddress
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Forzar UTF-8 en stdout para Windows
if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ─── Configuracion ────────────────────────────────────────────────────────────
PORT = 8443
DJANGO_BASE = "http://127.0.0.1:8000"
CERT_FILE = "scanner_cert.pem"
KEY_FILE  = "scanner_key.pem"
SCANNER_HTML = Path(__file__).parent / "backend" / "api" / "templates" / "scanner.html"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

# ─── Generar certificado autofirmado ──────────────────────────────────────────

def generate_cert():
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend

    print("[SSL] Generando certificado para IP " + LOCAL_IP + " ...")
    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "MX"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Vantti POS Local"),
        x509.NameAttribute(NameOID.COMMON_NAME, LOCAL_IP),
    ])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=825))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address(LOCAL_IP)),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256(), default_backend())
    )
    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(KEY_FILE, "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ))
    print("[SSL] Certificado guardado: " + CERT_FILE)


# ─── HTML del escaner (autocontenido, sin llamadas HTTP externas) ──────────────

SCANNER_PAGE = None

def build_scanner_html():
    """
    Carga el template y reemplaza la URL del endpoint por la ruta relativa
    /relay/ que el MISMO servidor HTTPS maneja internamente.
    """
    global SCANNER_PAGE
    if SCANNER_HTML.exists():
        html = SCANNER_HTML.read_text(encoding="utf-8")
        # Redirigir las llamadas de fetch al relay HTTPS local
        html = html.replace(
            'fetch("/api/productos/escanear_remoto/"',
            'fetch("/relay/"'
        )
        # Por si ya tenia la URL absoluta de sesiones anteriores
        html = html.replace(
            'fetch("http://' + LOCAL_IP + ':8000/api/productos/escanear_remoto/"',
            'fetch("/relay/"'
        )
        SCANNER_PAGE = html.encode("utf-8")
    else:
        # Pagina de error si no encuentra el template
        SCANNER_PAGE = b"<h1>Error: scanner.html no encontrado</h1>"

# ─── Handler HTTP ─────────────────────────────────────────────────────────────

class ScannerHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        msg = fmt % args
        print("[HTTPS] " + self.address_string() + " -> " + msg)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        if path in ("", "/", "/scanner"):
            build_scanner_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(SCANNER_PAGE)))
            self._cors()
            self.end_headers()
            self.wfile.write(SCANNER_PAGE)

        elif path == "/health":
            self.send_json(200, {"status": "ok"})

        else:
            self.send_json(404, {"error": "ruta no encontrada"})

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        if path == "/relay":
            # Recibir codigo del celular y reenviarlo a Django server-side
            # (asi el browser solo habla con HTTPS, sin mixed-content)
            try:
                data = json.loads(body)
                codigo = data.get("codigo", "").strip()
                print("[SCAN] Codigo recibido: " + codigo)

                # Reenviar a Django internamente (Python, no el browser)
                req = urllib.request.Request(
                    DJANGO_BASE + "/api/productos/escanear_remoto/",
                    data=json.dumps({"codigo": codigo}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp_body = resp.read()
                    self.send_json(200, {"ok": True, "codigo": codigo})

            except urllib.error.URLError as e:
                print("[RELAY] Error al contactar Django: " + str(e))
                self.send_json(502, {"error": "Django no disponible", "detail": str(e)})
            except Exception as e:
                print("[RELAY] Error: " + str(e))
                self.send_json(400, {"error": str(e)})

        else:
            self.send_json(404, {"error": "ruta no encontrada"})


# ─── Agregar regla de firewall automaticamente ────────────────────────────────

def open_firewall_port():
    try:
        import subprocess
        cmd = (
            'powershell -Command "New-NetFirewallRule '
            "-DisplayName 'Vantti POS HTTPS Scanner' "
            "-Direction Inbound -LocalPort " + str(PORT) + " "
            "-Protocol TCP -Action Allow -ErrorAction SilentlyContinue\""
        )
        subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
        print("[FW] Regla de firewall para puerto " + str(PORT) + " configurada.")
    except Exception as e:
        print("[FW] No se pudo configurar firewall: " + str(e))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Regenerar cert si no existe
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        generate_cert()
    else:
        print("[SSL] Usando certificado existente.")

    # Intentar abrir firewall automaticamente
    open_firewall_port()

    # Precargar HTML
    build_scanner_html()

    # Configurar SSL
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    server = HTTPServer(("0.0.0.0", PORT), ScannerHandler)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)

    print("")
    print("=" * 52)
    print("  [HTTPS] Servidor Escaner Vantti POS")
    print("=" * 52)
    print("  Puerto : " + str(PORT))
    print("  PC     : https://localhost:" + str(PORT) + "/scanner")
    print("  Celular: https://" + LOCAL_IP + ":" + str(PORT) + "/scanner")
    print("")
    print("  AVISO: Primera vez el navegador del celular")
    print("  mostrara 'Sitio no seguro'. Pulsa 'Avanzado'")
    print("  -> 'Continuar de todos modos'. Solo 1 vez.")
    print("=" * 52)
    print("")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[HTTPS] Servidor detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
