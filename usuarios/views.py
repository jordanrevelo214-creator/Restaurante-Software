
# 📁 usuarios/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone 
from .models import Usuario, AuditLog
from pedidos.models import Pedido, Mesa

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