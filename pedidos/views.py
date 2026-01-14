

# 📁 pedidos/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
import json
from django.views.decorators.http import etag
from django.utils import timezone

from clientes.models import Cliente
from .models import Pedido, Producto, DetallePedido, Mesa, Factura
from usuarios.models import AuditLog
from usuarios.models import AuditLog
from inventario.models import MovimientoKardex
from .forms import ProductoForm # Importar Formulario

# --- FUNCIÓN AUXILIAR PARA LA IP ---
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# --- VISTAS DEL MESERO ---

# 👇👇👇 ESTA ES LA VISTA NUEVA QUE FALTABA 👇👇👇
@login_required
def panel_mesas(request):
    # Traemos todas las mesas ordenadas por su número
    mesas = Mesa.objects.all().order_by('numero')
    return render(request, 'pedidos/panel_mesas.html', {'mesas': mesas})
# 👆👆👆 FIN DE LO NUEVO 👆👆👆

@login_required
def detalle_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    
    # Buscamos si hay un pedido activo
    pedido_activo = Pedido.objects.filter(
        mesa=mesa, 
        estado__in=['borrador', 'confirmado', 'listo', 'entregado']
    ).first()
    
    # Si no hay pedido y la mesa está libre, creamos uno nuevo (pero NO ocupamos la mesa aún)
    if not pedido_activo:
        pedido_activo = Pedido.objects.create(
            mesa=mesa,
            mesero=request.user,
            estado='borrador'
        )
        # mesa.estado = 'ocupada'  <-- ELIMINADO: No ocupar hasta que haya productos
        # mesa.save()

    productos = Producto.objects.filter(disponible=True)

    # Detección manual de HTMX
    is_htmx = request.headers.get('HX-Request') == 'true' or request.META.get('HTTP_HX_REQUEST')

    context = {
        'mesa': mesa,
        'pedido': pedido_activo,
        'productos': productos,
        'is_htmx': is_htmx,
    }
    return render(request, 'pedidos/detalle_mesa.html', context)

@login_required
def agregar_producto(request, pedido_id, producto_id):
    
    # 1. Buscamos los objetos con los IDs que vienen de la URL
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    producto = get_object_or_404(Producto, pk=producto_id)

    # 2. Lógica de inventario
    if producto.stock > 0:
        detalle, created = DetallePedido.objects.get_or_create(
            pedido=pedido,
            producto=producto,
            defaults={'precio_unitario': producto.precio}
        )
        
        if not created:
            detalle.cantidad += 1
            detalle.save()
        
        # Restar stock
        producto.stock -= 1
        producto.save()

        # NUEVO: Si la mesa estaba libre, ahora sí la ocupamos
        if pedido.mesa.estado == 'libre':
            pedido.mesa.estado = 'ocupada'
            pedido.mesa.save()

    # 3. Respuesta: Devolvemos el HTML del panel derecho actualizado
    context = {
        'pedido': pedido,
        'mesa': pedido.mesa
    }
    return render(request, 'pedidos/partials/orden_actual.html', context)

