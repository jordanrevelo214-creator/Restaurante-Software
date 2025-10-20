# 📁 usuarios/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from .models import Usuario # Importar el modelo Usuario
from django.contrib.auth.decorators import login_required
# Para recuperación de contraseña
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth import login, get_backends
#aqui realizare un cambio

def login_view(request):
    if request.user.is_authenticated:
        if request.user.rol == 'mesero':
            return redirect('usuarios:dashboard_mesero')
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
            
            print("="*50)
            print(f"DEBUG LOGIN: Identificador recibido: '{identifier}'")
            print(f"DEBUG LOGIN: Password recibida: '{password}'")
            print(f"DEBUG LOGIN: Usuario encontrado: {user_q.username}")
            print(f"DEBUG LOGIN: Check password result: {user_q.check_password(password)}")
            print("="*50)
             
            if user_q.check_password(password):
                backend = get_backends()[0]
                user_q.backend = f"{backend.__module__}.{backend.__class__.__name__}"
                login(request, user_q)
                
                if user_q.rol == 'mesero':
                    return redirect('usuarios:dashboard_mesero')
                elif user_q.rol == 'admin':
                    return redirect('admin:index')
                else:
                    return redirect('/') 
            else:
                messages.error(request, 'Credenciales inválidas.')
        
        except Usuario.DoesNotExist:
            messages.error(request, 'Credenciales inválidas.')

    return render(request, 'usuarios/login.html')

# Vista de Logout
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('usuarios:login')

# Vista de ejemplo para el Dashboard del Mesero
@login_required
def dashboard_mesero(request):
    # Lógica para proteger la vista, solo meseros pueden entrar
    if request.user.rol != 'mesero':
        # Opcional: puedes redirigir a una página de 'acceso denegado'
        return redirect('usuarios:login') 
    return render(request, 'usuarios/dashboard_mesero.html')
# -----------------------------
# Vistas de recuperación de contraseña
# -----------------------------
def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = Usuario.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(f'/usuarios/reset/{uid}/{token}/')
            message = f"Para restablecer tu contraseña, ingresa aquí: {reset_url}"
            send_mail(
                'Restablece tu contraseña',
                message,
                'pantojacarlos2003@gmail.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, "Se ha enviado un enlace de recuperación a tu correo.")
        except Usuario.DoesNotExist:
            messages.error(request, "No existe un usuario con ese correo.")
    return render(request, "usuarios/password_reset.html")


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            
            print("="*50)
            print(f"DEBUG: Password recibida: '{password}'")
            print(f"DEBUG: Password2 recibida: '{password2}'")
            print(f"DEBUG: Son iguales: {password == password2}")
            print("="*50)
            
            if password == password2:
                print(f"DEBUG: Guardando contraseña para usuario: {user.username}")
                user.set_password(password)
                user.save()
                
                user.refresh_from_db()
                verificacion = user.check_password(password)
                print(f"DEBUG: Verificación inmediata: {verificacion}")
                print("="*50)
                
                messages.success(request, "Contraseña restablecida correctamente.")
                return redirect('usuarios:login')
            else:
                messages.error(request, "Las contraseñas no coinciden.")
        return render(request, "usuarios/password_reset_confirm.html", {"validlink": True})
    else:
        messages.error(request, "El enlace no es válido o ha expirado.")
        return render(request, "usuarios/password_reset_confirm.html", {"validlink": False})
     


