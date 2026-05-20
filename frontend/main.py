import flet as ft

from app.components.shell import build_shell_view
from app.state.session import AppState
from app.theme import BACKGROUND, build_theme
from app.views import PROTECTED_ROUTES, build_login_view


DEFAULT_ROUTE = "/dashboard"


def main(page: ft.Page):
    page.title = "Vantti POS"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = build_theme()
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.window.width = 1440
    page.window.height = 900
    page.window.min_width = 1120
    page.window.min_height = 720

    state = AppState(page)

    def route_change(_):
        route = page.route or DEFAULT_ROUTE

        if route == "/login" and state.restore_session():
            page.go(DEFAULT_ROUTE)
            return

        if route in PROTECTED_ROUTES and not state.restore_session():
            page.go("/login")
            return

        if route == "/login":
            page.views = [build_login_view(page, state)]
        else:
            builder = PROTECTED_ROUTES.get(route, PROTECTED_ROUTES[DEFAULT_ROUTE])
            if route not in PROTECTED_ROUTES:
                route = DEFAULT_ROUTE
            content = builder(page, state)
            page.views = [build_shell_view(page, state, route, content)]
        page.update()

    def view_pop(_):
        if len(page.views) > 1:
            page.views.pop()
        target_route = page.views[-1].route if page.views else "/login"
        page.go(target_route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go(DEFAULT_ROUTE if state.restore_session() else "/login")


if __name__ == "__main__":
    ft.app(target=main)
