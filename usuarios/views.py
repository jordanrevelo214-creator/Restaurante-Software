
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages # <--- ESTA ES LA IMPORTACIÓN CORRECTA
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Usuario
from pedidos.models import Mesa

def login_view(request):
    # Si ya está logueado, redirigir según su rol
    if request.user.is_authenticated:
        if request.user.rol == 'mesero':
            return redirect('usuarios:dashboard_mesero')
        elif request.user.rol == 'cocina':
            return redirect('pedidos:dashboard_cocina')
        elif request.user.rol == 'admin':
            return redirect('admin:index')

    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')

        if not identifier or not password:
            messages.error(request, 'Por favor, ingrese su usuario/correo y contraseña.')
            return render(request, 'usuarios/login.html')

        try:
            # Buscamos por username O email
            user_q = Usuario.objects.get(Q(username=identifier) | Q(email=identifier))
            
            # Verificamos contraseña
            user = authenticate(request, username=user_q.username, password=password)

            if user is not None:
                login(request, user)
                
                # --- REDIRECCIÓN POR ROL ---
                if user.rol == 'mesero':
                    return redirect('usuarios:dashboard_mesero')
                elif user.rol == 'cocina':
                    return redirect('pedidos:dashboard_cocina')
                elif user.rol == 'admin':
                    return redirect('admin:index')
                else:
                    return redirect('/') 
            else:
                messages.error(request, 'Credenciales inválidas.')
        
        except Usuario.DoesNotExist:
            messages.error(request, 'Credenciales inválidas.')

    return render(request, 'usuarios/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('usuarios:login')

@login_required
def dashboard_mesero(request):
    if request.user.rol != 'mesero':
        return redirect('usuarios:login')
    
    # Obtenemos las mesas ordenadas para mostrarlas en el dashboard
    mesas = Mesa.objects.all().order_by('numero')
    return render(request, 'usuarios/dashboard_mesero.html', {'mesas': mesas})