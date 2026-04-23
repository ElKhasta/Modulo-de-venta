from django.contrib import admin
from django.urls import include, path

from .views import catalogo_VANTTI

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", catalogo_VANTTI, name="catalogo"),
]
