
from django.db import models

class Cliente(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('cedula', 'Cédula'),
        ('ruc', 'RUC'),
        ('pasaporte', 'Pasaporte'),
        ('consumidor_final', 'Consumidor Final'),
    ]

    nombres = models.CharField(max_length=100, verbose_name="Nombres y Apellidos")
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES, default='cedula')
    numero_documento = models.CharField(max_length=13, unique=True, verbose_name="Número de Identificación")
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombres} ({self.numero_documento})"