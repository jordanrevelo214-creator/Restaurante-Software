
from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('buscar/', views.buscar_cliente, name='buscar_cliente'),
    path('asignar/<int:pedido_id>/<int:cliente_id>/', views.asignar_cliente, name='asignar_cliente'),
]