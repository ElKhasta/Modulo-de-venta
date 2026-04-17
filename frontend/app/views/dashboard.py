import flet as ft

from app.components.ui import app_card, empty_state, metric_card, money, page_header, show_message, status_pill
from app.services.api import AuthenticationError, ApiError
from app.theme import GOLD, INFO, NAVY, SUCCESS, TEXT, TEXT_SOFT


def build_dashboard_view(page: ft.Page, state):
    try:
        summary = state.api.get("dashboard/summary/") or {}
    except AuthenticationError as exc:
        state.logout()
        show_message(page, str(exc), error=True)
        page.go("/login")
        return ft.Column([])
    except ApiError as exc:
        return ft.Column(
            [
                page_header("Dashboard", "No fue posible cargar el resumen."),
                empty_state("Error de conexion", str(exc)),
            ],
            spacing=20,
        )

    metric_row = ft.ResponsiveRow(
        [
            ft.Container(content=metric_card("Productos", str(summary.get("total_productos", 0)), ft.Icons.INVENTORY_2_ROUNDED, NAVY), col={"xs": 12, "sm": 6, "xl": 3}),
            ft.Container(content=metric_card("Clientes", str(summary.get("total_clientes", 0)), ft.Icons.GROUP_ROUNDED, INFO), col={"xs": 12, "sm": 6, "xl": 3}),
            ft.Container(content=metric_card("Ventas", str(summary.get("total_ventas", 0)), ft.Icons.POINT_OF_SALE_ROUNDED, GOLD), col={"xs": 12, "sm": 6, "xl": 3}),
            ft.Container(content=metric_card("Ingresos", money(summary.get("monto_total", 0)), ft.Icons.ATTACH_MONEY_ROUNDED, SUCCESS), col={"xs": 12, "sm": 6, "xl": 3}),
        ],
        run_spacing=16,
    )

    recent_sales = summary.get("ventas_recientes", [])
    low_stock = summary.get("productos_bajo_stock", [])

    recent_sales_controls = []
    for sale in recent_sales:
        recent_sales_controls.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(f"Venta #{sale['id']}", size=14, weight=ft.FontWeight.W_600, color=TEXT),
                                ft.Text(sale.get("cliente", "Publico general"), size=12, color=TEXT_SOFT),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        ft.Text(money(sale.get("total", 0)), size=16, weight=ft.FontWeight.W_700, color=SUCCESS),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                border_radius=14,
                bgcolor=ft.Colors.with_opacity(0.05, NAVY),
            )
        )

    low_stock_controls = []
    for product in low_stock:
        tone = "error" if int(product.get("stock", 0)) == 0 else "warning"
        low_stock_controls.append(
            ft.Row(
                [
                    ft.Text(product.get("nombre", "Producto"), color=TEXT, size=14, expand=True),
                    status_pill(f"Stock {product.get('stock', 0)}", tone),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

    if not recent_sales_controls:
        recent_sales_controls.append(ft.Text("Todavia no hay ventas registradas.", color=TEXT_SOFT))
    if not low_stock_controls:
        low_stock_controls.append(ft.Text("No hay productos con stock bajo.", color=TEXT_SOFT))

    sections = ft.ResponsiveRow(
        [
            ft.Container(
                content=app_card(
                    ft.Column(
                        [
                            ft.Text("Ventas recientes", size=18, weight=ft.FontWeight.W_700, color=TEXT),
                            ft.Text("Resumen rapido de las ultimas operaciones.", size=12, color=TEXT_SOFT),
                            ft.Divider(height=18, color=ft.Colors.TRANSPARENT),
                            ft.Column(recent_sales_controls, spacing=10),
                        ],
                        spacing=0,
                    ),
                    expand=True,
                ),
                col={"xs": 12, "lg": 7},
            ),
            ft.Container(
                content=app_card(
                    ft.Column(
                        [
                            ft.Text("Stock critico", size=18, weight=ft.FontWeight.W_700, color=TEXT),
                            ft.Text("Productos que requieren atencion inmediata.", size=12, color=TEXT_SOFT),
                            ft.Divider(height=18, color=ft.Colors.TRANSPARENT),
                            ft.Column(low_stock_controls, spacing=10),
                        ],
                        spacing=0,
                    ),
                    expand=True,
                ),
                col={"xs": 12, "lg": 5},
            ),
        ],
        run_spacing=16,
    )

    return ft.Column(
        [page_header("Dashboard", "Metricas centrales del sistema de ventas."), metric_row, sections],
        spacing=20,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
