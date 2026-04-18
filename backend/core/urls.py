from django.contrib import admin
from django.urls import path
from .views import catalogo_VANTTI # Cambiamos buscador por catalogo

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', catalogo_VANTTI, name='catalogo'), # La página principal ahora es el catálogo
]