# 📁 usuarios/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, AuditLog

class CustomUserAdmin(UserAdmin):
    # Esto es lo básico para que el admin reconozca tu campo 'rol'
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('rol',)}),
    )
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('rol',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_staff')

# Registra tu modelo Usuario con esta configuración
admin.site.register(Usuario, CustomUserAdmin)

# Registra el AuditLog para poder verlo en el panel
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'timestamp')
    list_filter = ('action', 'user')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('user', 'action', 'ip_address', 'timestamp')