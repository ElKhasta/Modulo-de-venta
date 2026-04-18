import json
import urllib.request

def obtener_recomendacion_vania(producto_nombre):
    url = "http://localhost:11434/api/generate"
    prompt = f"Eres un experto chef de VANTTI. Sugiere un maridaje y una receta de 3 pasos para: {producto_nombre}. Responde en español."
    
    data = json.dumps({
        "model": "vanIA",
        "prompt": prompt,
        "stream": False
    }).encode('utf-8')
    
    # Esta es la forma correcta para la PowerShell y Python:
    headers = {'Content-Type': 'application/json'}
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get('response', "vanIA está procesando...")
    except Exception as e:
        return f"Error de conexión: Asegúrate de que Ollama esté abierto. ({str(e)})"