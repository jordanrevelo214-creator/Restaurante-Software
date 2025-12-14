# 📁 clientes/views.py

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Cliente

@login_required
def buscar_cliente(request):
    query = request.GET.get('q', '')
    
    # 👇 Print para ver en la consola negra si llega la petición
    print(f"--- BUSCANDO CLIENTE: '{query}' ---")

    if not query:
        clientes = []
    else:
        # Usamos 'cedula_o_ruc' y 'nombres' que son los campos reales de tu modelo
        clientes = Cliente.objects.filter(
            Q(nombres__icontains=query) | 
            Q(cedula_o_ruc__icontains=query)
        )[:5] # Limitamos a 5 para no llenar la pantalla

    # 👇 Print para ver cuántos encontró
    print(f"--- CLIENTES ENCONTRADOS: {len(clientes)} ---")

    context = {'clientes': clientes}
    return render(request, 'clientes/partials/resultados_busqueda.html', context)