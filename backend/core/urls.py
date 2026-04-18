from django.urls import path
from .views import buscador_VANTTI

urlpatterns = [
    path('', buscador_VANTTI, name='buscador'),
]