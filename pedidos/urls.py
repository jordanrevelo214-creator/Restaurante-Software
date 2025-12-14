
from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    path('mesa/<int:mesa_id>/', views.detalle_mesa, name='detalle_mesa'),
    path('agregar/<int:pedido_id>/<int:producto_id>/', views.agregar_producto, name='agregar_producto'),
    path('confirmar/<int:pedido_id>/', views.confirmar_pedido, name='confirmar_pedido'),
    path('pagar/<int:pedido_id>/', views.pagar_pedido, name='pagar_pedido'),
    path('cocina/', views.dashboard_cocina, name='dashboard_cocina'),
    path('cocina/terminar/<int:pedido_id>/', views.terminar_pedido, name='terminar_pedido'),
    path('modificar-cantidad/<int:item_id>/<str:accion>/', views.modificar_cantidad_item, name='modificar_cantidad'),
    path('cocina/actualizar/', views.actualizar_cocina, name='actualizar_cocina'),
    path('pedido/<int:pedido_id>/cobrar/', views.modal_cobrar, name='modal_cobrar'),
    path('pedido/<int:pedido_id>/pagar/', views.procesar_pago, name='procesar_pago'),
    path('factura/<int:factura_id>/ticket/', views.ver_ticket, name='ver_ticket'),
    path('', views.panel_mesas, name='panel_mesas'),
    
]