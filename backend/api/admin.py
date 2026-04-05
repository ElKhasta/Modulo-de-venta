from django.contrib import admin
from .models import Cliente, Producto, Venta, DetalleVenta

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    readonly_fields=('subtotal',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'rfc')
    search_fields = ('nombre','rfc')
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display=('nombre','precio','stock',)
    search_fields = ('nombre',)
    list_filter = ('precio',)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'total')
    search_fields = ('fecha','cliente__nombre',)
    list_filter = ('cliente',)
    inlines = [DetalleVentaInline]


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'venta', 'producto', 'cantidad', 'precio_historico')
    search_fields = ('venta__id', 'producto__nombre')
    list_filter = ('venta', 'producto')
