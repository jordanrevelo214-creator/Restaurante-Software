
from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('mesero/', views.dashboard_mesero, name='dashboard_mesero'),
]