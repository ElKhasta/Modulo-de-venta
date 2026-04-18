from django.shortcuts import render
from .ia_utils import obtener_recomendaciones_multiples

def buscador_VANTTI(request):
    # Capturamos lo que el usuario escribe en el buscador (por defecto Queso)
    query = request.GET.get('q', '')
    sugerencias = ""
    
    if query:
        sugerencias = obtener_recommendaciones_multiples(query)
    
    return render(request, 'detalle.html', {
        'busqueda': query,
        'sugerencias': sugerencias
    })