
# 📁 usuarios/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone 
from .models import Usuario, AuditLog
from pedidos.models import Pedido, Mesa
from pedidos.models import Producto
import csv
from django.http import HttpResponse
from pedidos.models import Pedido 
from inventario.models import Insumo

# 1. LOGIN
def login_view(request):
    if request.user.is_authenticated:
        if request.user.rol == 'mesero':
            return redirect('usuarios:dashboard_mesero')
        elif request.user.rol == 'cocina':
            return redirect('pedidos:dashboard_cocina')
        elif request.user.rol == 'gerente':
            return redirect('usuarios:dashboard_gerente')
        elif request.user.rol == 'admin':
            return redirect('admin:index')

    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')

        if not identifier or not password:
            messages.error(request, 'Por favor, ingrese su usuario/correo y contraseña.')
            return render(request, 'usuarios/login.html')

        try:
            user_q = Usuario.objects.get(Q(username=identifier) | Q(email=identifier))
            user = authenticate(request, username=user_q.username, password=password)

            if user is not None:
                login(request, user)
                if user.rol == 'mesero':
                    return redirect('usuarios:dashboard_mesero')
                elif user.rol == 'cocina':
                    return redirect('pedidos:dashboard_cocina')
                elif user.rol == 'gerente':
                    return redirect('usuarios:dashboard_gerente')
                elif user.rol == 'admin':
                    return redirect('admin:index')
                else:
                    return redirect('/') 
            else:
                messages.error(request, 'Credenciales inválidas.')
        
        except Usuario.DoesNotExist:
            messages.error(request, 'Credenciales inválidas.')

    return render(request, 'usuarios/login.html')

# 2. LOGOUT
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('usuarios:login')

# 3. DASHBOARD MESERO
@login_required
def dashboard_mesero(request):
    if request.user.rol != 'mesero':
        return redirect('usuarios:login')
    mesas = Mesa.objects.all().order_by('numero')
    return render(request, 'usuarios/dashboard_mesero.html', {'mesas': mesas})

# 4. DASHBOARD GERENTE (LA QUE FALTABA)
@login_required
def dashboard_gerente(request):
    if request.user.rol != 'gerente' and request.user.rol != 'admin':
        return redirect('usuarios:login')

    # Datos para las Tarjetas
    total_usuarios = Usuario.objects.count()
    usuarios_activos = Usuario.objects.filter(is_active=True).count()
    
    # Ventas de HOY
    hoy = timezone.now().date()
    pedidos_hoy = Pedido.objects.filter(created_at__date=hoy, estado='pagado')
    total_ventas_hoy = sum(p.total for p in pedidos_hoy)
    
    # Logs
    ultimos_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]

    context = {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'total_ventas_hoy': total_ventas_hoy,
        'ultimos_logs': ultimos_logs,
    }
    return render(request, 'usuarios/dashboard_gerente.html', context)

@login_required
def lista_usuarios(request):
    # Seguridad: Solo gerentes o admins
    if request.user.rol != 'gerente' and request.user.rol != 'admin':
        return redirect('usuarios:login')
        
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})

@login_required
def gestion_menu(request):
    # Seguridad: Solo gerentes o admins
    if request.user.rol != 'gerente' and request.user.rol != 'admin':
        return redirect('usuarios:login')

    # Traemos todos los productos
    productos = Producto.objects.all().order_by('nombre')
    
    return render(request, 'usuarios/gestion_menu.html', {'productos': productos})

@login_required
def reportes_ventas(request):
    # Seguridad: Solo Gerentes o Admins
    if request.user.rol != 'gerente' and request.user.rol != 'admin':
        return redirect('usuarios:login')

    # Obtener pedidos pagados
    pedidos = Pedido.objects.filter(estado='pagado').order_by('-created_at')
    total_ingresos = sum(p.total for p in pedidos)

    # Lógica de Exportación a Excel (CSV)
    if 'exportar' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_ventas.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Fecha', 'Mesa', 'Mesero', 'Total'])
        
        for p in pedidos:
            writer.writerow([
                p.id, 
                p.created_at.strftime("%d/%m/%Y %H:%M"), 
                f"Mesa {p.mesa.numero}", 
                p.mesero.username, 
                p.total
            ])
        return response

    return render(request, 'usuarios/reportes.html', {
        'pedidos': pedidos, 
        'total_ingresos': total_ingresos
    })

@login_required
def gestion_inventario(request):
    # Seguridad
    if request.user.rol != 'gerente' and request.user.rol != 'admin':
        return redirect('usuarios:login')

    # Traemos todos los insumos ordenados por nombre
    insumos = Insumo.objects.all().order_by('nombre')
    
    return render(request, 'usuarios/gestion_inventario.html', {'insumos': insumos})