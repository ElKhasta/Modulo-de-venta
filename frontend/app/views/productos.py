import flet as ft
import threading
import time
import base64
import asyncio
import socket
from decimal import Decimal

from app.components.ui import app_card, close_dialog, empty_state, field, money, open_dialog, page_header, primary_button, secondary_button, show_message, status_pill
from app.services.api import AuthenticationError, ApiError
from app.theme import ERROR, NAVY, TEXT, TEXT_SOFT, SUCCESS

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def build_productos_view(page: ft.Page, state):
    productos = []
    productos_cache = {}  # O(1) Cache indexado por codigo_barras
    camara_activa = False
    cap = None
    
    def focus_scanner(*_):
        page.run_task(scan_input.focus)
    
    # Controles de Búsqueda y Filtros
    search_input = field("Buscar por nombre o codigo", expand=True)
    
    # Lector HID con autofocus permanente y debouncing
    scan_input = ft.TextField(
        label="Escáner Láser / Lector HID (Enfoque Permanente)",
        hint_text="Escanea un código de barras...",
        prefix_icon=ft.Icons.QR_CODE_SCANNER_ROUNDED,
        autofocus=True,
        border_radius=14,
        filled=True,
        bgcolor="#F4F6F8",
        on_submit=lambda e: procesar_codigo_escaneado(scan_input.value)
    )
    
    # Píldora de estado del Escáner HID
    scanner_status_pill = ft.Container(
        content=ft.Row([
            ft.Container(width=8, height=8, bgcolor=SUCCESS, border_radius=4),
            ft.Text("Escáner HID Activo", size=12, weight=ft.FontWeight.W_600, color=SUCCESS)
        ], spacing=6),
        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.1, SUCCESS)
    )
    
    content_column = ft.Column(spacing=12, scroll=ft.ScrollMode.ALWAYS)

    def handle_auth_error(exc: Exception):
        state.logout()
        show_message(page, str(exc), error=True)
        page.go("/login")

    def render():
        term = (search_input.value or "").strip().lower()
        filtered = [
            product for product in productos 
            if term in product["nombre"].lower() or term in product["codigo_barras"].lower()
        ]

        if not filtered:
            content_column.controls = [empty_state("Sin productos", "Agrega productos para comenzar a vender.")]
        else:
            rows = []
            for product in filtered:
                tone = "success" if int(product["stock"]) > 5 else "warning" if int(product["stock"]) > 0 else "error"
                rows.append(
                    app_card(
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(product["nombre"], size=16, weight=ft.FontWeight.W_700, color=TEXT),
                                        ft.Text(f"Codigo: {product['codigo_barras']}", size=12, color=TEXT_SOFT),
                                    ],
                                    spacing=4,
                                    expand=True,
                                ),
                                ft.Text(money(product["precio"]), size=16, weight=ft.FontWeight.W_700, color=NAVY),
                                status_pill(f"Stock {product['stock']}", tone),
                                ft.IconButton(icon=ft.Icons.EDIT_ROUNDED, on_click=lambda e, p=product: open_form(p)),
                                ft.IconButton(icon=ft.Icons.DELETE_ROUNDED, icon_color=ERROR, on_click=lambda e, p=product: confirm_delete(p)),
                            ],
                            spacing=16,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    )
                )
            content_column.controls = rows
        page.update()

    def load_data():
        nonlocal productos, productos_cache
        try:
            productos = state.api.get("productos/") or []
            
            # Reconstruir caché local O(1)
            productos_cache.clear()
            for p in productos:
                productos_cache[p["codigo_barras"]] = p
                
            render()
        except AuthenticationError as exc:
            handle_auth_error(exc)
        except ApiError as exc:
            content_column.controls = [empty_state("No fue posible cargar productos", str(exc))]
            page.update()

    def open_form(product=None, new_barcode=None):
        nombre = field("Nombre", value=product["nombre"] if product else "")
        codigo = field("Codigo de barras", value=product["codigo_barras"] if product else (new_barcode or ""))
        precio = field("Precio", value=str(product["precio"]) if product else "")
        stock = field("Stock", value=str(product["stock"]) if product else "0")

        def save(_):
            try:
                nombre_value = (nombre.value or "").strip()
                codigo_value = (codigo.value or "").strip()
                precio_value = float((precio.value or "0").strip())
                stock_value = int((stock.value or "0").strip())

                if not nombre_value or not codigo_value:
                    raise ValueError("Captura nombre y codigo de barras.")
                if precio_value <= 0:
                    raise ValueError("El precio debe ser mayor a cero.")
                if stock_value < 0:
                    raise ValueError("El stock no puede ser negativo.")

                payload = {
                    "nombre": nombre_value,
                    "codigo_barras": codigo_value,
                    "precio": f"{precio_value:.2f}",
                    "stock": stock_value,
                }

                if product and "id" in product:
                    state.api.put(f"productos/{product['codigo_barras']}/", json=payload)
                    show_message(page, "Producto actualizado correctamente.")
                elif product and "id" not in product and codigo_value in productos_cache:
                    # En caso de que se haya cargado del backend por escaneo pero no esté en cache local
                    state.api.put(f"productos/{codigo_value}/", json=payload)
                    show_message(page, "Producto actualizado correctamente.")
                else:
                    state.api.post("productos/", json=payload)
                    show_message(page, "Producto creado correctamente.")
                
                close_dialog(page, dialog)
                load_data()
                
                # Devolver el foco al scanner HID
                focus_scanner()
            except AuthenticationError as exc:
                close_dialog(page, dialog)
                handle_auth_error(exc)
            except Exception as exc:
                show_message(page, str(exc), error=True)

        dialog = ft.AlertDialog(
            modal=True,
            scrollable=True,
            title=ft.Text("Editar producto" if product else "Nuevo producto"),
            content=ft.Container(width=420, content=ft.Column([nombre, codigo, precio, stock], spacing=14, tight=True)),
            actions=[
                secondary_button("Cancelar", lambda e: [close_dialog(page, dialog), focus_scanner()]),
                primary_button("Guardar", save)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=focus_scanner
        )
        open_dialog(page, dialog)

    def confirm_delete(product):
        def remove(_):
            try:
                state.api.delete(f"productos/{product['codigo_barras']}/")
                show_message(page, "Producto eliminado correctamente.")
                close_dialog(page, dialog)
                load_data()
                focus_scanner()
            except AuthenticationError as exc:
                close_dialog(page, dialog)
                handle_auth_error(exc)
            except Exception as exc:
                show_message(page, str(exc), error=True)

        dialog = ft.AlertDialog(
            modal=True,
            scrollable=True,
            title=ft.Text("Eliminar producto"),
            content=ft.Text(f"Se eliminara '{product['nombre']}'. Esta accion no se puede deshacer."),
            actions=[
                secondary_button("Cancelar", lambda e: [close_dialog(page, dialog), focus_scanner()]),
                primary_button("Eliminar", remove, icon=ft.Icons.DELETE_ROUNDED)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=focus_scanner
        )
        open_dialog(page, dialog)

    def procesar_codigo_escaneado(codigo):
        if not codigo:
            return
        
        codigo_str = str(codigo).strip()
        
        # Debouncing: Bloqueamos temporalmente el lector para evitar doble escaneo
        scan_input.disabled = True
        scan_input.update()

        # 1. Intentar resolver localmente usando caché local O(1)
        product = productos_cache.get(codigo_str)
        if product:
            show_message(page, f"Código '{codigo_str}' resuelto instantáneamente en caché O(1).")
            open_form(product)
            
            scan_input.value = ""
            scan_input.disabled = False
            scan_input.update()
            focus_scanner()
            return

        # 2. Consultar al backend (defensivo: maneja QR de fidelización y GS1 variable)
        try:
            response = state.api.post("productos/procesar_escaneo/", json={"codigo": codigo_str})
            if response:
                tipo = response.get("tipo")
                datos = response.get("datos")
                
                if tipo == "producto":
                    # Producto cargado desde el backend (ej: precio dinámico peso variable)
                    open_form(datos)
                    show_message(page, f"Producto '{datos['nombre']}' cargado por escaneo.")
                elif tipo == "cliente":
                    show_message(page, f"Cliente QR Detectado: {datos['nombre']} (RFC: {datos['rfc']})")
                else:
                    show_message(page, f"Escaneo recibido: {tipo}")
        except Exception:
            # 3. Si no existe en la base de datos ni en cache, abrimos el formulario de nuevo producto
            show_message(page, f"Código '{codigo_str}' no registrado. Iniciando registro...", error=True)
            open_form(new_barcode=codigo_str)

        # Restaurar lector HID y re-enfocar imperativamente
        scan_input.value = ""
        scan_input.disabled = False
        scan_input.update()
        focus_scanner()

    def abrir_dialogo_vincular_celular(e):
        local_ip = get_local_ip()
        local_url = f"http://{local_ip}:8080/"
        
        dialog = ft.AlertDialog(
            modal=True,
            scrollable=True,
            title=ft.Text("Vincular Celular como Escáner"),
            content=ft.Container(
                width=450,
                content=ft.Column([
                    ft.Text("Sigue estos pasos para usar tu teléfono como escáner inalámbrico:", size=13, color=TEXT_SOFT),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Column([
                        ft.Row([
                            ft.Container(content=ft.Text("1", size=10, color=NAVY, weight=ft.FontWeight.W_700), bgcolor=GOLD, width=18, height=18, border_radius=9, alignment=ft.alignment.Alignment(0, 0)),
                            ft.Text("Conecta el celular a la misma red Wi-Fi.", size=12, color=TEXT)
                        ], spacing=8),
                        ft.Row([
                            ft.Container(content=ft.Text("2", size=10, color=NAVY, weight=ft.FontWeight.W_700), bgcolor=GOLD, width=18, height=18, border_radius=9, alignment=ft.alignment.Alignment(0, 0)),
                            ft.Text("Escanea el QR de abajo con la cámara de tu celular:", size=12, color=TEXT)
                        ], spacing=8),
                        ft.Row([
                            ft.Container(content=ft.Text("3", size=10, color=NAVY, weight=ft.FontWeight.W_700), bgcolor=GOLD, width=18, height=18, border_radius=9, alignment=ft.alignment.Alignment(0, 0)),
                            ft.Text("O ingresa esta dirección en el navegador:", size=12, color=TEXT)
                        ], spacing=8),
                    ], spacing=8),
                    ft.Container(
                        content=ft.Text(local_url, size=14, weight=ft.FontWeight.W_700, color=NAVY, selectable=True),
                        bgcolor="#E9EEF5",
                        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                        border_radius=8,
                        alignment=ft.alignment.Alignment(0, 0)
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Container(
                        content=ft.Image(
                            src=f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&color=003366&data={local_url}",
                            width=180,
                            height=180,
                            fit="contain"
                        ),
                        alignment=ft.alignment.Alignment(0, 0)
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.SECURITY_ROUNDED, color=GOLD, size=16),
                                ft.Text("¿El celular no puede acceder?", size=11, weight=ft.FontWeight.W_700, color=NAVY)
                            ], spacing=6),
                            ft.Text("Asegúrate de ejecutar abrir_puertos_firewall.bat en la raíz del proyecto haciendo click derecho y seleccionando 'Ejecutar como Administrador' para abrir el cortafuegos.", size=10, color=TEXT_SOFT)
                        ], spacing=4),
                        border=ft.Border.all(1, "#D5DDE6"),
                        bgcolor="#F4F6F8",
                        border_radius=10,
                        padding=10
                    )
                ], spacing=10, tight=True)
            ),
            actions=[
                primary_button("Entendido", lambda e: [close_dialog(page, dialog), focus_scanner()])
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=focus_scanner
        )
        open_dialog(page, dialog)

    # Polling asíncrono para Escáner Remoto Móvil
    async def polling_escaneos_remotos():
        while page.route == "/productos":
            try:
                response = state.api.get("productos/obtener_escaneos_remotos/")
                if response and response.get("escaneos"):
                    for code in response["escaneos"]:
                        procesar_codigo_escaneado(code)
            except Exception:
                pass
            await asyncio.sleep(1.0)

    # Iniciar polling y carga de datos
    search_input.on_change = lambda e: render()
    load_data()
    
    # Iniciar tarea asíncrona de polling de escáner remoto móvil
    page.run_task(polling_escaneos_remotos)

    return ft.Column(
        [
            ft.Row(
                [
                    page_header("Productos", "Administra inventario, precios y stock."),
                    ft.Row([
                        secondary_button(
                            "Cámara PC",
                            icon=ft.Icons.COMPUTER_ROUNDED,
                            url=f"{state.api.base_url.rstrip('/')}/scanner/"
                        ),
                        secondary_button(
                            "Cámara Celular (QR)",
                            icon=ft.Icons.PHONE_ANDROID_ROUNDED,
                            on_click=abrir_dialogo_vincular_celular
                        ),
                        primary_button("Nuevo producto", lambda e: open_form(), icon=ft.Icons.ADD_BOX_ROUNDED)
                    ], spacing=12)
                ], 
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            app_card(
                ft.Column([
                    ft.Row([search_input, scanner_status_pill], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    scan_input
                ], spacing=12)
            ),
            content_column,
        ],
        spacing=20,
        expand=True,
        scroll=ft.ScrollMode.ALWAYS,
    )
