import flet as ft

from app.components.ui import app_card, field, primary_button, show_message
from app.theme import BACKGROUND, GOLD, NAVY, TEXT, TEXT_SOFT, brand_gradient


def build_login_view(page: ft.Page, state):
    username_field = field("Usuario", expand=True)
    password_field = field("Contrasena", password=True, expand=True)
    status_text = ft.Text("", color=TEXT_SOFT, size=12)

    def submit(_):
        username = (username_field.value or "").strip()
        password = password_field.value or ""

        if not username or not password:
            show_message(page, "Captura usuario y contrasena.", error=True)
            return

        login_button.disabled = True
        status_text.value = "Validando credenciales..."
        page.update()

        try:
            state.login(username, password)
            page.go("/dashboard")
        except Exception as exc:
            status_text.value = str(exc)
            show_message(page, str(exc), error=True)
        finally:
            login_button.disabled = False
            page.update()

    login_button = primary_button("Entrar", submit, icon=ft.Icons.LOGIN_ROUNDED, expand=True)

    brand_panel = ft.Container(
        gradient=brand_gradient(),
        border_radius=24,
        padding=36,
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text("VP", size=26, weight=ft.FontWeight.W_800, color=NAVY),
                    bgcolor=GOLD,
                    width=64,
                    height=64,
                    border_radius=18,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Text("Vantti POS", size=34, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                ft.Text(
                    "Plataforma modular para ventas, clientes, inventario y control operativo.",
                    size=15,
                    color=ft.Colors.with_opacity(0.86, ft.Colors.WHITE),
                ),
                ft.Container(height=16),
                ft.Text("Incluye", size=13, weight=ft.FontWeight.W_600, color=GOLD),
                ft.Text("API REST segura", color=ft.Colors.WHITE),
                ft.Text("Autenticacion JWT", color=ft.Colors.WHITE),
                ft.Text("Dashboard con datos reales", color=ft.Colors.WHITE),
                ft.Text("Frontend Flet en una sola app", color=ft.Colors.WHITE),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        col={"xs": 12, "md": 6},
    )

    login_card = app_card(
        ft.Column(
            [
                ft.Text("Iniciar sesion", size=28, weight=ft.FontWeight.W_700, color=TEXT),
                ft.Text("Accede con un usuario real de Django.", size=13, color=TEXT_SOFT),
                ft.Container(height=8),
                username_field,
                password_field,
                status_text,
                login_button,
            ],
            spacing=16,
        ),
        padding=32,
    )

    return ft.View(
        route="/login",
        bgcolor=BACKGROUND,
        padding=0,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                padding=40,
                content=ft.Container(
                    width=1080,
                    content=ft.ResponsiveRow(
                        [
                            brand_panel,
                            ft.Container(content=login_card, col={"xs": 12, "md": 6}, alignment=ft.Alignment(0, 0)),
                        ],
                        run_spacing=24,
                    ),
                ),
            )
        ],
    )
