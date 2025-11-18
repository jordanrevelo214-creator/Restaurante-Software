

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, AuditLog

class CustomUserAdmin(UserAdmin):
    model = Usuario
    
    # 1. QUÉ VER EN LA LISTA
    list_display = ('username', 'email', 'rol', 'cedula', 'is_active')
    list_filter = ('rol', 'is_active')
    search_fields = ('username', 'email', 'cedula')

    # 2. PANTALLA DE EDICIÓN (Aquí SÍ mostramos todos tus campos personalizados)
    fieldsets = UserAdmin.fieldsets + (
        ('Información del Restaurante', {'fields': ('rol', 'cedula', 'telefono', 'direccion')}),
    )
    
    # 3. PANTALLA DE CREACIÓN (ADD USER)
    # Aquí usamos la configuración original de Django: Solo Usuario y Contraseña.
    # Esto evita el error rojo. Una vez guardes, te dejará editar lo demás.
    add_fieldsets = UserAdmin.add_fieldsets

    # --- Acciones y Permisos ---
    actions = ['desactivar_usuarios', 'activar_usuarios']

    @admin.action(description='Desactivar usuarios')
    def desactivar_usuarios(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='Reactivar usuarios')
    def activar_usuarios(self, request, queryset):
        queryset.update(is_active=True)

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Usuario, CustomUserAdmin)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    def has_delete_permission(self, request, obj=None):
        return False