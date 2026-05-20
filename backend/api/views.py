from decimal import Decimal

from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Cliente, Producto, Venta
from .serializers import (
    ClienteSerializer,
    CurrentUserSerializer,
    DashboardProductSerializer,
    DashboardSaleSerializer,
    LoginSerializer,
    ProductoSerializer,
    VentaReadSerializer,
    VentaWriteSerializer,
)
from .services import delete_sale


class AuthLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class AuthRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class CurrentUserView(APIView):
    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class DashboardSummaryView(APIView):
    def get(self, request):
        sales_queryset = Venta.objects.select_related("cliente")
        summary = {
            "total_productos": Producto.objects.count(),
            "total_clientes": Cliente.objects.count(),
            "total_ventas": sales_queryset.count(),
            "monto_total": sales_queryset.aggregate(
                total=Coalesce(Sum("total"), Decimal("0.00"))
            )["total"],
            "ventas_recientes": DashboardSaleSerializer(
                [
                    {
                        "id": venta.id,
                        "fecha": venta.fecha,
                        "total": venta.total,
                        "cliente": venta.cliente.nombre if venta.cliente else "Publico general",
                    }
                    for venta in sales_queryset[:5]
                ],
                many=True,
            ).data,
            "productos_bajo_stock": DashboardProductSerializer(
                list(Producto.objects.filter(stock__lte=5).values("id", "nombre", "stock")[:5]),
                many=True,
            ).data,
        }
        return Response(summary)


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["nombre", "codigo_barras"]
    ordering_fields = ["nombre", "precio", "stock"]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "No se puede eliminar este producto porque ya forma parte de una venta."},
                status=status.HTTP_409_CONFLICT,
            )


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["nombre", "email", "telefono", "rfc"]
    ordering_fields = ["nombre", "email"]


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.select_related("cliente").prefetch_related("detalles__producto")
    filter_backends = [OrderingFilter]
    ordering_fields = ["fecha", "total"]
    http_method_names = ["get", "post", "put", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action in {"create", "update"}:
            return VentaWriteSerializer
        return VentaReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        venta = serializer.save()
        return Response(VentaReadSerializer(venta).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        venta = serializer.save()
        return Response(VentaReadSerializer(venta).data)

    def destroy(self, request, *args, **kwargs):
        venta = self.get_object()
        delete_sale(venta)
        return Response(status=status.HTTP_204_NO_CONTENT)
