import flet as ft

from app.components.ui import app_card
from app.theme import BACKGROUND, BORDER, GOLD, NAVY, SIDEBAR_TEXT, SURFACE, TEXT, TEXT_SOFT


NAV_ITEMS = [
    {"route": "/dashboard", "label": "Dashboard", "icon": ft.Icons.DASHBOARD_ROUNDED},
    {"route": "/productos", "label": "Productos", "icon": ft.Icons.INVENTORY_2_ROUNDED},
    {"route": "/clientes", "label": "Clientes", "icon": ft.Icons.GROUP_ROUNDED},
    {"route": "/ventas", "label": "Ventas", "icon": ft.Icons.POINT_OF_SALE_ROUNDED},
    {"route": "/scanner-movil", "label": "Escáner Móvil", "icon": ft.Icons.QR_CODE_SCANNER_ROUNDED},
]


def build_shell_view(page: ft.Page, state, route: str, content):
    selected_index = next((index for index, item in enumerate(NAV_ITEMS) if item["route"] == route), 0)
    
    is_mobile = page.width < 768

    def on_nav_change(event):
        page.go(NAV_ITEMS[event.control.selected_index]["route"])

    def on_logout(_):
        state.logout()
        page.go("/login")

    # Ocultar barra lateral en móviles para dar espacio al contenido
    rail = ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=104,
        min_extended_width=200,
        bgcolor=NAVY,
        visible=not is_mobile,  # Oculto en celulares
        indicator_color=ft.Colors.with_opacity(0.22, GOLD),
        on_change=on_nav_change,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icon(item["icon"], color=SIDEBAR_TEXT),
                selected_icon=ft.Icon(item["icon"], color=GOLD),
                label=ft.Text(item["label"], color=SIDEBAR_TEXT),
            )
            for item in NAV_ITEMS
        ],
        trailing=ft.Container(
            content=ft.Column(
                [
                    ft.Divider(color=ft.Colors.with_opacity(0.12, SIDEBAR_TEXT)),
                    ft.TextButton(
                        "Cerrar",
                        icon=ft.Icons.LOGOUT_ROUNDED,
                        icon_color=GOLD,
                        style=ft.ButtonStyle(color={ft.ControlState.DEFAULT: SIDEBAR_TEXT}),
                        on_click=on_logout,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(bottom=16),
        ),
    )

    user_name = (state.user or {}).get("username", "Usuario")
    
    # Cabecera responsiva: reduce el padding y oculta la tarjeta del usuario en celular para ahorrar espacio
    header = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Vantti POS", size=20 if is_mobile else 22, weight=ft.FontWeight.W_700, color=TEXT),
                        ft.Text("POS Multiplataforma" if is_mobile else "Sistema de ventas con Django REST y Flet", size=11 if is_mobile else 13, color=TEXT_SOFT),
                    ],
                    spacing=2,
                ),
                ft.Container(expand=True),
                # Ocultar tarjeta de usuario en celular para evitar que se corte la cabecera
                ft.Container(
                    content=app_card(
                        ft.Row(
                            [
                                ft.CircleAvatar(bgcolor=NAVY, color=ft.Colors.WHITE, content=ft.Text(user_name[:1].upper())),
                                ft.Column(
                                    [
                                        ft.Text(user_name, size=14, weight=ft.FontWeight.W_600, color=TEXT),
                                        ft.Text("Sesión", size=11, color=TEXT_SOFT),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=10,
                    ),
                    visible=not is_mobile
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=16 if is_mobile else 28, vertical=12 if is_mobile else 20),
        bgcolor=SURFACE,
        border=ft.Border.only(bottom=ft.BorderSide(1, BORDER)),
    )

    # Ancho y padding responsivo para adaptarse a pantallas móviles y de escritorio
    content_wrapper = ft.Container(
        content=content,
        padding=12 if is_mobile else 28,
        expand=True,
    )

    # Permitir deslizamiento vertical fluido nativo para dispositivos móviles
    scrollable_content = ft.Column(
        [content_wrapper],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    body = ft.Row(
        [
            rail,
            ft.VerticalDivider(width=1, color=BORDER, visible=not is_mobile),
            ft.Container(
                content=scrollable_content,
                bgcolor=BACKGROUND,
                expand=True,
            ),
        ],
        spacing=0,
        expand=True,
    )

    # Barra de navegación inferior móvil para una experiencia táctil tipo app nativa (iOS/Android)
    bottom_nav = None
    if is_mobile:
        bottom_nav = ft.NavigationBar(
            selected_index=selected_index,
            bgcolor=NAVY,
            indicator_color=ft.Colors.with_opacity(0.22, GOLD),
            on_change=on_nav_change,
            destinations=[
                ft.NavigationBarDestination(
                    icon=item["icon"],
                    label=item["label"]
                )
                for item in NAV_ITEMS
            ]
        )

    return ft.View(
        route=route, 
        padding=0, 
        bgcolor=BACKGROUND, 
        controls=[ft.Column([header, body], spacing=0, expand=True)],
        navigation_bar=bottom_nav
    )
