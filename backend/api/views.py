import json
from decimal import Decimal

from django.shortcuts import render
from django.db import transaction
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def html_scanner(request):
    return render(request, "scanner.html")


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


PENDING_REMOTE_SCANS = []


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
    lookup_field = "codigo_barras"
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

    @action(detail=False, methods=["post"])
    def procesar_escaneo(self, request):
        """
        Ingesta de hardware para códigos escaneados (QR o código de barras).
        - Deserializa JSON para códigos QR de fidelización.
        - Parsea códigos GS1 (prefijo "2") para productos con peso/precio variable.
        - Busca por código de barras estándar en otros casos.
        """
        codigo = request.data.get("codigo")
        if not codigo:
            return Response(
                {"detail": "El campo 'codigo' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        codigo_str = str(codigo).strip()

        # 1. Intentar parsear como código QR de fidelización (JSON)
        try:
            data_qr = json.loads(codigo_str)
            if isinstance(data_qr, dict):
                email = data_qr.get("email")
                telefono = data_qr.get("telefono")
                rfc = data_qr.get("rfc")
                cliente_id = data_qr.get("cliente_id")

                cliente = None
                if cliente_id:
                    cliente = Cliente.objects.filter(id=cliente_id).first()
                if not cliente and email:
                    cliente = Cliente.objects.filter(email=email).first()
                if not cliente and telefono:
                    cliente = Cliente.objects.filter(telefono=telefono).first()
                if not cliente and rfc:
                    cliente = Cliente.objects.filter(rfc=rfc).first()

                if cliente:
                    return Response({
                        "tipo": "cliente",
                        "datos": ClienteSerializer(cliente).data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "tipo": "cliente_no_encontrado",
                        "detail": "Código QR válido de fidelización, pero el cliente no fue encontrado."
                    }, status=status.HTTP_404_NOT_FOUND)
        except (json.JSONDecodeError, TypeError):
            pass  # Si no es JSON, continuamos con la búsqueda de productos

        # 2. Intentar parsear como código GS1 de peso/precio variable (prefijo "2", longitud 13)
        if codigo_str.startswith("2") and len(codigo_str) == 13 and codigo_str.isdigit():
            # Extraemos el SKU base (posiciones 1 a 6 o 7 del EAN-13, ej: primeros 7 caracteres)
            sku_candidato_7 = codigo_str[:7]
            sku_candidato_6 = codigo_str[:6]

            # Buscamos el producto en base de datos que coincida
            producto = Producto.objects.filter(codigo_barras=sku_candidato_7).first()
            if not producto:
                producto = Producto.objects.filter(codigo_barras=sku_candidato_6).first()
            if not producto:
                # Búsqueda fallback flexible por prefijo de código de barras
                for p in Producto.objects.filter(codigo_barras__startswith="2"):
                    if codigo_str.startswith(p.codigo_barras):
                        producto = p
                        break

            if producto:
                # Extraemos el precio del código escaneado (dígitos 7 a 11, longitud 5)
                # Ej: 2001234003503 -> SKU = 2001234, Precio = 00350 (3.50), Control = 3
                try:
                    precio_centavos = int(codigo_str[7:12])
                    precio_dinamico = Decimal(precio_centavos) / Decimal("100.00")
                except (ValueError, IndexError):
                    precio_dinamico = producto.precio

                datos_producto = ProductoSerializer(producto).data
                datos_producto["precio"] = f"{precio_dinamico:.2f}"
                datos_producto["es_peso_variable"] = True

                return Response({
                    "tipo": "producto",
                    "datos": datos_producto
                }, status=status.HTTP_200_OK)

        # 3. Búsqueda directa por código de barras estándar
        producto = Producto.objects.filter(codigo_barras=codigo_str).first()
        if producto:
            return Response({
                "tipo": "producto",
                "datos": ProductoSerializer(producto).data
            }, status=status.HTTP_200_OK)

        return Response(
            {"detail": f"Código '{codigo_str}' no coincide con ningún producto o cliente registrado."},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=["post"], url_path="descontar-stock")
    @transaction.atomic
    def descontar_stock(self, request, codigo_barras=None):
        """
        Descuenta inventario del producto de forma transaccional usando select_for_update.
        Previene condiciones de carrera y dobles escaneos.
        """
        # Usamos select_for_update para bloquear la fila del producto hasta finalizar la transacción
        try:
            producto = Producto.objects.select_for_update().get(codigo_barras=codigo_barras)
        except Producto.DoesNotExist:
            return Response(
                {"detail": "El producto especificado no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            cantidad = int(request.data.get("cantidad", 1))
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            return Response(
                {"detail": "La cantidad a descontar debe ser un entero positivo mayor a cero."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if producto.stock < cantidad:
            return Response(
                {"detail": f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Descontar stock de forma segura
        producto.stock -= cantidad
        producto.save(update_fields=["stock"])

        return Response(ProductoSerializer(producto).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def escanear_remoto(self, request):
        """
        Recibe un codigo escaneado de forma remota (desde la version movil del POS).
        Es publico (AllowAny) porque el celular no tiene sesion JWT.
        """
        codigo = request.data.get("codigo")
        if not codigo:
            return Response(
                {"detail": "El campo 'codigo' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        global PENDING_REMOTE_SCANS
        PENDING_REMOTE_SCANS.append(str(codigo).strip())
        if len(PENDING_REMOTE_SCANS) > 100:
            PENDING_REMOTE_SCANS.pop(0)

        return Response(
            {"status": "success", "message": f"Codigo '{codigo}' encolado remotamente."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"])
    def obtener_escaneos_remotos(self, request):
        """
        Obtiene y limpia la lista de escaneos remotos pendientes para el cliente de escritorio.
        """
        global PENDING_REMOTE_SCANS
        escaneos = list(PENDING_REMOTE_SCANS)
        PENDING_REMOTE_SCANS.clear()
        return Response({"escaneos": escaneos}, status=status.HTTP_200_OK)



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
