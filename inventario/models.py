
from django.db import models
from pedidos.models import Producto

# 1. PROVEEDORES
class Proveedor(models.Model):
    ruc = models.CharField(max_length=13, unique=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

# 2. INSUMOS (Ingredientes)
class Insumo(models.Model):
    UNIDAD_CHOICES = [
        ('kg', 'Kilogramos'),
        ('lt', 'Litros'),
        ('un', 'Unidades'),
        ('lb', 'Libras'),
    ]
    nombre = models.CharField(max_length=100)
    unidad_medida = models.CharField(max_length=5, choices=UNIDAD_CHOICES)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3, default=5)

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.unidad_medida})"

# 3. KARDEX (Historial)
class MovimientoKardex(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada (Compra)'),
        ('salida', 'Salida (Venta/Merma)'),
        ('ajuste', 'Ajuste de Inventario'),
    ]
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.CharField(max_length=200, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Actualizamos el stock del insumo automáticamente
        if self.tipo == 'entrada':
            self.insumo.stock_actual += self.cantidad
        else:
            self.insumo.stock_actual -= self.cantidad
        
        self.insumo.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo.upper()} - {self.insumo.nombre}"

# 4. RECETAS (Conexión Plato -> Insumos)
class Receta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='receta')
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    cantidad_necesaria = models.DecimalField(max_digits=10, decimal_places=3, help_text="Cantidad para 1 plato")

    def __str__(self):
        return f"{self.producto.nombre} usa {self.cantidad_necesaria} de {self.insumo.nombre}"
