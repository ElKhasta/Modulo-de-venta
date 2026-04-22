from django.http import HttpResponseForbidden
from .ia_utils import auditor_seguridad_vania

class SecuritySentinelMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        'core.middleware.SecuritySentinelMiddleware',

    def __call__(self, request):
        # 1. Unimos todo lo que el usuario escriba en la URL o formularios
        inputs_a_revisar = list(request.GET.values()) + list(request.POST.values())
        
        for texto in inputs_a_revisar:
            # Solo revisamos textos sospechosos (cortos pero con caracteres raros)
            if len(str(texto)) > 3:
                # La IA revisa si es un ataque
                analisis = auditor_seguridad_vania(str(texto))
                
                if isinstance(analisis, dict) and analisis.get('ataque') == 'SI':
                    # BLOQUEO INMEDIATO AL HACKER
                    return HttpResponseForbidden(
                        "<h1 style='color:red; background:black; padding:50px; text-align:center; font-family:monospace;'>"
                        "🛑 VANTTI SENTINEL: ACCESO DENEGADO.<br>Intento de Inyección SQL / XSS Bloqueado."
                        "</h1>"
                    )

        # Si todo está limpio, deja pasar al usuario normalmente
        return self.get_response(request)
    