from .clientes import build_clientes_view
from .dashboard import build_dashboard_view
from .login import build_login_view
from .productos import build_productos_view
from .ventas import build_ventas_view


PROTECTED_ROUTES = {
    "/dashboard": build_dashboard_view,
    "/productos": build_productos_view,
    "/clientes": build_clientes_view,
    "/ventas": build_ventas_view,
}

__all__ = ["PROTECTED_ROUTES", "build_login_view"]
