from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Cliente, MovimientoInventario, Producto, Venta
from .serializers import (
    ClienteSerializer,
    CurrentUserSerializer,
    InventoryMovementRequestSerializer,
    LoginSerializer,
    ProductoSerializer,
    ScanResolveSerializer,
    VentaReadSerializer,
    VentaWriteSerializer,
)
from .services import (
    apply_inventory_movement,
    create_product_with_stock_tracking,
    delete_sale,
    update_product_with_stock_tracking,
)


class AuthLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class AuthRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class CurrentUserView(APIView):
    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


def _inventory_actions_for_product(producto: Producto) -> list[str]:
    actions = [MovimientoInventario.TIPO_INCREMENTAR, MovimientoInventario.TIPO_BAJA_LOGICA]
    if producto.stock > 0:
        actions.insert(1, MovimientoInventario.TIPO_DISMINUIR)
    return actions


def _product_basic_payload(producto: Producto) -> dict:
    return {
        "id": producto.id,
        "codigo_barras": producto.codigo_barras,
        "nombre": producto.nombre,
        "precio": str(producto.precio),
        "stock": producto.stock,
    }


class InventoryResolveScanView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ScanResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        codigo_barras = serializer.validated_data["codigo_barras"]

        producto = Producto.objects.filter(codigo_barras=codigo_barras).first()
        if not producto:
            return Response(
                {
                    "existe": False,
                    "producto": None,
                    "stock_actual": None,
                    "acciones_permitidas": [MovimientoInventario.TIPO_ALTA_PRODUCTO],
                }
            )

        return Response(
            {
                "existe": True,
                "producto": _product_basic_payload(producto),
                "stock_actual": producto.stock,
                "acciones_permitidas": _inventory_actions_for_product(producto),
            }
        )


class InventoryMovementView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InventoryMovementRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        codigo_barras = serializer.validated_data["codigo_barras"]
        producto = Producto.objects.filter(codigo_barras=codigo_barras).first()
        if not producto:
            return Response(
                {
                    "detail": "Producto no encontrado para el codigo de barras proporcionado.",
                    "existe": False,
                    "acciones_permitidas": [MovimientoInventario.TIPO_ALTA_PRODUCTO],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        usuario = request.user if request.user.is_authenticated else None
        producto_actualizado, movimiento = apply_inventory_movement(
            product_id=producto.id,
            tipo_movimiento=serializer.validated_data["tipo"],
            cantidad=serializer.validated_data["cantidad"],
            usuario=usuario,
            origen=serializer.validated_data.get("origen") or "api.inventario.movimientos",
            codigo_barras_leido=codigo_barras,
            nota=serializer.validated_data.get("nota", ""),
        )

        return Response(
            {
                "producto": _product_basic_payload(producto_actualizado),
                "stock_anterior": movimiento.stock_anterior,
                "stock_nuevo": movimiento.stock_nuevo,
                "movimiento": {
                    "id": movimiento.id,
                    "tipo_movimiento": movimiento.tipo_movimiento,
                    "cantidad": movimiento.cantidad,
                    "origen": movimiento.origen,
                    "codigo_barras_leido": movimiento.codigo_barras_leido,
                    "nota": movimiento.nota,
                },
                "timestamp": movimiento.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["nombre", "codigo_barras"]
    ordering_fields = ["nombre", "precio", "stock"]

    def _request_user(self, request):
        if request.user.is_authenticated:
            return request.user
        return None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        producto = create_product_with_stock_tracking(
            validated_data=dict(serializer.validated_data),
            usuario=self._request_user(request),
            origen="api.productos.create",
        )
        return Response(self.get_serializer(producto).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        producto = update_product_with_stock_tracking(
            producto=instance,
            validated_data=dict(serializer.validated_data),
            usuario=self._request_user(request),
            origen="api.productos.update",
        )
        return Response(self.get_serializer(producto).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

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
        delete_sale(venta, usuario=request.user if request.user.is_authenticated else None)
        return Response(status=status.HTTP_204_NO_CONTENT)
