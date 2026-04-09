import ollama # type: ignore
from .models import Producto, Venta # pyright: ignore[reportMissingImports]

def analizar_inventario_con_ia(request):
    # Obtenemos productos con poco stock
    productos_criticos = Producto.objects.filter(stock__lt=5)
    
    lista_productos = ", ".join([f"{p.nombre} (Stock: {p.stock})" for p in productos_criticos])
    
    prompt = f"Actúa como un experto en logística. Tengo estos productos con bajo stock: {lista_productos}. Dame 3 consejos rápidos para gestionar este inventario."

    response = ollama.chat(model='llama3.2', messages=[
        {'role': 'user', 'content': prompt},
    ])

    mensaje_ia = response['message']['content']
    return render(request, 'dashboard.html', {'consejo_ia': mensaje_ia}) # pyright: ignore[reportUndefinedVariable]
