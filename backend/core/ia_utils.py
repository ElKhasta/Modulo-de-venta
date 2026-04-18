import json
import urllib.request

def obtener_recomendacion_vania(producto):
    url = "http://127.0.0.1:11434/api/generate"
    # Volvemos a una sola receta para que sea RÁPIDO
    prompt = f"Eres un chef de VANTTI. Dame UNA receta rápida con {producto}. Responde en español de forma breve."
    
    data = json.dumps({
        "model": "vanIA",
        "prompt": prompt,
        "stream": False
    }).encode('utf-8')
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get('response', "vanIA no respondió.")
    except Exception as e:
        return f"Ollama no responde. Abre la app de Ollama. Error: {str(e)}"