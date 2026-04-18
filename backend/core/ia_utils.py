import json
import urllib.request

def obtener_recomendaciones_multiples(producto_nombre):
    url = "http://localhost:11434/api/generate"
    
    # Prompt mejorado para pedir 3 opciones
    prompt = (
        f"Eres el chef ejecutivo de VANTTI. El cliente tiene: {producto_nombre}. "
        "Proporciona 3 opciones de recetas diferentes y creativas. "
        "Para cada opción incluye: 1. Nombre del platillo, 2. Ingredientes clave, 3. Un maridaje sugerido. "
        "Responde en español de forma estructurada y breve."
    )
    
    data = json.dumps({
        "model": "vanIA",
        "prompt": prompt,
        "stream": False
    }).encode('utf-8')
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=40) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get('response', "vanIA no pudo generar las opciones.")
    except Exception as e:
        return f"Error de conexión con vanIA: {str(e)}"