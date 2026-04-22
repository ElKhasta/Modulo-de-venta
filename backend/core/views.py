from django.shortcuts import render, get_object_or_404
from .models import Producto
from .ia_utils import obtener_recomendacion_vania

def catalogo_VANTTI(request):
    # 1. Filtramos la categoría
    cat_slug = request.GET.get('categoria', 'QUESO')
    productos_filtrados = Producto.objects.filter(categoria=cat_slug)
    
    # 2. Buscamos el producto asegurándonos que pertenezca a la categoría
    prod_id = request.GET.get('id')
    if prod_id:
        producto_activo = get_object_or_404(Producto, id=prod_id, categoria=cat_slug)
    else:
        producto_activo = productos_filtrados.first()

    # 3. Solicitamos análisis a vanIA (AHORA INCLUYE TEMPERATURA)
    if producto_activo:
        info = f"Producto: {producto_activo.nombre}, Lote: {producto_activo.lote}, Temperatura: {producto_activo.temperatura_optima}"
        sugerencia = obtener_recomendacion_vania(info)
    else:
        sugerencia = "Esperando selección de producto para iniciar análisis de integridad."

    context = {
        'categorias': ['LECHE', 'QUESO', 'CREMA', 'YOGURT'],
        'cat_activa': cat_slug,
        'productos': productos_filtrados,
        'producto_activo': producto_activo,
        'sugerencia': sugerencia
    }
    return render(request, 'detalle.html', context)