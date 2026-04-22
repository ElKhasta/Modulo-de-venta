from django.db import models

class RegistroSeguridad(models.Model):
    TIPOS_ATAQUE = [
        ('SQLI', 'Inyección SQL'),
        ('XSS', 'Cross-Site Scripting'),
        ('BF', 'Fuerza Bruta'),
        ('SUSP', 'Actividad Sospechosa'),
    ]
    
    ip_ofensora = models.GenericIPAddressField()
    tipo_ataque = models.CharField(max_length=5, choices=TIPOS_ATAQUE)
    payload_malicioso = models.TextField()
    fecha_deteccion = models.DateTimeField(auto_now_add=True)
    bloqueado = models.BooleanField(default=True)

    
    class Meta:
        app_label = 'core' 

    def __str__(self):
        return f"{self.tipo_ataque} detectado desde {self.ip_ofensora}"
    from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    lote = models.CharField(max_length=50, default="LOTE-001")
    temperatura_optima = models.CharField(max_length=20, default="4°C")

    class Meta:
        app_label = 'core'

    def __str__(self):
        return self.nombre
    from django.db import models

class Producto(models.Model):
    CATEGORIAS = [
        ('LECHE', 'Leche'),
        ('QUESO', 'Queso'),
        ('CREMA', 'Crema'),
        ('YOGURT', 'Yogurt'),
    ]
    
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='QUESO')
    lote = models.CharField(max_length=50, default="LOTE-001")
    temperatura_optima = models.CharField(max_length=20, default="4°C")

    def __str__(self):
        return f"[{self.categoria}] {self.nombre}"