@login_required
def confirmar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    if pedido.items.exists():
        pedido.estado = 'confirmado'
        pedido.save()
        
        # 1. LOG DE AUDITORÍA
        AuditLog.objects.create(
            user=request.user,
            ip_address=get_client_ip(request),
            action=f"Envió a cocina: Pedido #{pedido.id} (Mesa {pedido.mesa.numero})"
        )

        # 2. DESCARGA DE INVENTARIO (RECETAS)
        for detalle in pedido.items.all():
            producto = detalle.producto
            cantidad_vendida = detalle.cantidad

            if producto.receta.exists():
                for item_receta in producto.receta.all():
                    insumo = item_receta.insumo
                    cantidad_a_descontar = item_receta.cantidad_necesaria * cantidad_vendida
                    
                    # Restamos del stock del INSUMO
                    insumo.stock_actual -= cantidad_a_descontar
                    insumo.save()

                    # Guardamos en Kardex
                    MovimientoKardex.objects.create(
                        insumo=insumo,
                        tipo='salida',
                        cantidad=cantidad_a_descontar,
                        costo_total=cantidad_a_descontar * insumo.costo_unitario,
                        observacion=f"Venta Pedido #{pedido.id}: {producto.nombre} x{cantidad_vendida}"
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

# --- NUEVA VISTA PARA HTMX (+/- CANTIDAD) ---

@login_required
def modificar_cantidad_item(request, item_id, accion):
    # CORREGIDO: Usamos 'DetallePedido' en lugar de 'PedidoItem'
    item = get_object_or_404(DetallePedido, id=item_id)
    pedido = item.pedido
    
    if pedido.estado == 'borrador':
        if accion == 'sumar':
            item.cantidad += 1
            item.save()
        elif accion == 'restar':
            item.cantidad -= 1
            if item.cantidad <= 0:
                item.delete()
            else:
                item.save()
        
    # Devolvemos el HTML parcial para HTMX
    context = {
        'pedido': pedido,
        'mesa': pedido.mesa
    }
    return render(request, 'pedidos/partials/orden_actual.html', context)

def cocina_etag(request, *args, **kwargs):
    # Buscamos el último pedido modificado o creado
    ultimo_pedido = Pedido.objects.filter(estado='confirmado').order_by('-updated_at').first()
    conteo = Pedido.objects.filter(estado='confirmado').count()
    
    if ultimo_pedido:
        # La huella es: Cantidad de pedidos + Fecha del último cambio
        return str(conteo) + str(ultimo_pedido.updated_at)
    else:
        return "0"

# Con esto logramos que la cocina se actualice cada cierto tiempo 

@login_required
@etag(cocina_etag)
def actualizar_cocina(request):
   
    # Buscamos SOLO los pedidos 'confirmado' (pendientes de cocinar)
    # Ordenamos por antigüedad (el más viejo primero)
    pedidos = Pedido.objects.filter(estado='confirmado').order_by('created_at')
    return render(request, 'pedidos/partials/lista_pedidos_cocina.html', {'pedidos': pedidos})

@login_required
def ver_comanda(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    return render(request, 'pedidos/comanda_cocina.html', {'pedido': pedido, 'now': timezone.now()})

@login_required
def modal_cobrar(request, pedido_id):
    # Buscamos el pedido para mostrar el total
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    return render(request, 'pedidos/modals/cobrar.html', {'pedido': pedido})

@login_required
def procesar_pago(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        cliente_id = request.POST.get('cliente_id')
        
        # 1. Obtener Cliente (si enviaron uno)
        cliente = None
        if cliente_id:
            cliente = get_object_or_404(Cliente, pk=cliente_id)
            
        # 2. Crear la Factura (Snapshot de datos)
        # Si no hay cliente, usamos datos genéricos de Consumidor Final
        datos_factura = {
            'pedido': pedido,
            'cliente': cliente,
            'subtotal': pedido.total, 
            'total': pedido.total,
            'metodo_pago': 'efectivo', 
            'razon_social': cliente.nombres if cliente else 'CONSUMIDOR FINAL',
            'ruc_ci': cliente.cedula_o_ruc if cliente else '9999999999999',
            'direccion': cliente.direccion if cliente else '',
            'correo': cliente.email if cliente else ''
        }
        
        factura = Factura.objects.create(**datos_factura)
        
        # 3. AUTOMATIZACIÓN DE INVENTARIO (KARDEX)
        # Recorremos cada plato vendido para descontar sus ingredientes
        for item in pedido.items.all():
            producto = item.producto
            cantidad_vendida = item.cantidad
            
            # Buscamos si el producto tiene receta (ingredientes)
            if hasattr(producto, 'receta'):
                for ingrediente in producto.receta.all():
                    insumo = ingrediente.insumo
                    cantidad_a_descontar = ingrediente.cantidad_necesaria * cantidad_vendida
                    
                    # Registramos la salida en el Kardex
                    MovimientoKardex.objects.create(
                        insumo=insumo,
                        tipo='salida',
                        cantidad=cantidad_a_descontar,
                        costo_total=cantidad_a_descontar * insumo.costo_unitario, # Costo estimado
                        observacion=f"Venta Pedido #{pedido.id}: {cantidad_vendida}x {producto.nombre}"
                    )

        # 4. Actualizar Estados
        pedido.estado = 'pagado'
        pedido.save()
        
        mesa = pedido.mesa
        mesa.estado = 'libre'
        mesa.save()
        
        # 4. Redirigir al Ticket
        return redirect('pedidos:ver_ticket', factura_id=factura.id)

def ver_ticket(request, factura_id):
    factura = get_object_or_404(Factura, pk=factura_id)
    return render(request, 'pedidos/ticket.html', {'factura': factura})

# --- GESTIÓN DE PRODUCTOS (GERENTE) ---

# --- GESTIÓN DE RECETAS (Menú Gerente) ---
from .forms import RecetaForm 
from inventario.models import Receta

@login_required
def gestion_receta(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    recetas = producto.receta.all() # Related name configurado en el modelo
    
    if request.method == 'POST':
        form = RecetaForm(request.POST)
        if form.is_valid():
            nueva_receta = form.save(commit=False)
            nueva_receta.producto = producto
            nueva_receta.save()
            # Recargamos el mismo modal con los datos actualizados
            return render(request, 'pedidos/modals/gestion_receta.html', {
                'producto': producto, 'recetas': recetas, 'form': RecetaForm()
            })
    else:
        form = RecetaForm()

    return render(request, 'pedidos/modals/gestion_receta.html', {
        'producto': producto,
        'recetas': recetas,
        'form': form
    })

@login_required
def eliminar_ingrediente(request, receta_id):
    receta_item = get_object_or_404(Receta, pk=receta_id)
    producto_id = receta_item.producto.id
    receta_item.delete()
    
    # Redirigimos de vuelta al modal principal de gestión de ese producto
    return gestion_receta(request, producto_id)

@login_required
def crear_producto(request):
    # Verificación de rol (opcional, pero recomendada)
    if request.user.rol not in ['gerente', 'admin']:
        return HttpResponse("No autorizado", status=403)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Retornar refresh para actualizar la tabla
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = ProductoForm()
    
    return render(request, 'pedidos/modals/form_producto.html', {'form': form, 'titulo': 'Nuevo Plato'})

@login_required
def editar_producto(request, pk):
    if request.user.rol not in ['gerente', 'admin']:
        return HttpResponse("No autorizado", status=403)

    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'pedidos/modals/form_producto.html', {'form': form, 'titulo': f'Editar {producto.nombre}'})

@login_required
@require_POST
def eliminar_producto(request, pk):
    if request.user.rol not in ['gerente', 'admin']:
        return HttpResponse("No autorizado", status=403)
    
    producto = get_object_or_404(Producto, pk=pk)
    producto.delete()
    return HttpResponse(status=204, headers={'HX-Refresh': 'true'})

@login_required
def check_notificaciones(request):
    if request.user.rol != 'mesero':
        return HttpResponse("")

    pedidos_listos = Pedido.objects.filter(
        mesero=request.user, 
        estado='listo'
    )
    
    if not pedidos_listos.exists():
        return HttpResponse("")

    return render(request, 'pedidos/partials/notificaciones.html', {'pedidos_listos': pedidos_listos})

