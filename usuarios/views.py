
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
# 5. PASSWORD RESET REQUEST (solicitar reseteo con EMAIL)
def password_reset_request(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        
        try:
            # Buscar usuario por username o email
            user = Usuario.objects.get(Q(username=identifier) | Q(email=identifier))
            
            # Generar token
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from django.core.mail import send_mail
            from django.conf import settings
            
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Crear el link de reseteo
            reset_link = request.build_absolute_uri(
                f'/usuarios/password-reset-confirm/{uid}/{token}/'
            )
            
            # Enviar email
            subject = 'Recuperación de Contraseña - Restaurante'
            message = f'''
Hola {user.username},

Recibimos una solicitud para restablecer tu contraseña.

Haz clic en el siguiente enlace para crear una nueva contraseña:
{reset_link}

Si no solicitaste este cambio, puedes ignorar este mensaje.

Saludos,
Equipo del Restaurante
            '''
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, f'Se ha enviado un correo a {user.email} con las instrucciones para restablecer tu contraseña.')
            except Exception as e:
                messages.error(request, f'Error al enviar el correo: {str(e)}')
                
        except Usuario.DoesNotExist:
            # Por seguridad, mostramos el mismo mensaje aunque el usuario no exista
            messages.success(request, 'Si el usuario existe, recibirás un correo con las instrucciones.')
    
    return render(request, 'usuarios/password_reset.html')

# 6. PASSWORD RESET CONFIRM (cambiar contraseña)
def password_reset_confirm(request, uidb64, token):
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth.tokens import default_token_generator
    
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password and confirm_password:
                if len(new_password) < 6:
                    messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
                elif new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, '¡Contraseña cambiada exitosamente! Ya puedes iniciar sesión.')
                    return redirect('usuarios:login')
                else:
                    messages.error(request, 'Las contraseñas no coinciden.')
            else:
                messages.error(request, 'Por favor completa ambos campos.')
        
        return render(request, 'usuarios/password_reset_confirm.html', {'validlink': True, 'user': user})
    else:
        messages.error(request, 'El enlace de reseteo es inválido o ha expirado.')
        return render(request, 'usuarios/password_reset_confirm.html', {'validlink': False})