# 📁 pedidos/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
from .models import Mesa, Pedido, Producto, DetallePedido

# 1. VISTA PARA VER LA MESA Y TOMAR PEDIDO
@login_required
def detalle_mesa(request, mesa_id):
    # Obtenemos la mesa
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    
    # Buscamos si ya hay un pedido activo
    pedido_activo = Pedido.objects.filter(
        mesa=mesa, 
        estado__in=['borrador', 'confirmado', 'listo', 'entregado']
    ).first()
    
    # Si no hay pedido, creamos uno nuevo
    if not pedido_activo:
        pedido_activo = Pedido.objects.create(
            mesa=mesa,
            mesero=request.user,
            estado='borrador'
        )
        mesa.estado = 'ocupada'
        mesa.save()

    # Traemos el menú disponible
    productos = Producto.objects.filter(disponible=True)

    context = {
        'mesa': mesa,
        'pedido': pedido_activo,
        'productos': productos,
    }
    return render(request, 'pedidos/detalle_mesa.html', context)


# 2. VISTA PARA AGREGAR UN PRODUCTO (USADA POR JAVASCRIPT)
@require_POST
def agregar_producto(request, pedido_id):
    data = json.loads(request.body)
    producto_id = data.get('producto_id')

    pedido = get_object_or_404(Pedido, pk=pedido_id)
    producto = get_object_or_404(Producto, pk=producto_id)

    # Validamos Stock
    if producto.stock > 0:
        detalle, created = DetallePedido.objects.get_or_create(
            pedido=pedido,
            producto=producto,
            defaults={'precio_unitario': producto.precio}
        )
        
        if not created:
            detalle.cantidad += 1
            detalle.save()
        
        # Restamos del stock
        producto.stock -= 1
        producto.save()

        return JsonResponse({'success': True, 'message': 'Producto agregado', 'nuevo_total': pedido.total})
    else:
        return JsonResponse({'success': False, 'message': 'No hay stock disponible'})


# 3. VISTA PARA CONFIRMAR EL PEDIDO (ENVIAR A COCINA)
@login_required
def confirmar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    # Solo confirmamos si tiene productos
    if pedido.items.exists():
        pedido.estado = 'confirmado' # Cambia el estado para que lo vea cocina
        pedido.save()
        return redirect('usuarios:dashboard_mesero') # Regresa al panel principal
    else:
        return redirect('pedidos:detalle_mesa', mesa_id=pedido.mesa.id)
    
@login_required
def dashboard_cocina(request):
    # Solo mostramos los pedidos que están "En Cocina" (confirmado)
    # Los ordenamos por hora (el más viejo primero)
    pedidos = Pedido.objects.filter(estado='confirmado').order_by('created_at')
    return render(request, 'pedidos/dashboard_cocina.html', {'pedidos': pedidos})

# 5. ACCIÓN PARA MARCAR COMO "LISTO"
@login_required
def terminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    if pedido.estado == 'confirmado':
        pedido.estado = 'listo' # Cambia a 'Listo para Servir'
        pedido.save()
    
    return redirect('pedidos:dashboard_cocina')