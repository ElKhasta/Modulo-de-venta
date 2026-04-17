from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Producto(models.Model):
    codigo_barras = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, unique=True)
    rfc = models.CharField(max_length=13, unique=True, null=True, blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.rfc})"


class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        cliente_nombre = self.cliente.nombre if self.cliente else "Sin cliente"
        return f"Factura #{self.id} - {cliente_nombre}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name="detalles", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_historico = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        ordering = ["id"]

    def clean(self):
        if not self.pk and self.producto.stock < self.cantidad:
            raise ValidationError(
                f"No hay suficiente stock de {self.producto.nombre}. Disponible: {self.producto.stock}"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        if not self.cantidad or not self.precio_historico:
            return Decimal("0.00")
        return self.cantidad * self.precio_historico
