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


def login_view(request):
    # Si el usuario ya está autenticado, redirigirlo a su dashboard
    if request.user.is_authenticated:
        if request.user.rol == 'mesero':
            return redirect('usuarios:dashboard_mesero')
        elif request.user.rol == 'admin':
            return redirect('admin:index') # O un dashboard de admin si tienes uno
        # Añade otras redirecciones de rol si es necesario
        
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')

        if not identifier or not password:
            messages.error(request, 'Por favor, ingrese su usuario/correo y contraseña.')
            return render(request, 'usuarios/login.html')

        # [cite_start]Buscamos al usuario por 'username' O por 'email' [cite: 16]
        try:
            user_q = Usuario.objects.get(Q(username=identifier) | Q(email=identifier))
            
            # Autenticamos con el username real y la contraseña
            user = authenticate(request, username=user_q.username, password=password)

            if user is not None:
                login(request, user)
                # [cite_start]Redirigimos según el rol del usuario [cite: 19]
                if user.rol == 'mesero':
                    return redirect('usuarios:dashboard_mesero')
                elif user.rol == 'admin':
                    return redirect('admin:index')
                # Por si hay otros roles en el futuro
                else:
                    return redirect('/') 
            else:
                # [cite_start]Mensaje de error genérico para no dar pistas [cite: 18, 53]
                messages.error(request, 'Credenciales inválidas.')
        
        except Usuario.DoesNotExist:
            # [cite_start]Mismo mensaje genérico si el usuario no existe [cite: 18, 53]
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
            if password == password2:
                user.set_password(password)
                user.save()
                messages.success(request, "Contraseña restablecida correctamente.")
                return redirect('usuarios:login')
            else:
                messages.error(request, "Las contraseñas no coinciden.")
        return render(request, "usuarios/password_reset_confirm.html", {"validlink": True})
    else:
        messages.error(request, "El enlace no es válido o ha expirado.")
        return render(request, "usuarios/password_reset_confirm.html", {"validlink": False})
     


