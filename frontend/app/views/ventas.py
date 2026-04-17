import flet as ft

from app.components.ui import app_card, empty_state, field, money, page_header, primary_button, secondary_button, show_message
from app.services.api import AuthenticationError, ApiError
from app.theme import ERROR, NAVY, SUCCESS, TEXT, TEXT_SOFT


def build_ventas_view(page: ft.Page, state):
    clientes = []
    productos = []
    ventas = []
    carrito = []
    editing_sale_id = None

    cliente_dropdown = ft.Dropdown(label="Cliente", border_radius=14, filled=True, bgcolor="#F4F6F8")
    producto_dropdown = ft.Dropdown(label="Producto", border_radius=14, filled=True, bgcolor="#F4F6F8", expand=True)
    cantidad_field = field("Cantidad", value="1", width=120)
    cart_column = ft.Column(spacing=10)
    sales_column = ft.Column(spacing=12)
    mode_text = ft.Text("Nueva venta", size=20, weight=ft.FontWeight.W_700, color=TEXT)
    helper_text = ft.Text("Agrega productos al carrito y registra la venta.", size=12, color=TEXT_SOFT)
    total_text = ft.Text(money(0), size=28, weight=ft.FontWeight.W_700, color=NAVY)

    def handle_auth_error(exc: Exception):
        state.logout()
        show_message(page, str(exc), error=True)
        page.go("/login")

    def close_dialog(dialog):
        dialog.open = False
        page.update()

    def update_catalog_options():
        cliente_dropdown.options = [ft.dropdown.Option(key="", text="Publico general")]
        cliente_dropdown.options.extend([ft.dropdown.Option(key=str(client["id"]), text=client["nombre"]) for client in clientes])
        producto_dropdown.options = [
            ft.dropdown.Option(key=str(product["id"]), text=f"{product['nombre']} | {money(product['precio'])} | stock {product['stock']}")
            for product in productos
        ]

    def render_cart():
        total = sum(float(item["precio_historico"]) * int(item["cantidad"]) for item in carrito)
        total_text.value = money(total)

        if not carrito:
            cart_column.controls = [empty_state("Carrito vacio", "Selecciona productos para crear una venta.")]
        else:
            rows = []
            for index, item in enumerate(carrito):
                subtotal = float(item["precio_historico"]) * int(item["cantidad"])
                rows.append(
                    app_card(
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(item["nombre"], size=15, weight=ft.FontWeight.W_700, color=TEXT),
                                        ft.Text(f"Cantidad: {item['cantidad']} | Precio unitario: {money(item['precio_historico'])}", size=12, color=TEXT_SOFT),
                                    ],
                                    spacing=4,
                                    expand=True,
                                ),
                                ft.Text(money(subtotal), size=16, weight=ft.FontWeight.W_700, color=SUCCESS),
                                ft.IconButton(icon=ft.Icons.DELETE_ROUNDED, icon_color=ERROR, on_click=lambda e, idx=index: remove_item(idx)),
                            ],
                            spacing=16,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=16,
                    )
                )
            cart_column.controls = rows
        page.update()

    def render_sales():
        if not ventas:
            sales_column.controls = [empty_state("Sin ventas", "Las ventas registradas apareceran aqui.")]
        else:
            rows = []
            for sale in ventas:
                detail_count = len(sale.get("detalles") or [])
                rows.append(
                    app_card(
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Column(
                                            [
                                                ft.Text(f"Venta #{sale['id']}", size=16, weight=ft.FontWeight.W_700, color=TEXT),
                                                ft.Text(sale.get("cliente_nombre", "Publico general"), size=12, color=TEXT_SOFT),
                                            ],
                                            spacing=4,
                                            expand=True,
                                        ),
                                        ft.Text(money(sale.get("total", 0)), size=18, weight=ft.FontWeight.W_700, color=SUCCESS),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(f"Productos en la venta: {detail_count}", size=12, color=TEXT_SOFT),
                                ft.Row(
                                    [
                                        secondary_button("Editar", lambda e, s=sale: load_sale(s), icon=ft.Icons.EDIT_ROUNDED, expand=True),
                                        primary_button("Eliminar", lambda e, s=sale: confirm_delete(s), icon=ft.Icons.DELETE_ROUNDED, expand=True),
                                    ],
                                    spacing=12,
                                ),
                            ],
                            spacing=12,
                        )
                    )
                )
            sales_column.controls = rows
        page.update()

    def refresh_catalogs():
        nonlocal clientes, productos
        clientes = state.api.get("clientes/") or []
        productos = state.api.get("productos/") or []
        update_catalog_options()
        page.update()

    def load_sales():
        nonlocal ventas
        ventas = state.api.get("ventas/") or []
        render_sales()

    def reset_form():
        nonlocal editing_sale_id, carrito
        editing_sale_id = None
        carrito = []
        cliente_dropdown.value = ""
        producto_dropdown.value = None
        cantidad_field.value = "1"
        mode_text.value = "Nueva venta"
        helper_text.value = "Agrega productos al carrito y registra la venta."
        save_button.text = "Guardar venta"
        render_cart()
        page.update()

    def load_sale(sale):
        nonlocal editing_sale_id, carrito
        editing_sale_id = sale["id"]
        cliente_dropdown.value = str(sale.get("cliente") or "")
        carrito = [
            {
                "producto_id": detail["producto"],
                "nombre": detail["producto_nombre"],
                "cantidad": int(detail["cantidad"]),
                "precio_historico": float(detail["precio_historico"]),
            }
            for detail in sale.get("detalles", [])
        ]
        mode_text.value = f"Editando venta #{sale['id']}"
        helper_text.value = "Al guardar, el backend recalcula stock y total de forma segura."
        save_button.text = "Actualizar venta"
        render_cart()

    def remove_item(index: int):
        carrito.pop(index)
        render_cart()

    def add_item():
        product_id = producto_dropdown.value
        if not product_id:
            show_message(page, "Selecciona un producto.", error=True)
            return

        try:
            quantity = int(cantidad_field.value or 0)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            show_message(page, "La cantidad debe ser mayor a cero.", error=True)
            return

        product = next((item for item in productos if str(item["id"]) == product_id), None)
        if not product:
            show_message(page, "Producto no disponible.", error=True)
            return

        existing = next((item for item in carrito if item["producto_id"] == product["id"]), None)
        if existing:
            existing["cantidad"] += quantity
        else:
            carrito.append(
                {
                    "producto_id": product["id"],
                    "nombre": product["nombre"],
                    "cantidad": quantity,
                    "precio_historico": float(product["precio"]),
                }
            )

        producto_dropdown.value = None
        cantidad_field.value = "1"
        render_cart()

    def save_sale():
        if not carrito:
            show_message(page, "Agrega al menos un producto al carrito.", error=True)
            return

        payload = {
            "cliente": int(cliente_dropdown.value) if cliente_dropdown.value else None,
            "detalles": [
                {
                    "producto": item["producto_id"],
                    "cantidad": int(item["cantidad"]),
                    "precio_historico": item["precio_historico"],
                }
                for item in carrito
            ],
        }

        try:
            if editing_sale_id:
                state.api.put(f"ventas/{editing_sale_id}/", json=payload)
                show_message(page, "Venta actualizada correctamente.")
            else:
                state.api.post("ventas/", json=payload)
                show_message(page, "Venta registrada correctamente.")
            reset_form()
            refresh_catalogs()
            load_sales()
        except AuthenticationError as exc:
            handle_auth_error(exc)
        except Exception as exc:
            show_message(page, str(exc), error=True)

    def confirm_delete(sale):
        def remove(_):
            try:
                state.api.delete(f"ventas/{sale['id']}/")
                show_message(page, "Venta eliminada correctamente.")
                close_dialog(dialog)
                if editing_sale_id == sale["id"]:
                    reset_form()
                refresh_catalogs()
                load_sales()
            except AuthenticationError as exc:
                close_dialog(dialog)
                handle_auth_error(exc)
            except Exception as exc:
                show_message(page, str(exc), error=True)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar venta"),
            content=ft.Text(f"Se eliminara la venta #{sale['id']} y el stock sera restaurado."),
            actions=[secondary_button("Cancelar", lambda e: close_dialog(dialog)), primary_button("Eliminar", remove, icon=ft.Icons.DELETE_ROUNDED)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    save_button = primary_button("Guardar venta", lambda e: save_sale(), icon=ft.Icons.CHECK_CIRCLE_ROUNDED)
    cancel_button = secondary_button("Limpiar", lambda e: reset_form())

    try:
        refresh_catalogs()
        load_sales()
        reset_form()
    except AuthenticationError as exc:
        handle_auth_error(exc)
    except ApiError as exc:
        return ft.Column([page_header("Ventas", "No fue posible cargar el modulo de ventas."), empty_state("Error de conexion", str(exc))], spacing=20)

    form_card = app_card(
        ft.Column(
            [
                mode_text,
                helper_text,
                cliente_dropdown,
                ft.Row([producto_dropdown, cantidad_field], spacing=12),
                primary_button("Agregar al carrito", lambda e: add_item(), icon=ft.Icons.ADD_SHOPPING_CART_ROUNDED, expand=True),
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                ft.Text("Carrito", size=16, weight=ft.FontWeight.W_700, color=TEXT),
                cart_column,
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
                ft.Row(
                    [
                        ft.Column([ft.Text("Total actual", size=12, color=TEXT_SOFT), total_text], spacing=4),
                        ft.Row([cancel_button, save_button], spacing=12),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=14,
        ),
        expand=True,
    )

    history_card = app_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Historial de ventas", size=20, weight=ft.FontWeight.W_700, color=TEXT),
                                ft.Text("Puedes editar o eliminar ventas registradas.", size=12, color=TEXT_SOFT),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        secondary_button("Actualizar", lambda e: load_sales(), icon=ft.Icons.REFRESH_ROUNDED),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                sales_column,
            ],
            spacing=14,
        ),
        expand=True,
    )

    return ft.Column(
        [
            page_header("Ventas", "Registra operaciones reales y controla inventario en la misma vista."),
            ft.ResponsiveRow(
                [
                    ft.Container(content=form_card, col={"xs": 12, "lg": 7}),
                    ft.Container(content=history_card, col={"xs": 12, "lg": 5}),
                ],
                run_spacing=16,
            ),
        ],
        spacing=20,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
