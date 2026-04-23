from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuthLoginView,
    AuthRefreshView,
    ClienteViewSet,
    CurrentUserView,
    InventoryMovementView,
    InventoryResolveScanView,
    ProductoViewSet,
    VentaViewSet,
)


router = DefaultRouter()
router.register("productos", ProductoViewSet, basename="producto")
router.register("clientes", ClienteViewSet, basename="cliente")
router.register("ventas", VentaViewSet, basename="venta")


app_name = "api"
urlpatterns = [
    path("auth/login/", AuthLoginView.as_view(), name="auth-login"),
    path("auth/refresh/", AuthRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", CurrentUserView.as_view(), name="auth-me"),
    path("login/", AuthLoginView.as_view(), name="compat-login"),
    path("inventario/resolve-scan/", InventoryResolveScanView.as_view(), name="inventario-resolve-scan"),
    path("inventario/movimientos/", InventoryMovementView.as_view(), name="inventario-movimientos"),
    path("", include(router.urls)),
]
