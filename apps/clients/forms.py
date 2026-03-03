from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'name', 'phone', 'email', 'address', 
            'balance', 'credit_limit', 'client_type', 
            'loyalty_level', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Mamadou Diallo'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 77 123 45 67'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'client@email.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse complète...'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'client_type': forms.Select(attrs={'class': 'form-select'}),
            'loyalty_level': forms.NumberInput(attrs={'class': 'form-range', 'type': 'range', 'min': '0', 'max': '5', 'step': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
