from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Cliente, DetalleVenta, MovimientoInventario, Producto, Venta
from .services import create_sale, update_sale


class CurrentUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = CurrentUserSerializer(self.user).data
        return data


class ScanResolveSerializer(serializers.Serializer):
    codigo_barras = serializers.CharField(max_length=50)

    def validate_codigo_barras(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("El codigo_barras es obligatorio.")
        return cleaned


class InventoryMovementRequestSerializer(serializers.Serializer):
    codigo_barras = serializers.CharField(max_length=50)
    tipo = serializers.CharField(required=False)
    tipo_movimiento = serializers.CharField(required=False, write_only=True)
    cantidad = serializers.IntegerField(min_value=0)
    nota = serializers.CharField(required=False, allow_blank=True, default="")
    origen = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_codigo_barras(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("El codigo_barras es obligatorio.")
        return cleaned

    def validate(self, attrs):
        tipo = attrs.get("tipo") or attrs.get("tipo_movimiento")
        if not tipo:
            raise serializers.ValidationError({"tipo": "El tipo de movimiento es obligatorio."})

        tipo = tipo.strip().lower()
        tipos_validos = {
            MovimientoInventario.TIPO_INCREMENTAR,
            MovimientoInventario.TIPO_DISMINUIR,
            MovimientoInventario.TIPO_ALTA_PRODUCTO,
            MovimientoInventario.TIPO_BAJA_LOGICA,
        }
        if tipo not in tipos_validos:
            raise serializers.ValidationError({"tipo": "Tipo de movimiento no soportado."})

        cantidad = attrs["cantidad"]
        if tipo in {
            MovimientoInventario.TIPO_INCREMENTAR,
            MovimientoInventario.TIPO_DISMINUIR,
            MovimientoInventario.TIPO_ALTA_PRODUCTO,
        } and cantidad <= 0:
            raise serializers.ValidationError({"cantidad": "La cantidad debe ser mayor a cero."})

        attrs["tipo"] = tipo
        attrs.pop("tipo_movimiento", None)
        return attrs


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ["id", "nombre", "email", "telefono", "rfc"]


class ProductoSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ["id", "codigo_barras", "nombre", "precio", "stock", "is_low_stock"]

    def get_is_low_stock(self, obj):
        return obj.stock <= 5


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source="producto.nombre")
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = DetalleVenta
        fields = [
            "id",
            "producto",
            "producto_nombre",
            "cantidad",
            "precio_historico",
            "subtotal",
        ]


class DetalleVentaInputSerializer(serializers.Serializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    cantidad = serializers.IntegerField(min_value=1)
    precio_historico = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class VentaReadSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.SerializerMethodField()
    detalles = DetalleVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = ["id", "fecha", "total", "cliente", "cliente_nombre", "detalles"]

    def get_cliente_nombre(self, obj):
        return obj.cliente.nombre if obj.cliente else "Publico general"


class VentaWriteSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        allow_null=True,
        required=False,
    )
    detalles = DetalleVentaInputSerializer(many=True)

    class Meta:
        model = Venta
        fields = ["id", "cliente", "detalles"]

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError("Debes agregar al menos un producto a la venta.")
        return value

    def _request_user(self):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user
        return None

    def create(self, validated_data):
        detalles = validated_data.pop("detalles")
        cliente = validated_data.get("cliente")
        return create_sale(cliente=cliente, detalles=detalles, usuario=self._request_user())

    def update(self, instance, validated_data):
        detalles = validated_data.pop("detalles")
        cliente = validated_data.get("cliente")
        return update_sale(instance, cliente=cliente, detalles=detalles, usuario=self._request_user())
