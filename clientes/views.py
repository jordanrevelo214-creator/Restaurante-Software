# 📁 clientes/views.py

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from .models import Cliente
from pedidos.models import Pedido

# 1. BUSCADOR (Lo que usa HTMX)
def buscar_cliente(request):
    query = request.GET.get('q', '')
    pedido_id = request.GET.get('pedido_id')
    clientes = []
    
    if query:
        # Buscamos por nombre O por cédula
        clientes = Cliente.objects.filter(
            Q(nombres__icontains=query) | 
            Q(numero_documento__icontains=query)
        )[:5] # Solo mostramos los 5 primeros

    context = {
        'clientes': clientes,
        'pedido_id': pedido_id
    }
    # OJO: Renderizamos un "partial" (un pedacito de HTML), no una página entera
    return render(request, 'clientes/partials/resultados_busqueda.html', context)

# 2. ASIGNAR CLIENTE AL PEDIDO
@require_POST
def asignar_cliente(request, pedido_id, cliente_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    
    pedido.cliente = cliente
    pedido.save()
    
    # Devolvemos el HTML actualizado del cliente seleccionado
    return HttpResponse(f"""
        <div style="background: #e8f5e9; color: #2e7d32; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <strong>Cliente Asignado:</strong> {cliente.nombres} ({cliente.numero_documento})
        </div>
    """)