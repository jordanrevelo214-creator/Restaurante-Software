from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'numero_documento', 'tipo_documento', 'email', 'telefono')
    search_fields = ('nombres', 'numero_documento')
    list_filter = ('tipo_documento',)
