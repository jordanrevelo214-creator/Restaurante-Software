
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('mesero', 'Mesero'),
    ]
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='mesero')
    