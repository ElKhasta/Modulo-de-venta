from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuthLoginView,
    AuthRefreshView,
    ClienteViewSet,
    CurrentUserView,
    DashboardSummaryView,
    ProductoViewSet,
    VentaViewSet,
)


router = DefaultRouter()
router.register("productos", ProductoViewSet, basename="producto")
router.register("clientes", ClienteViewSet, basename="cliente")
router.register("ventas", VentaViewSet, basename="venta")


urlpatterns = [
    path("auth/login/", AuthLoginView.as_view(), name="auth-login"),
    path("auth/refresh/", AuthRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", CurrentUserView.as_view(), name="auth-me"),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("", include(router.urls)),
]
