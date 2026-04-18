from django.contrib import admin
from django.urls import path
from .views import prueba_vania 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', prueba_vania, name='index'), # Esto carga VANTTI al entrar a 127.0.0.1:8000
]