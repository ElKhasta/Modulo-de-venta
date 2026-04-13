from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

class Producto(models.Model):
    codigo_barras = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        # Obligamos a ejecutar validadores (como el de stock >= 0)
        self.full_clean()
        super().save(*args, **kwargs)
    
class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, unique=True)
    rfc = models.CharField(max_length=13, unique=True, null=True, blank=True)
    def __str__(self):
        return f"{self.nombre} ({self.rfc})"
    
class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    def __str__(self):
        return f"Factura #{self.id} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)]) # No vender 0
    precio_historico = models.DecimalField(max_digits=10, decimal_places=2)
    
    def clean(self):
        """
        Validación de seguridad: Si alguien intenta crear un detalle
        que excede el stock actual, el modelo lanza el error.
        """
        if not self.pk: # Solo al crear nuevos detalles
            if self.producto.stock < self.cantidad:
                raise ValidationError(
                    f"No hay suficiente stock de {self.producto.nombre}. "
                    f"Disponible: {self.producto.stock}"
                )

    def save(self, *args, **kwargs):
        # Validamos todo antes de proceder
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        if self.cantidad and self.precio_historico:
            return self.cantidad * self.precio_historico
        return 0