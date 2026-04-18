from django.shortcuts import render
# Importamos la función para hablar con vanIA (Ollama)
try:
    from .ia_utils import obtener_recomendacion_vania
except ImportError:
    # Si por algo no encuentra el archivo, definimos una función de respaldo
    def obtener_recomendacion_vania(p): return "vanIA está cargando..."

def prueba_vania(request):
    # Producto ficticio para que NO necesitemos el archivo models.py
    producto = {
        'nombre': 'Queso Oaxaca VANTTI',
        'descripcion': 'Queso artesanal de hebra, orgullo de Cuautitlán.',
        'precio': 150.00
    }
    
    # Llamada a la IA
    sugerencia = obtener_recomendacion_vania(producto['nombre'])
    
    return render(request, 'detalle.html', {'producto': producto, 'sugerencia': sugerencia})