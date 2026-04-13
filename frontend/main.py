"""
Frontend Flet — Módulo de Venta
Conecta con el backend Django vía API REST (django-rest-framework).
Cambia BASE_URL si tu servidor corre en otro host/puerto.
"""

import flet as ft
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

# ─────────────────────── Paleta de colores ───────────────────────
PRIMARY      = "#1A1A2E"   # azul noche
SECONDARY    = "#16213E"   # azul oscuro
ACCENT       = "#0F3460"   # azul medio
HIGHLIGHT    = "#E94560"   # rojo coral
SURFACE      = "#1F2A47"   # tarjeta
TEXT         = "#EAEAEA"   # texto claro
SUBTEXT      = "#9BA3BC"   # texto secundario
SUCCESS      = "#4CAF50"
WARNING      = "#FFC107"
ERROR_COLOR  = "#F44336"


# ══════════════════════════════════════════════════════════════════
#  HELPERS DE API
# ══════════════════════════════════════════════════════════════════

def api_get(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}/", timeout=5)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "No se pudo conectar al servidor. ¿Está corriendo el backend?"
    except Exception as e:
        return None, str(e)


def api_post(endpoint, data):
    try:
        r = requests.post(f"{BASE_URL}/{endpoint}/", json=data, timeout=5)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "No se pudo conectar al servidor."
    except Exception as e:
        try:
            return None, r.json()
        except Exception:
            return None, str(e)


def api_delete(endpoint, pk):
    try:
        r = requests.delete(f"{BASE_URL}/{endpoint}/{pk}/", timeout=5)
        r.raise_for_status()
        return True, None
    except Exception as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════
#  COMPONENTES REUTILIZABLES
# ══════════════════════════════════════════════════════════════════

def titulo(texto, icono=""):
    return ft.Row([
        ft.Text(icono, size=22),
        ft.Text(texto, size=22, weight=ft.FontWeight.BOLD, color=TEXT),
    ], spacing=8)


def tarjeta(contenido, padding=20):
    return ft.Container(
        content=contenido,
        bgcolor=SURFACE,
        border_radius=12,
        padding=padding,
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=12,
                            color=ft.Colors.with_opacity(0.3, "#000000")),
    )


def boton_primario(texto, on_click, icono=None, color=HIGHLIGHT, expand=False):
    return ft.ElevatedButton(
        text=texto,
        icon=icono,
        on_click=on_click,
        bgcolor=color,
        color=TEXT,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
        ),
        expand=expand,
    )


def campo_texto(label, hint="", password=False, width=None):
    return ft.TextField(
        label=label,
        hint_text=hint,
        password=password,
        bgcolor=SECONDARY,
        border_color=ACCENT,
        focused_border_color=HIGHLIGHT,
        label_style=ft.TextStyle(color=SUBTEXT),
        color=TEXT,
        cursor_color=HIGHLIGHT,
        border_radius=8,
        width=width,
    )


def chip_estado(texto, color):
    return ft.Container(
        content=ft.Text(texto, size=11, color=TEXT, weight=ft.FontWeight.W_600),
        bgcolor=ft.Colors.with_opacity(0.25, color),
        border=ft.border.all(1, ft.Colors.with_opacity(0.6, color)),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )


def snack(page, mensaje, error=False):
    page.snack_bar = ft.SnackBar(
        content=ft.Text(mensaje, color=TEXT),
        bgcolor=ERROR_COLOR if error else SUCCESS,
        duration=3000,
    )
    page.snack_bar.open = True
    page.update()


# ══════════════════════════════════════════════════════════════════
#  VISTAS
# ══════════════════════════════════════════════════════════════════

