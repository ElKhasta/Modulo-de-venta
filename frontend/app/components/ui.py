import flet as ft

from app.theme import BACKGROUND, BORDER, CARD_SHADOW, ERROR, GOLD, INFO, NAVY, SUCCESS, SURFACE, TEXT, TEXT_SOFT, WARNING


STATUS_COLORS = {
    "info": INFO,
    "success": SUCCESS,
    "warning": WARNING,
    "error": ERROR,
}


def money(value) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def show_message(page: ft.Page, message: str, *, error: bool = False) -> None:
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=ERROR if error else SUCCESS,
        duration=3500,
    )
    page.snack_bar.open = True
    page.update()


def app_card(content, *, expand: bool = False, padding: int = 20, height=None):
    return ft.Container(
        content=content,
        bgcolor=SURFACE,
        border_radius=20,
        border=ft.border.all(1, BORDER),
        padding=padding,
        expand=expand,
        height=height,
        shadow=CARD_SHADOW,
    )


def page_header(title: str, subtitle: str | None = None):
    controls = [ft.Text(title, size=28, weight=ft.FontWeight.W_700, color=TEXT)]
    if subtitle:
        controls.append(ft.Text(subtitle, size=13, color=TEXT_SOFT))
    return ft.Column(controls, spacing=4)


def primary_button(text: str, on_click, *, icon=None, expand: bool = False, disabled: bool = False):
    return ft.FilledButton(
        text,
        icon=icon,
        on_click=on_click,
        disabled=disabled,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: GOLD},
            color={ft.ControlState.DEFAULT: NAVY},
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        expand=expand,
    )


def secondary_button(text: str, on_click, *, icon=None, expand: bool = False):
    return ft.OutlinedButton(
        text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, BORDER)},
            color={ft.ControlState.DEFAULT: TEXT},
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        expand=expand,
    )


def metric_card(title: str, value: str, icon, accent: str):
    return app_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icon, color=accent, size=26),
                        ft.Text(title, size=12, color=TEXT_SOFT),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(value, size=30, weight=ft.FontWeight.W_700, color=TEXT),
            ],
            spacing=12,
        ),
        expand=True,
    )


def status_pill(label: str, tone: str = "info"):
    color = STATUS_COLORS.get(tone, INFO)
    return ft.Container(
        content=ft.Text(label, size=11, color=color, weight=ft.FontWeight.W_600),
        bgcolor=ft.Colors.with_opacity(0.08, color),
        border=ft.border.all(1, ft.Colors.with_opacity(0.25, color)),
        border_radius=999,
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
    )


def empty_state(title: str, subtitle: str):
    return app_card(
        ft.Column(
            [
                ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=TEXT_SOFT, size=38),
                ft.Text(title, size=18, weight=ft.FontWeight.W_600, color=TEXT),
                ft.Text(subtitle, size=13, color=TEXT_SOFT, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        padding=28,
    )


def field(label: str, *, value: str = "", password: bool = False, multiline: bool = False, width=None, expand: bool = False):
    return ft.TextField(
        label=label,
        value=value,
        password=password,
        can_reveal_password=password,
        multiline=multiline,
        border_radius=14,
        border_color=BORDER,
        focused_border_color=NAVY,
        label_style=ft.TextStyle(color=TEXT_SOFT),
        text_style=ft.TextStyle(color=TEXT),
        width=width,
        expand=expand,
        filled=True,
        bgcolor=BACKGROUND,
    )
