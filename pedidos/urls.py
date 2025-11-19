
from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    path('mesa/<int:mesa_id>/', views.detalle_mesa, name='detalle_mesa'),
    path('agregar/<int:pedido_id>/', views.agregar_producto, name='agregar_producto'),
    path('confirmar/<int:pedido_id>/', views.confirmar_pedido, name='confirmar_pedido'),
    path('cocina/', views.dashboard_cocina, name='dashboard_cocina'),
    path('cocina/terminar/<int:pedido_id>/', views.terminar_pedido, name='terminar_pedido'),
]