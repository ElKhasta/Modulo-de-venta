from rest_framework import serializers
from .models import Producto, Venta, DetalleVenta

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__' # Exponemos ID, nombre, stock y precio

class DetalleVentaSerializer(serializers.ModelSerializer):
    # Agregamos el nombre del producto para que el Front no vea solo un ID numérico
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetalleVenta
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_historico', 'subtotal']

class VentaSerializer(serializers.ModelSerializer):
    # Esto anida los detalles dentro de la venta (Relación Maestro-Detalle)
    detalles = DetalleVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = ['id', 'fecha', 'total', 'detalles']
        