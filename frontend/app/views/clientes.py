import flet as ft

from app.components.ui import app_card, close_dialog, empty_state, field, open_dialog, page_header, primary_button, secondary_button, show_message
from app.services.api import AuthenticationError, ApiError
from app.theme import ERROR, TEXT, TEXT_SOFT


def build_clientes_view(page: ft.Page, state):
    clientes = []
    search_input = field("Buscar por nombre, telefono, email o RFC", expand=True)
    content_column = ft.Column(spacing=12, scroll=ft.ScrollMode.ALWAYS)

    def handle_auth_error(exc: Exception):
        state.logout()
        show_message(page, str(exc), error=True)
        page.go("/login")

    def render():
        term = (search_input.value or "").strip().lower()
        filtered = [
            client
            for client in clientes
            if term in client["nombre"].lower()
            or term in client["telefono"].lower()
            or term in client["email"].lower()
            or term in str(client.get("rfc") or "").lower()
        ]

        if not filtered:
            content_column.controls = [empty_state("Sin clientes", "Registra clientes para asociarlos a ventas.")]
        else:
            rows = []
            for client in filtered:
                rows.append(
                    app_card(
                        ft.Row(
                            [
                                ft.CircleAvatar(bgcolor=ft.Colors.with_opacity(0.12, "#003366"), content=ft.Text(client["nombre"][:1].upper())),
                                ft.Column(
                                    [
                                        ft.Text(client["nombre"], size=16, weight=ft.FontWeight.W_700, color=TEXT),
                                        ft.Text(client["email"], size=12, color=TEXT_SOFT),
                                        ft.Text(f"Tel: {client['telefono']} | RFC: {client.get('rfc') or 'Sin RFC'}", size=12, color=TEXT_SOFT),
                                    ],
                                    spacing=4,
                                    expand=True,
                                ),
                                ft.IconButton(icon=ft.Icons.EDIT_ROUNDED, on_click=lambda e, c=client: open_form(c)),
                                ft.IconButton(icon=ft.Icons.DELETE_ROUNDED, icon_color=ERROR, on_click=lambda e, c=client: confirm_delete(c)),
                            ],
                            spacing=16,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    )
                )
            content_column.controls = rows
        page.update()

    def load_data():
        nonlocal clientes
        try:
            clientes = state.api.get("clientes/") or []
            render()
        except AuthenticationError as exc:
            handle_auth_error(exc)
        except ApiError as exc:
            content_column.controls = [empty_state("No fue posible cargar clientes", str(exc))]
            page.update()

    def open_form(client=None):
        nombre = field("Nombre completo", value=client["nombre"] if client else "")
        email = field("Email", value=client["email"] if client else "")
        telefono = field("Telefono", value=client["telefono"] if client else "")
        rfc = field("RFC", value=(client.get("rfc") or "") if client else "")

        def save(_):
            try:
                nombre_value = (nombre.value or "").strip()
                email_value = (email.value or "").strip()
                telefono_value = (telefono.value or "").strip()
                rfc_value = (rfc.value or "").strip() or None

                if not nombre_value or not email_value or not telefono_value:
                    raise ValueError("Captura nombre, email y telefono.")

                payload = {
                    "nombre": nombre_value,
                    "email": email_value,
                    "telefono": telefono_value,
                    "rfc": rfc_value,
                }

                if client:
                    state.api.put(f"clientes/{client['id']}/", json=payload)
                    show_message(page, "Cliente actualizado correctamente.")
                else:
                    state.api.post("clientes/", json=payload)
                    show_message(page, "Cliente creado correctamente.")
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
            title=ft.Text("Editar cliente" if client else "Nuevo cliente"),
            content=ft.Container(width=420, content=ft.Column([nombre, email, telefono, rfc], spacing=14, tight=True)),
            actions=[secondary_button("Cancelar", lambda e: close_dialog(page, dialog)), primary_button("Guardar", save)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        open_dialog(page, dialog)

    def confirm_delete(client):
        def remove(_):
            try:
                state.api.delete(f"clientes/{client['id']}/")
                show_message(page, "Cliente eliminado correctamente.")
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
            title=ft.Text("Eliminar cliente"),
            content=ft.Text(f"Se eliminara '{client['nombre']}'."),
            actions=[secondary_button("Cancelar", lambda e: close_dialog(page, dialog)), primary_button("Eliminar", remove, icon=ft.Icons.DELETE_ROUNDED)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        open_dialog(page, dialog)

    search_input.on_change = lambda e: render()
    load_data()

    return ft.Column(
        [
            ft.Row([page_header("Clientes", "Gestiona la base de clientes del sistema."), primary_button("Nuevo cliente", lambda e: open_form(), icon=ft.Icons.PERSON_ADD_ROUNDED)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            app_card(search_input),
            content_column,
        ],
        spacing=20,
        expand=True,
        scroll=ft.ScrollMode.ALWAYS,
    )
