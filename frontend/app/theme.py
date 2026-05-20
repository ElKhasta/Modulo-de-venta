import flet as ft


NAVY = "#003366"
NAVY_DARK = "#00264D"
GOLD = "#C9A227"
GOLD_SOFT = "#E6D7A6"
BACKGROUND = "#F4F6F8"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#E9EEF5"
TEXT = "#1E293B"
TEXT_SOFT = "#5B6573"
BORDER = "#D5DDE6"
SUCCESS = "#2E7D32"
ERROR = "#B3261E"
WARNING = "#A16207"
INFO = "#0F766E"
SIDEBAR_TEXT = "#F8FAFC"

CARD_SHADOW = ft.BoxShadow(
    spread_radius=0,
    blur_radius=24,
    color=ft.Colors.with_opacity(0.08, "#0F172A"),
    offset=ft.Offset(0, 8),
)


def build_theme() -> ft.Theme:
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=NAVY,
            secondary=GOLD,
            surface=SURFACE,
            error=ERROR,
        ),
        font_family="Segoe UI",
    )


def brand_gradient() -> ft.LinearGradient:
    return ft.LinearGradient(
        begin=ft.Alignment(-1, -1),
        end=ft.Alignment(1, 1),
        colors=[NAVY_DARK, NAVY],
    )
