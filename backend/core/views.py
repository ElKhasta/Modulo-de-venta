from django.shortcuts import render
from .ia_utils import obtener_recomendacion_vania

def catalogo_VANTTI(request):
    # Detectamos la sección. Si no hay, por defecto es Queso Oaxaca.
    seccion = request.GET.get('seccion', 'Queso Oaxaca')
    
    # Llamamos a vanIA solo para ese producto
    recomendacion = obtener_recomendacion_vania(seccion)
    
    return render(request, 'detalle.html', {
        'producto_activo': seccion,
        'sugerencia': recomendacion
    })