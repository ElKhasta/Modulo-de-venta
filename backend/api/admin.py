from django.contrib import admin

from .models import Cliente, DetalleVenta, Producto, Venta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    readonly_fields = ("subtotal",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "email", "telefono", "rfc")
    search_fields = ("nombre", "rfc", "telefono")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo_barras", "precio", "stock")
    search_fields = ("nombre", "codigo_barras")
    list_filter = ("stock",)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "fecha", "total")
    search_fields = ("id", "cliente__nombre")
    list_filter = ("cliente", "fecha")
    inlines = [DetalleVentaInline]


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ("id", "venta", "producto", "cantidad", "precio_historico", "subtotal")
    search_fields = ("venta__id", "producto__nombre")
    list_filter = ("venta", "producto")
