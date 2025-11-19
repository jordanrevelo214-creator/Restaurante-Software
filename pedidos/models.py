
from django.db import models
from django.conf import settings

# 1. MESA
class Mesa(models.Model):
    numero = models.IntegerField(unique=True, verbose_name="Número de Mesa")
    capacidad = models.IntegerField(default=4)
    ESTADO_CHOICES = [
        ('libre', 'Libre'),
        ('ocupada', 'Ocupada'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='libre')

    def __str__(self):
        return f"Mesa {self.numero}"

# 2. PRODUCTO (Menú)
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0, verbose_name="Stock Disponible")
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

# 3. PEDIDO (La cuenta)
class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),       # Mesero tomando orden
        ('confirmado', 'En Cocina'),    # Enviado a cocina
        ('listo', 'Listo para Servir'), # Cocina terminó
        ('entregado', 'Entregado'),     # Comiendo
        ('pagado', 'Pagado'),           # Finalizado
        ('cancelado', 'Cancelado'),
    ]

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='pedidos')
    mesero = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pedido #{self.id} - Mesa {self.mesa.numero}"
    
    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

# 4. DETALLE (Platos del pedido)
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) # Guardamos precio histórico

    def save(self, *args, **kwargs):
        if not self.id:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
