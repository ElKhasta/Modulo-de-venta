from rest_framework import serializers
from supabase_auth import User
from .models import Producto, Venta, DetalleVenta, Cliente # <--- Añadimos Cliente

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__' # Exponemos todos los campos del cliente (ID, nombre, RFC, etc.)

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__' 

class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetalleVenta
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_historico', 'subtotal']

class VentaSerializer(serializers.ModelSerializer):
    # Anidamos los detalles
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    
    # Nuevo: Agregamos información del cliente a la respuesta de la venta
    # Usamos StringRelatedField para ver el nombre o el ID directamente
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')

    class Meta:
        model = Venta
        # Añadimos 'cliente' (ID) y 'cliente_nombre' (texto) a los campos
        fields = ['id', 'fecha', 'total', 'cliente', 'cliente_nombre', 'detalles']
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'is_staff']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data) # Importante usar create_user para encriptar pass
        