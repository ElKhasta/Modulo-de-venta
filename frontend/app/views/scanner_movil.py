import flet as ft
import threading
import time
import base64
import requests
import socket
import os
from pathlib import Path
from app.components.ui import app_card, page_header, primary_button, secondary_button, show_message, close_dialog, open_dialog
from app.theme import NAVY, GOLD, SURFACE, TEXT, TEXT_SOFT, SUCCESS, ERROR

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def build_scanner_movil_view(page: ft.Page, state):
    historial = []
    
    # Controles de UI
    server_status = ft.Row([
        ft.Container(width=10, height=10, bgcolor=SUCCESS, border_radius=5),
        ft.Text("Conectado a Escritorio", size=13, weight=ft.FontWeight.W_600, color=SUCCESS)
    ], alignment=ft.MainAxisAlignment.CENTER)
    
    codigo_field = ft.TextField(
        label="Código manual",
        hint_text="Escribe o simula el código de barras",
        border_radius=14,
        filled=True,
        bgcolor="#F4F6F8",
        on_submit=lambda e: enviar_escaneo()
    )
    
    historial_column = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, expand=True)
    
    def render_historial():
        if not historial:
            historial_column.controls = [
                ft.Container(
                    content=ft.Text("Ningún código escaneado recientemente.", size=12, color=TEXT_SOFT, italic=True),
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=20
                )
            ]
        else:
            controls = []
            for item in reversed(historial):
                controls.append(
                    app_card(
                        ft.Row([
                            ft.Icon(ft.Icons.QR_CODE_SCANNER_ROUNDED, color=NAVY),
                            ft.Column([
                                ft.Text(item["codigo"], size=14, weight=ft.FontWeight.W_700, color=TEXT),
                                ft.Text(f"Enviado a las {item['hora']}", size=11, color=TEXT_SOFT),
                            ], spacing=2, expand=True),
                            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=SUCCESS, size=18)
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=12
                    )
                )
            historial_column.controls = controls
        page.update()

    def enviar_escaneo(codigo=None):
        codigo_val = (codigo or codigo_field.value or "").strip()
        if not codigo_val:
            show_message(page, "Por favor ingresa un código válido.", error=True)
            return
            
        try:
            # Enviar a la API del backend Django
            payload = {"codigo": codigo_val}
            response = state.api.post("productos/escanear_remoto/", json=payload)
            
            # Registrar en el historial local
            hora_actual = time.strftime("%H:%M:%S")
            historial.append({"codigo": codigo_val, "hora": hora_actual})
            
            show_message(page, f"Enviado con éxito: {codigo_val}")
            codigo_field.value = ""
            render_historial()
            
        except Exception as exc:
            show_message(page, f"Error al enviar: {str(exc)}", error=True)

    render_historial()

    # Dynamic local IP and QR configuration for desktop connection
    local_ip = get_local_ip()
    local_url = f"http://{local_ip}:8080/"

    # URL del escaner: usa tunel HTTPS de Cloudflare si esta disponible,
    # de lo contrario usa el servidor HTTPS local (puerto 8443).
    # El tunel lo arranca iniciar.py y escribe la URL en .tunnel_url
    def get_scanner_url():
        # 1. Variable de entorno (la setea iniciar.py al arrancar)
        tunnel = os.environ.get("VANTTI_TUNNEL_URL", "").strip()
        if tunnel:
            return tunnel + "/api/scanner/"
        # 2. Archivo .tunnel_url (escrito por iniciar.py)
        tunnel_file = Path(__file__).parent.parent.parent / ".tunnel_url"
        if tunnel_file.exists():
            tunnel = tunnel_file.read_text(encoding="utf-8").strip()
            if tunnel:
                return tunnel + "/api/scanner/"
        # 3. Fallback: servidor HTTPS local con cert autofirmado
        return f"https://{local_ip}:8443/scanner"

    scanner_url = get_scanner_url()
    usando_tunel = scanner_url.startswith("https://") and "trycloudflare" in scanner_url

    # Mobile Layout: Camera scanner trigger and manual tools
    card_principal_movil = app_card(
        ft.Column([
            ft.Text("Escáner Móvil Remoto", size=20, weight=ft.FontWeight.W_700, color=TEXT),
            ft.Text("Usa este dispositivo móvil como un escáner de hardware inalámbrico para el POS de Escritorio.", size=12, color=TEXT_SOFT, text_align=ft.TextAlign.CENTER),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            server_status,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.FilledButton(
                "Escanear con Camara",
                icon=ft.Icons.CAMERA_ALT_ROUNDED,
                url=scanner_url,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: GOLD},
                    color={ft.ControlState.DEFAULT: NAVY},
                    padding=ft.Padding.symmetric(horizontal=18, vertical=16),
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
                expand=True
            ),
            # Mostrar estado del tunel HTTPS
            ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.LOCK_ROUNDED if usando_tunel else ft.Icons.LOCK_OPEN_ROUNDED,
                        color=SUCCESS if usando_tunel else GOLD,
                        size=14
                    ),
                    ft.Text(
                        "HTTPS seguro - camara lista" if usando_tunel
                        else "Ejecuta iniciar.py para habilitar la camara automaticamente",
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=SUCCESS if usando_tunel else TEXT_SOFT
                    ),
                ], spacing=6),
                bgcolor="#F0FFF4" if usando_tunel else "#FFF8E7",
                border=ft.Border.all(1, SUCCESS if usando_tunel else GOLD),
                border_radius=10,
                padding=ft.Padding.symmetric(horizontal=12, vertical=8)
            ),
            ft.Text("— O —", size=12, color=TEXT_SOFT, weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
            ft.Row([codigo_field, primary_button("Enviar", lambda e: enviar_escaneo(), icon=ft.Icons.SEND_ROUNDED)], spacing=10),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Text("Historial de Escaneos Remotos", size=14, weight=ft.FontWeight.W_700, color=TEXT),
            historial_column
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=24
    )

    # Desktop Layout: Pairing QR Code and step-by-step guides
    card_emparejamiento_pc = ft.ResponsiveRow([
        ft.Container(
            content=app_card(
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PHONELINK_SETUP_ROUNDED, color=NAVY, size=26),
                        ft.Text("Vincular Teléfono Celular", size=20, weight=ft.FontWeight.W_700, color=TEXT)
                    ], spacing=10),
                    ft.Text("Sigue estos sencillos pasos para usar tu teléfono como escáner inalámbrico activo:", size=13, color=TEXT_SOFT),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Column([
                        ft.Row([
                            ft.Container(content=ft.Text("1", size=11, color=NAVY, weight=ft.FontWeight.W_700), bgcolor=GOLD, width=20, height=20, border_radius=10, alignment=ft.alignment.Alignment(0, 0)),
                            ft.Text("Conecta tu celular a la misma red Wi-Fi que esta computadora.", size=12, color=TEXT, weight=ft.FontWeight.W_500)
                        ], spacing=10),
                        ft.Row([
                            ft.Container(content=ft.Text("2", size=11, color=NAVY, weight=ft.FontWeight.W_700), bgcolor=GOLD, width=20, height=20, border_radius=10, alignment=ft.alignment.Alignment(0, 0)),
                            ft.Text("Escanea el código QR de la derecha con tu teléfono.", size=12, color=TEXT, weight=ft.FontWeight.W_500)
                        ], spacing=10),
                        ft.Row([
                            ft.Container(content=ft.Text("3", size=11, color=NAVY, weight=ft.FontWeight.W_700), bgcolor=GOLD, width=20, height=20, border_radius=10, alignment=ft.alignment.Alignment(0, 0)),
                            ft.Text("O ingresa esta dirección en tu navegador móvil:", size=12, color=TEXT, weight=ft.FontWeight.W_500)
                        ], spacing=10),
                    ], spacing=12),
                    ft.Container(
                        content=ft.Text(local_url, size=15, weight=ft.FontWeight.W_700, color=NAVY, selectable=True),
                        bgcolor="#E9EEF5",
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                        border_radius=10,
                        alignment=ft.alignment.Alignment(0, 0)
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.SECURITY_ROUNDED, color=GOLD, size=18),
                                ft.Text("¿El celular no puede acceder?", size=12, weight=ft.FontWeight.W_700, color=NAVY)
                            ], spacing=6),
                            ft.Text("Firewall bloquea las conexiones locales. Ejecuta abrir_puertos_firewall.bat como Administrador (abre puertos 8000, 8080 y 8443).\n\nPara el escáner de cámara: al abrir, acepta la advertencia del certificado una sola vez pulsando 'Avanzado' → 'Continuar de todos modos'.", size=11, color=TEXT_SOFT)
                        ], spacing=6),
                        border=ft.Border.all(1, "#D5DDE6"),
                        bgcolor="#F4F6F8",
                        border_radius=12,
                        padding=12
                    )
                ], spacing=12)
            ),
            col={"xs": 12, "md": 7}
        ),
        ft.Container(
            content=app_card(
                ft.Column([
                    ft.Text("Código QR de Enlace", size=16, weight=ft.FontWeight.W_700, color=TEXT, text_align=ft.TextAlign.CENTER),
                    ft.Text("Apunta la cámara de tu celular aquí", size=12, color=TEXT_SOFT, text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Container(
                        content=ft.Image(
                            src=f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&color=003366&data={local_url}",
                            width=220,
                            height=220,
                            fit="contain"
                        ),
                        alignment=ft.alignment.Alignment(0, 0)
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Text(f"Red Local: {local_ip}", size=12, color=NAVY, weight=ft.FontWeight.W_700, text_align=ft.TextAlign.CENTER)
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=24
            ),
            col={"xs": 12, "md": 5}
        )
    ], spacing=20)

    # Responsive view picker based on client screen size
    is_mobile = page.width < 768

    content_layout = ft.Column([
        page_header("Escáner Móvil", "Transmite códigos de barras instantáneamente a la pantalla de tu computadora."),
        ft.Row([
            ft.Container(
                content=card_principal_movil if is_mobile else card_emparejamiento_pc,
                expand=True,
                width=440 if is_mobile else 880
            )
        ], alignment=ft.MainAxisAlignment.CENTER, expand=True)
    ], spacing=20, expand=True, scroll=ft.ScrollMode.ALWAYS)

    # Habilitar pellizcar para hacer zoom y navegación táctil fluida con los dedos en celulares
    return ft.InteractiveViewer(
        content=content_layout,
        min_scale=1.0,
        max_scale=3.5,
        expand=True
    )
