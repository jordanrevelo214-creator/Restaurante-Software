# 📁 pedidos/admin.py

from django.contrib import admin
from .models import Mesa, Producto, Pedido, DetallePedido

@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'capacidad', 'estado')
    ordering = ('numero',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'disponible')
    search_fields = ('nombre',)

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'mesa', 'mesero', 'estado', 'total')
    list_filter = ('estado',)
    inlines = [DetallePedidoInline]