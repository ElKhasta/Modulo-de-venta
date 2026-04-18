import json
import urllib.request

def obtener_recomendacion_vania(producto_nombre):
    url = "http://localhost:11434/api/generate"
    prompt = f"Eres un experto chef de VANTTI. El cliente compró {producto_nombre}. Sugiere un maridaje corto y una receta de 3 pasos. Responde en español."
    
    data = {
        "model": "vanIA",
        "prompt": prompt,
        "stream": False
    }
    
    # Aquí está la corrección: Usamos 'headers' en lugar de 'content_type' directo
    headers = {'Content-Type': 'application/json'}
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers=headers
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get('response', "vanIA está procesando...")
    except Exception as e:
        return f"Error al conectar con vanIA: {str(e)}"