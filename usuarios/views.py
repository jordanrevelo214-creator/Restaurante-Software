
# 📁 usuarios/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Sum
from django.contrib.auth.decorators import login_required
from django.utils import timezone 
from .models import Usuario, AuditLog
from pedidos.models import Pedido, Mesa
from pedidos.models import Producto, Factura, DetallePedido
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
                # Agregamos ?init_session=true para que el frontend active la "sessionStorage"
                if user.rol == 'mesero':
                    return redirect(reverse('usuarios:dashboard_mesero') + '?init_session=true')
                elif user.rol == 'cocina':
                    return redirect(reverse('pedidos:dashboard_cocina') + '?init_session=true')
                elif user.rol == 'gerente':
                    return redirect(reverse('usuarios:dashboard_gerente') + '?init_session=true')
                elif user.rol == 'admin':
                    return redirect('/admin/')
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
    
    # Usuarios ONLINE (Actividad en últimos 5 minutos)
    hace_5_minutos = timezone.now() - timezone.timedelta(minutes=5)
    usuarios_online = Usuario.objects.filter(last_activity__gte=hace_5_minutos).count()
    usuarios_activos = usuarios_online # Reemplazamos la variable para el template
    
    # Ventas de HOY
    hoy = timezone.now().date()
    pedidos_hoy = Pedido.objects.filter(created_at__date=hoy, estado='pagado')
    total_ventas_hoy = sum(p.total for p in pedidos_hoy)
    
    # Logs
    ultimos_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]

    # --- DATOS PARA GRÁFICOS ---
    
    # 1. Ventas de la Semana (Últimos 7 días)
    fechas_grafico = []
    ventas_grafico = []
    hoy = timezone.now().date()
    
    for i in range(6, -1, -1):
        fecha = hoy - timezone.timedelta(days=i)
        # Filtramos facturas de ese día
        venta_dia = Factura.objects.filter(fecha_emision__date=fecha).aggregate(Sum('total'))['total__sum'] or 0
        
        # Formato fecha: "Lun 12"
        fechas_grafico.append(fecha.strftime("%d/%m")) 
        ventas_grafico.append(float(venta_dia))

    top_productos_q = DetallePedido.objects.filter(pedido__estado='pagado') \
        .values('producto__nombre') \
        .annotate(total_vendido=Sum('cantidad')) \
        .order_by('-total_vendido')[:5]

    top_labels = [item['producto__nombre'] for item in top_productos_q]
    top_data = [item['total_vendido'] for item in top_productos_q]

    context = {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'total_ventas_hoy': total_ventas_hoy,
        'ultimos_logs': ultimos_logs,
        'pedidos_completados_hoy': pedidos_hoy.count(),
        
        # Datos JSON para JS
        'fechas_grafico': fechas_grafico,
        'ventas_grafico': ventas_grafico,
        'top_labels': top_labels,
        'top_data': top_data,
    }
    return render(request, 'usuarios/dashboard_gerente.html', context)

@login_required
def lista_usuarios(request):
    # Seguridad: Solo gerentes o admins
    if request.user.rol != 'gerente' and request.user.rol != 'admin':
        return redirect('usuarios:login')
        
    usuarios = Usuario.objects.all().order_by('-last_activity')
    time_threshold = timezone.now() - timezone.timedelta(minutes=5)

    return render(request, 'usuarios/lista_usuarios.html', {
        'usuarios': usuarios,
        'time_threshold': time_threshold
    })

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
