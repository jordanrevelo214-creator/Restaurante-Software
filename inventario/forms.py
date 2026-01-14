from django import forms
from .models import Insumo, MovimientoKardex

class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        # AGREGADOS: stock_actual y costo_unitario para que el gerente pueda editarlos
        fields = ['nombre', 'unidad_medida', 'stock_actual', 'costo_unitario', 'stock_minimo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'style': 'width: 100%; padding: 8px;'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select', 'style': 'width: 100%; padding: 8px;'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-input', 'style': 'width: 100%; padding: 8px;'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-input', 'style': 'width: 100%; padding: 8px;'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-input', 'style': 'width: 100%; padding: 8px;'}),
        }

class MovimientoKardexForm(forms.ModelForm):
    class Meta:
        model = MovimientoKardex
        fields = ['insumo', 'tipo', 'cantidad', 'costo_total', 'observacion']
        widgets = {
            'insumo': forms.Select(attrs={'class': 'form-select', 'style': 'width: 100%; padding: 8px;'}),
            'tipo': forms.Select(attrs={'class': 'form-select', 'style': 'width: 100%; padding: 8px;'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-input', 'style': 'width: 100%; padding: 8px;'}),
            'costo_total': forms.NumberInput(attrs={'class': 'form-input', 'style': 'width: 100%; padding: 8px;'}),
            'observacion': forms.Textarea(attrs={'class': 'form-input', 'style': 'width: 100%; padding: 8px; height: 80px;'}),
        }
