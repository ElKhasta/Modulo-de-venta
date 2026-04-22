from django.contrib import admin
from .models import Producto, RegistroSeguridad

# Registramos el catálogo de lácteos
admin.site.register(Producto)

# Registramos el monitor del Sentinel
admin.site.register(RegistroSeguridad)