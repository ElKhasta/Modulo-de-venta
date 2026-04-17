import flet as ft

from app.components.ui import app_card
from app.theme import BACKGROUND, BORDER, GOLD, NAVY, SIDEBAR_TEXT, SURFACE, TEXT, TEXT_SOFT


NAV_ITEMS = [
    {"route": "/dashboard", "label": "Dashboard", "icon": ft.Icons.DASHBOARD_ROUNDED},
    {"route": "/productos", "label": "Productos", "icon": ft.Icons.INVENTORY_2_ROUNDED},
    {"route": "/clientes", "label": "Clientes", "icon": ft.Icons.GROUP_ROUNDED},
    {"route": "/ventas", "label": "Ventas", "icon": ft.Icons.POINT_OF_SALE_ROUNDED},
]


def build_shell_view(page: ft.Page, state, route: str, content):
    selected_index = next((index for index, item in enumerate(NAV_ITEMS) if item["route"] == route), 0)

    def on_nav_change(event):
        page.go(NAV_ITEMS[event.control.selected_index]["route"])

    def on_logout(_):
        state.logout()
        page.go("/login")

    rail = ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=104,
        min_extended_width=200,
        bgcolor=NAVY,
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
                        "Cerrar sesion",
                        icon=ft.Icons.LOGOUT_ROUNDED,
                        icon_color=GOLD,
                        style=ft.ButtonStyle(color={ft.ControlState.DEFAULT: SIDEBAR_TEXT}),
                        on_click=on_logout,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(bottom=16),
        ),
    )

    user_name = (state.user or {}).get("username", "Usuario")
    header = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Vantti POS", size=22, weight=ft.FontWeight.W_700, color=TEXT),
                        ft.Text("Sistema de ventas con Django REST y Flet", size=13, color=TEXT_SOFT),
                    ],
                    spacing=2,
                ),
                ft.Container(expand=True),
                app_card(
                    ft.Row(
                        [
                            ft.CircleAvatar(bgcolor=NAVY, color=ft.Colors.WHITE, content=ft.Text(user_name[:1].upper())),
                            ft.Column(
                                [
                                    ft.Text(user_name, size=14, weight=ft.FontWeight.W_600, color=TEXT),
                                    ft.Text("Sesion autenticada", size=11, color=TEXT_SOFT),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=14,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=28, vertical=20),
        bgcolor=SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
    )

    body = ft.Row(
        [
            rail,
            ft.VerticalDivider(width=1, color=BORDER),
            ft.Container(content=ft.Container(content=content, padding=28, expand=True), bgcolor=BACKGROUND, expand=True),
        ],
        spacing=0,
        expand=True,
    )

    return ft.View(route=route, padding=0, bgcolor=BACKGROUND, controls=[ft.Column([header, body], spacing=0, expand=True)])
