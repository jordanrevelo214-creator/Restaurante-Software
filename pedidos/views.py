from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def lista_pedidos(request):
    return render(request, 'pedidos/lista_pedidos.html')