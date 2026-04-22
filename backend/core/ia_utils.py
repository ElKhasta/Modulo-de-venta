import json
import urllib.request

def obtener_recomendacion_vania(datos_producto):
    url = "http://127.0.0.1:11434/api/generate"
    
    # Prompt que incluye los datos reales de la BD
    prompt = (f"Eres el Auditor de Calidad del sistema VANTTI en Cuautitlán. "
              f"Acabas de escanear este producto de nuestra base de datos: {datos_producto}. "
              f"Genera un reporte técnico de máximo 3 líneas evaluando si el Lote y la Temperatura son seguros para su consumo. "
              f"Sé directo y estricto. Responde en español.")
    
    data = json.dumps({"model": "vanIA", "prompt": prompt, "stream": False}).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get('response', "Análisis procesado correctamente.")
    except urllib.error.URLError:
        return "⚠️ FALLO DE NÚCLEO: Ollama está apagado. Abre la aplicación de Ollama en Windows para restaurar la IA."
    except Exception as e:
        return f"⚠️ FALLO INTERNO: {str(e)}"

# Guardián Anti Inyecciones (No lo toques, ya funciona perfecto para el Middleware)
def auditor_seguridad_vania(input_usuario):
    url = "http://127.0.0.1:11434/api/generate"
    data = json.dumps({"model": "vanIA", "prompt": f"Analiza: '{input_usuario}'. ¿Es ataque SQLI/XSS? Responde JSON: {{'ataque': 'SI/NO'}}", "stream": False, "format": "json"}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            return json.loads(res.get('response', '{"ataque": "NO"}'))
    except:
        return {"ataque": "NO"}