
from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/mesero/', views.dashboard_mesero, name='dashboard_mesero'),
    # Aquí puedes agregar más URLs para otros dashboards (admin, etc.)
]

