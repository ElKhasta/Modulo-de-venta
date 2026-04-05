from django.db import models
from django.core.exceptions import ValidationError

class Producto(models.Model):
    codigo_barras=models.CharField(max_length=50, unique=True)
    nombre=models.CharField(max_length=100)
    precio=models.DecimalField(max_digits=10, decimal_places=2)
    stock=models.IntegerField(default=0)
    def __str__(self):
        return self.nombre
    
class Cliente(models.Model):
    nombre=models.CharField(max_length=150)
    email=models.EmailField()
    telefono=models.CharField(max_length=20, unique=True)
    rfc=models.CharField(max_length=13, unique=True, null=True, blank=True)
    def __str__(self):
        return f"{self.nombre} ({self.rfc})"
    
class Venta(models.Model):
    cliente=models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    fecha=models.DateTimeField(auto_now_add=True)
    total=models.DecimalField(max_digits=12, decimal_places=2, default=0)
    def __str__(self):
        return f"Factura #{self.id} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"
class DetalleVenta(models.Model):
    venta=models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto=models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad=models.IntegerField()
    precio_historico=models.DecimalField(max_digits=10, decimal_places=2)
    def save(self, *args, **kwargs):
        if self.pk:
            anterior = DetalleVenta.objects.get(pk=self.pk)
            diferencia = self.cantidad - anterior.cantidad
        else:
            diferencia = self.cantidad

        if self.producto.stock < diferencia:
            raise ValidationError(
                f"No hay suficiente stock de {self.producto.nombre}. "
                f"Disponible: {self.producto.stock}, Solicitado adicional: {diferencia}"
            )
        self.producto.stock -= diferencia
        self.producto.save()
        super().save(*args, **kwargs)
    @property
    def subtotal(self):
        if self.cantidad and self.precio_historico:
            return self.cantidad * self.precio_historico
        return 0