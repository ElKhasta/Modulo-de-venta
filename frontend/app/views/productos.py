import flet as ft

from app.components.ui import app_card, close_dialog, empty_state, field, money, open_dialog, page_header, primary_button, secondary_button, show_message, status_pill
from app.services.api import AuthenticationError, ApiError
from app.theme import ERROR, NAVY, TEXT, TEXT_SOFT


def build_productos_view(page: ft.Page, state):
    productos = []
    search_input = field("Buscar por nombre o codigo", expand=True)
    content_column = ft.Column(spacing=12, scroll=ft.ScrollMode.ALWAYS)

    def handle_auth_error(exc: Exception):
        state.logout()
        show_message(page, str(exc), error=True)
        page.go("/login")

    def render():
        term = (search_input.value or "").strip().lower()
        filtered = [product for product in productos if term in product["nombre"].lower() or term in product["codigo_barras"].lower()]

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
        nonlocal productos
        try:
            productos = state.api.get("productos/") or []
            render()
        except AuthenticationError as exc:
            handle_auth_error(exc)
        except ApiError as exc:
            content_column.controls = [empty_state("No fue posible cargar productos", str(exc))]
            page.update()

    def open_form(product=None):
        nombre = field("Nombre", value=product["nombre"] if product else "")
        codigo = field("Codigo de barras", value=product["codigo_barras"] if product else "")
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

                if product:
                    state.api.put(f"productos/{product['id']}/", json=payload)
                    show_message(page, "Producto actualizado correctamente.")
                else:
                    state.api.post("productos/", json=payload)
                    show_message(page, "Producto creado correctamente.")
                close_dialog(page, dialog)
                load_data()
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
            actions=[secondary_button("Cancelar", lambda e: close_dialog(page, dialog)), primary_button("Guardar", save)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        open_dialog(page, dialog)

    def confirm_delete(product):
        def remove(_):
            try:
                state.api.delete(f"productos/{product['id']}/")
                show_message(page, "Producto eliminado correctamente.")
                close_dialog(page, dialog)
                load_data()
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
            actions=[secondary_button("Cancelar", lambda e: close_dialog(page, dialog)), primary_button("Eliminar", remove, icon=ft.Icons.DELETE_ROUNDED)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        open_dialog(page, dialog)

    search_input.on_change = lambda e: render()
    load_data()

    return ft.Column(
        [
            ft.Row([page_header("Productos", "Administra inventario, precios y stock."), primary_button("Nuevo producto", lambda e: open_form(), icon=ft.Icons.ADD_BOX_ROUNDED)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            app_card(search_input),
            content_column,
        ],
        spacing=20,
        expand=True,
        scroll=ft.ScrollMode.ALWAYS,
    )