# ─────────────── DASHBOARD ───────────────
def vista_dashboard(page):
    data_p, _ = api_get("productos")
    data_c, _ = api_get("clientes")
    data_v, _ = api_get("ventas")

    total_productos = len(data_p) if data_p else 0
    total_clientes  = len(data_c) if data_c else 0
    total_ventas    = len(data_v) if data_v else 0
    monto_total     = sum(float(v.get("total", 0)) for v in data_v) if data_v else 0

    def stat_card(label, valor, icono, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icono, color=color, size=28),
                    ft.Text(label, color=SUBTEXT, size=13),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(str(valor), size=36, weight=ft.FontWeight.BOLD, color=TEXT),
            ], spacing=8),
            bgcolor=SURFACE,
            border_radius=14,
            padding=20,
            border=ft.border.all(1, ft.Colors.with_opacity(0.15, color)),
            shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.with_opacity(0.2, "#000")),
            expand=True,
        )

    ventas_recientes = ft.Column(spacing=6)
    if data_v:
        for v in data_v[-5:][::-1]:
            ventas_recientes.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.RECEIPT_LONG, color=HIGHLIGHT, size=18),
                        ft.Column([
                            ft.Text(f"Venta #{v['id']}", color=TEXT, size=13, weight=ft.FontWeight.W_600),
                            ft.Text(v.get("fecha", "")[:10], color=SUBTEXT, size=11),
                        ], spacing=2, expand=True),
                        ft.Text(f"${float(v.get('total',0)):,.2f}", color=SUCCESS,
                                weight=ft.FontWeight.BOLD, size=14),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ft.Colors.with_opacity(0.05, TEXT),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                )
            )
    else:
        ventas_recientes.controls.append(
            ft.Text("Sin ventas registradas aún.", color=SUBTEXT, size=13)
        )

    return ft.Column([
        titulo("Dashboard", "📊"),
        ft.Divider(color=ft.Colors.with_opacity(0.1, TEXT), height=20),
        ft.Row([
            stat_card("Productos",  total_productos, ft.Icons.INVENTORY_2,      "#7C4DFF"),
            stat_card("Clientes",   total_clientes,  ft.Icons.PEOPLE,           "#00BCD4"),
            stat_card("Ventas",     total_ventas,    ft.Icons.POINT_OF_SALE,    HIGHLIGHT),
            stat_card(f"$ Total",   f"{monto_total:,.2f}", ft.Icons.ATTACH_MONEY, SUCCESS),
        ], spacing=16),
        ft.Container(height=24),
        tarjeta(ft.Column([
            ft.Text("🕐  Ventas recientes", color=TEXT, size=15, weight=ft.FontWeight.W_600),
            ft.Divider(color=ft.Colors.with_opacity(0.08, TEXT)),
            ventas_recientes,
        ], spacing=10)),
    ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)


# ─────────────── PRODUCTOS ───────────────
def vista_productos(page):
    lista = ft.ListView(spacing=8, expand=True)
    dlg  = ft.AlertDialog(modal=True)

    def cargar():
        lista.controls.clear()
        data, err = api_get("productos")
        if err:
            lista.controls.append(ft.Text(err, color=ERROR_COLOR))
        elif data:
            for p in data:
                stock_color = SUCCESS if p["stock"] > 5 else WARNING if p["stock"] > 0 else ERROR_COLOR
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(p["nombre"], color=TEXT, size=14, weight=ft.FontWeight.W_600),
                                ft.Text(f"Código: {p['codigo_barras']}", color=SUBTEXT, size=12),
                            ], expand=True, spacing=2),
                            ft.Text(f"${float(p['precio']):,.2f}", color=HIGHLIGHT,
                                    weight=ft.FontWeight.BOLD, size=15),
                            chip_estado(f"Stock: {p['stock']}", stock_color),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ERROR_COLOR,
                                          tooltip="Eliminar",
                                          on_click=lambda e, pid=p["id"]: eliminar(pid)),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=SURFACE,
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=18, vertical=14),
                    )
                )
        else:
            lista.controls.append(ft.Text("No hay productos.", color=SUBTEXT))
        page.update()

    def eliminar(pid):
        ok, err = api_delete("productos", pid)
        if ok:
            snack(page, "Producto eliminado.")
        else:
            snack(page, f"Error: {err}", error=True)
        cargar()

    def abrir_formulario(e):
        nombre = campo_texto("Nombre del producto")
        codigo = campo_texto("Código de barras")
        precio = campo_texto("Precio", hint="0.00")
        stock  = campo_texto("Stock inicial", hint="0")

        def guardar(e):
            data, err = api_post("productos", {
                "nombre": nombre.value,
                "codigo_barras": codigo.value,
                "precio": precio.value,
                "stock": stock.value or 0,
            })
            if err:
                snack(page, f"Error: {err}", error=True)
            else:
                snack(page, "Producto creado.")
                dlg.open = False
                page.update()
                cargar()

        dlg.title   = ft.Text("➕ Nuevo Producto", color=TEXT)
        dlg.bgcolor = SECONDARY
        dlg.content = ft.Column([nombre, codigo, precio, stock], spacing=12, width=350)
        dlg.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: _cerrar_dlg()),
            boton_primario("Guardar", guardar),
        ]
        dlg.open = True
        page.overlay.append(dlg)
        page.update()

    def _cerrar_dlg():
        dlg.open = False
        page.update()

    cargar()

    return ft.Column([
        ft.Row([
            titulo("Productos", "📦"),
            boton_primario("Nuevo Producto", abrir_formulario, ft.Icons.ADD),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(color=ft.Colors.with_opacity(0.1, TEXT), height=20),
        lista,
    ], spacing=12, expand=True)


# ─────────────── CLIENTES ───────────────
def vista_clientes(page):
    lista = ft.ListView(spacing=8, expand=True)
    dlg   = ft.AlertDialog(modal=True)

    def cargar():
        lista.controls.clear()
        data, err = api_get("clientes")
        if err:
            lista.controls.append(ft.Text(err, color=ERROR_COLOR))
        elif data:
            for c in data:
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.CircleAvatar(
                                content=ft.Text(c["nombre"][0].upper(), color=TEXT, weight=ft.FontWeight.BOLD),
                                bgcolor=ACCENT, radius=22,
                            ),
                            ft.Column([
                                ft.Text(c["nombre"], color=TEXT, size=14, weight=ft.FontWeight.W_600),
                                ft.Text(f"✉ {c['email']}  |  📞 {c['telefono']}", color=SUBTEXT, size=12),
                                ft.Text(f"RFC: {c.get('rfc') or '—'}", color=SUBTEXT, size=11),
                            ], expand=True, spacing=2),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ERROR_COLOR,
                                          on_click=lambda e, cid=c["id"]: eliminar(cid)),
                        ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=SURFACE,
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=18, vertical=14),
                    )
                )
        else:
            lista.controls.append(ft.Text("No hay clientes.", color=SUBTEXT))
        page.update()

    def eliminar(cid):
        ok, err = api_delete("clientes", cid)
        if ok:
            snack(page, "Cliente eliminado.")
        else:
            snack(page, f"Error: {err}", error=True)
        cargar()

    def abrir_formulario(e):
        nombre   = campo_texto("Nombre completo")
        email    = campo_texto("Email")
        telefono = campo_texto("Teléfono")
        rfc      = campo_texto("RFC (opcional)")

        def guardar(e):
            data, err = api_post("clientes", {
                "nombre":   nombre.value,
                "email":    email.value,
                "telefono": telefono.value,
                "rfc":      rfc.value or None,
            })
            if err:
                snack(page, f"Error: {err}", error=True)
            else:
                snack(page, "Cliente creado.")
                dlg.open = False
                page.update()
                cargar()

        dlg.title   = ft.Text("👤 Nuevo Cliente", color=TEXT)
        dlg.bgcolor = SECONDARY
        dlg.content = ft.Column([nombre, email, telefono, rfc], spacing=12, width=350)
        dlg.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: _cerrar()),
            boton_primario("Guardar", guardar),
        ]
        dlg.open = True
        if dlg not in page.overlay:
            page.overlay.append(dlg)
        page.update()

    def _cerrar():
        dlg.open = False
        page.update()

    cargar()

    return ft.Column([
        ft.Row([
            titulo("Clientes", "👥"),
            boton_primario("Nuevo Cliente", abrir_formulario, ft.Icons.PERSON_ADD),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(color=ft.Colors.with_opacity(0.1, TEXT), height=20),
        lista,
    ], spacing=12, expand=True)


# ─────────────── NUEVA VENTA ───────────────
def vista_nueva_venta(page):
    clientes_data, _ = api_get("clientes")
    productos_data, _ = api_get("productos")

    clientes  = clientes_data  or []
    productos = productos_data or []

    carrito: list[dict] = []
    total_ref = ft.Ref[ft.Text]()
    tabla_ref = ft.Ref[ft.DataTable]()
    cliente_dd = ft.Dropdown(
        label="Cliente",
        bgcolor=SECONDARY,
        border_color=ACCENT,
        focused_border_color=HIGHLIGHT,
        label_style=ft.TextStyle(color=SUBTEXT),
        color=TEXT,
        border_radius=8,
        options=[ft.dropdown.Option(key=str(c["id"]), text=c["nombre"]) for c in clientes],
    )
    producto_dd = ft.Dropdown(
        label="Producto",
        bgcolor=SECONDARY,
        border_color=ACCENT,
        focused_border_color=HIGHLIGHT,
        label_style=ft.TextStyle(color=SUBTEXT),
        color=TEXT,
        border_radius=8,
        options=[ft.dropdown.Option(key=str(p["id"]), text=f"{p['nombre']} — ${float(p['precio']):,.2f} (stock: {p['stock']})") for p in productos],
    )
    cantidad_field = campo_texto("Cantidad", hint="1", width=120)

    def recalcular():
        total = sum(item["subtotal"] for item in carrito)
        total_ref.current.value = f"Total: ${total:,.2f}"
        filas = []
        for i, item in enumerate(carrito):
            filas.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item["nombre"], color=TEXT)),
                    ft.DataCell(ft.Text(str(item["cantidad"]), color=TEXT)),
                    ft.DataCell(ft.Text(f"${item['precio']:,.2f}", color=TEXT)),
                    ft.DataCell(ft.Text(f"${item['subtotal']:,.2f}", color=HIGHLIGHT,
                                        weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                              icon_color=ERROR_COLOR,
                                              on_click=lambda e, idx=i: quitar_item(idx))),
                ])
            )
        tabla_ref.current.rows = filas
        page.update()

    def quitar_item(idx):
        carrito.pop(idx)
        recalcular()

    def agregar_al_carrito(e):
        if not producto_dd.value:
            snack(page, "Selecciona un producto.", error=True)
            return
        try:
            cant = int(cantidad_field.value or 1)
            assert cant > 0
        except Exception:
            snack(page, "Cantidad inválida.", error=True)
            return

        prod = next((p for p in productos if str(p["id"]) == producto_dd.value), None)
        if not prod:
            return
        if cant > prod["stock"]:
            snack(page, f"Stock insuficiente. Disponible: {prod['stock']}", error=True)
            return

        # si ya está en carrito, suma
        existente = next((item for item in carrito if item["id"] == prod["id"]), None)
        if existente:
            existente["cantidad"] += cant
            existente["subtotal"] = existente["cantidad"] * existente["precio"]
        else:
            carrito.append({
                "id":       prod["id"],
                "nombre":   prod["nombre"],
                "cantidad": cant,
                "precio":   float(prod["precio"]),
                "subtotal": cant * float(prod["precio"]),
            })
        recalcular()

    def finalizar_venta(e):
        if not cliente_dd.value:
            snack(page, "Selecciona un cliente.", error=True)
            return
        if not carrito:
            snack(page, "El carrito está vacío.", error=True)
            return

        total = sum(item["subtotal"] for item in carrito)
        venta_data, err = api_post("ventas", {
            "cliente": int(cliente_dd.value),
            "total": total,
            "detalles": [
                {
                    "producto": item["id"],
                    "cantidad": item["cantidad"],
                    "precio_historico": item["precio"],
                }
                for item in carrito
            ],
        })
        if err:
            snack(page, f"Error al crear venta: {err}", error=True)
        else:
            snack(page, f"✅ Venta #{venta_data['id']} registrada con éxito.")
            carrito.clear()
            recalcular()

    tabla = ft.DataTable(
        ref=tabla_ref,
        columns=[
            ft.DataColumn(ft.Text("Producto",   color=SUBTEXT)),
            ft.DataColumn(ft.Text("Cantidad",   color=SUBTEXT), numeric=True),
            ft.DataColumn(ft.Text("Precio",     color=SUBTEXT), numeric=True),
            ft.DataColumn(ft.Text("Subtotal",   color=SUBTEXT), numeric=True),
            ft.DataColumn(ft.Text("",           color=SUBTEXT)),
        ],
        rows=[],
        border=ft.border.all(0),
        heading_row_color=ft.Colors.with_opacity(0.04, TEXT),
    )

    return ft.Column([
        titulo("Nueva Venta", "🛒"),
        ft.Divider(color=ft.Colors.with_opacity(0.1, TEXT), height=20),
        tarjeta(ft.Column([
            ft.Text("Datos del cliente", color=SUBTEXT, size=12, weight=ft.FontWeight.W_600),
            cliente_dd,
        ], spacing=10)),
        tarjeta(ft.Column([
            ft.Text("Agregar producto", color=SUBTEXT, size=12, weight=ft.FontWeight.W_600),
            ft.Row([producto_dd, cantidad_field,
                    boton_primario("Agregar", agregar_al_carrito, ft.Icons.ADD_SHOPPING_CART)],
                   spacing=12, vertical_alignment=ft.CrossAxisAlignment.END),
        ], spacing=10)),
        tarjeta(ft.Column([
            ft.Text("Carrito", color=TEXT, size=14, weight=ft.FontWeight.W_600),
            ft.Container(content=ft.Column([tabla], scroll=ft.ScrollMode.AUTO), height=220),
            ft.Divider(color=ft.Colors.with_opacity(0.08, TEXT)),
            ft.Row([
                ft.Text("", ref=total_ref, value="Total: $0.00",
                        size=20, weight=ft.FontWeight.BOLD, color=HIGHLIGHT, expand=True),
                boton_primario("Finalizar Venta", finalizar_venta, ft.Icons.CHECK_CIRCLE_OUTLINE, color=SUCCESS),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=12)),
    ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)


# ─────────────── HISTORIAL DE VENTAS ───────────────
def vista_ventas(page):
    lista = ft.ListView(spacing=8, expand=True)

    def cargar():
        lista.controls.clear()
        data, err = api_get("ventas")
        if err:
            lista.controls.append(ft.Text(err, color=ERROR_COLOR))
        elif data:
            for v in reversed(data):
                cliente_nombre = v.get("cliente_nombre") or f"ID {v.get('cliente', '?')}"
                fecha = v.get("fecha", "")[:16].replace("T", " ") if v.get("fecha") else "—"
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.RECEIPT_LONG, color=HIGHLIGHT, size=24),
                            ft.Column([
                                ft.Text(f"Venta #{v['id']}", color=TEXT, size=14,
                                        weight=ft.FontWeight.W_600),
                                ft.Text(f"Cliente: {cliente_nombre}", color=SUBTEXT, size=12),
                                ft.Text(f"Fecha: {fecha}", color=SUBTEXT, size=11),
                            ], expand=True, spacing=2),
                            ft.Text(f"${float(v.get('total', 0)):,.2f}",
                                    color=SUCCESS, weight=ft.FontWeight.BOLD, size=16),
                        ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=SURFACE,
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=18, vertical=14),
                        border=ft.border.all(1, ft.Colors.with_opacity(0.06, TEXT)),
                    )
                )
        else:
            lista.controls.append(ft.Text("Sin ventas registradas.", color=SUBTEXT))
        page.update()

    cargar()

    return ft.Column([
        ft.Row([
            titulo("Historial de Ventas", "📋"),
            boton_primario("Actualizar", lambda e: cargar(), ft.Icons.REFRESH),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(color=ft.Colors.with_opacity(0.1, TEXT), height=20),
        lista,
    ], spacing=12, expand=True)


# ══════════════════════════════════════════════════════════════════
#  APP PRINCIPAL
# ══════════════════════════════════════════════════════════════════

def main(page: ft.Page):
    page.title = "Módulo de Venta"
    page.bgcolor = PRIMARY
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.fonts = {}
    page.window.width  = 1100
    page.window.height = 720
    page.window.min_width  = 800
    page.window.min_height = 600

    # ── Contenedor del contenido principal ──
    contenido = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    def navegar(vista_fn):
        contenido.controls.clear()
        contenido.controls.append(
            ft.Container(content=vista_fn(page), padding=28, expand=True)
        )
        page.update()

    # ── Rail de navegación lateral ──
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        bgcolor=SECONDARY,
        indicator_color=ft.Colors.with_opacity(0.15, HIGHLIGHT),
        indicator_shape=ft.RoundedRectangleBorder(radius=10),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Dashboard",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.INVENTORY_2_OUTLINED,
                selected_icon=ft.Icons.INVENTORY_2,
                label="Productos",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
                label="Clientes",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SHOPPING_CART_OUTLINED,
                selected_icon=ft.Icons.SHOPPING_CART,
                label="Nueva Venta",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                selected_icon=ft.Icons.RECEIPT_LONG,
                label="Ventas",
            ),
        ],
        on_change=lambda e: cambiar_vista(e.control.selected_index),
    )

    vistas = [
        vista_dashboard,
        vista_productos,
        vista_clientes,
        vista_nueva_venta,
        vista_ventas,
    ]

    def cambiar_vista(idx):
        navegar(vistas[idx])

    # Cabecera superior
    header = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.POINT_OF_SALE, color=HIGHLIGHT, size=28),
            ft.Text("Módulo de Venta", size=18, weight=ft.FontWeight.BOLD, color=TEXT),
            ft.Text("v1.0", size=11, color=SUBTEXT),
        ], spacing=10),
        bgcolor=SECONDARY,
        padding=ft.padding.symmetric(horizontal=20, vertical=14),
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.1, TEXT))),
    )

    page.add(
        ft.Column([
            header,
            ft.Row([
                rail,
                ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.07, TEXT)),
                ft.Container(content=contenido, expand=True, bgcolor=PRIMARY),
            ], expand=True, spacing=0),
        ], spacing=0, expand=True)
    )

    navegar(vista_dashboard)


if __name__ == "__main__":
    ft.app(target=main)
