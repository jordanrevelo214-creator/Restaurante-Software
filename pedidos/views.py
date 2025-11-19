

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
from .models import Mesa, Pedido, Producto, DetallePedido
from usuarios.models import AuditLog

# --- FUNCIÓN AUXILIAR ---
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# --- VISTAS DEL MESERO ---

@login_required
def detalle_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    
    # Buscamos si hay un pedido activo
    pedido_activo = Pedido.objects.filter(
        mesa=mesa, 
        estado__in=['borrador', 'confirmado', 'listo', 'entregado']
    ).first()
    
    # Si no hay pedido y la mesa está libre, creamos uno nuevo
    if not pedido_activo:
        pedido_activo = Pedido.objects.create(
            mesa=mesa,
            mesero=request.user,
            estado='borrador'
        )
        mesa.estado = 'ocupada'
        mesa.save()

    productos = Producto.objects.filter(disponible=True)

    context = {
        'mesa': mesa,
        'pedido': pedido_activo,
        'productos': productos,
    }
    return render(request, 'pedidos/detalle_mesa.html', context)

@require_POST
def agregar_producto(request, pedido_id):
    data = json.loads(request.body)
    producto_id = data.get('producto_id')

    pedido = get_object_or_404(Pedido, pk=pedido_id)
    producto = get_object_or_404(Producto, pk=producto_id)

    if producto.stock > 0:
        detalle, created = DetallePedido.objects.get_or_create(
            pedido=pedido,
            producto=producto,
            defaults={'precio_unitario': producto.precio}
        )
        
        if not created:
            detalle.cantidad += 1
            detalle.save()
        
        producto.stock -= 1
        producto.save()

        return JsonResponse({'success': True, 'message': 'Producto agregado', 'nuevo_total': pedido.total})
    else:
        return JsonResponse({'success': False, 'message': 'No hay stock disponible'})

@login_required
def confirmar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    if pedido.items.exists():
        pedido.estado = 'confirmado'
        pedido.save()
        
        # LOG DE AUDITORÍA
        AuditLog.objects.create(
            user=request.user,
            ip_address=get_client_ip(request),
            action=f"Envió a cocina: Pedido #{pedido.id} (Mesa {pedido.mesa.numero})"
        )
        
        return redirect('usuarios:dashboard_mesero')
    else:
        return redirect('pedidos:detalle_mesa', mesa_id=pedido.mesa.id)

@login_required
def pagar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    if pedido.estado in ['confirmado', 'listo', 'entregado']:
        # 1. Marcar como pagado
        pedido.estado = 'pagado'
        pedido.save()
        
        # 2. Liberar mesa
        mesa = pedido.mesa
        mesa.estado = 'libre'
        mesa.save()

        # LOG DE AUDITORÍA
        AuditLog.objects.create(
            user=request.user,
            ip_address=get_client_ip(request),
            action=f"Cobró cuenta: Pedido #{pedido.id} - Total ${pedido.total}"
        )
    
    return redirect('usuarios:dashboard_mesero')

# --- VISTAS DE COCINA ---

@login_required
def dashboard_cocina(request):
    # Seguridad: Solo cocina o admin
    if request.user.rol != 'cocina' and request.user.rol != 'admin':
        return redirect('usuarios:login')

    pedidos = Pedido.objects.filter(estado='confirmado').order_by('created_at')
    return render(request, 'pedidos/dashboard_cocina.html', {'pedidos': pedidos})

@login_required
def terminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    if pedido.estado == 'confirmado':
        pedido.estado = 'listo'
        pedido.save()

        # LOG DE AUDITORÍA
        AuditLog.objects.create(
            user=request.user,
            ip_address=get_client_ip(request),
            action=f"Cocina terminó: Pedido #{pedido.id}"
        )
    
    return redirect('pedidos:dashboard_cocina')