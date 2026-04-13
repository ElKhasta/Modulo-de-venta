from rest_framework import viewsets, status
from rest_framework.decorators import api_view # <--- Necesario para el login
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth import authenticate # <--- El motor de validación de Django
from .models import Producto, Venta, DetalleVenta, Cliente
from .serializers import ProductoSerializer, VentaSerializer, ClienteSerializer

# --- VISTAS DE AUTENTICACIÓN ---

@api_view(['POST'])
def login_view(request):
    """
    Endpoint para que Vantti valide usuarios reales en Django/Supabase.
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    # Authenticate revisa contra la tabla auth_user de tu BD
    user = authenticate(username=username, password=password)
    
    if user is not None:
        return Response({
            "message": "Login exitoso",
            "user": user.username,
            "id": user.id
        }, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Usuario o contraseña incorrectos"}, status=status.HTTP_401_UNAUTHORIZED)


# --- VIEWSETS EXISTENTES ---

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        productos_data = data.get('productos', [])
        cliente_id = data.get('cliente_id')

        if not productos_data:
            return Response({"error": "No hay productos en la venta"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 1. Buscar el cliente
                cliente_obj = None
                if cliente_id:
                    try:
                        cliente_obj = Cliente.objects.get(id=cliente_id)
                    except Cliente.DoesNotExist:
                        raise ValueError("El cliente seleccionado no existe.")

                # 2. Crear cabecera
                nueva_venta = Venta.objects.create(
                    total=data['total'],
                    cliente=cliente_obj
                )
                
                # 3. Procesar productos
                for item in productos_data:
                    producto = Producto.objects.select_for_update().get(id=item['id'])
                    cantidad_vendida = item['cantidad']
                    
                    if producto.stock < cantidad_vendida:
                        raise ValueError(f"Stock insuficiente para {producto.nombre}.")

                    # 4. Crear detalle
                    DetalleVenta.objects.create(
                        venta=nueva_venta,
                        producto=producto,
                        cantidad=cantidad_vendida,
                        precio_historico=item['precio']
                    )
                    
                    # 5. Descontar stock
                    producto.stock -= cantidad_vendida
                    producto.save()
                
                return Response({"message": "Venta realizada con éxito"}, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error interno: {e}")
            return Response({"error": "Error inesperado en el servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
