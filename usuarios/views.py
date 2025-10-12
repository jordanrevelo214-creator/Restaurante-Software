from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirigir según el rol
            if user.rol == 'admin':
                return redirect('admin:index')
            else:
                return redirect('pedidos:lista_pedidos')  # Nombre de la URL para meseros
        else:
            error = "Usuario o contraseña incorrectos"
            return render(request, 'usuarios/login.html', {'error': error})
    return render(request, 'usuarios/login.html')

@login_required
def dashboard_mesero(request):
    # Vista temporal para meseros (la reemplazaremos con la de pedidos)
    return render(request, 'usuarios/mesero_dashboard.html')