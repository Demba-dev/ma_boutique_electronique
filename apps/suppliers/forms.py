from django import forms
from .models import Supplier

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name',
            'company_name',
            'phone',
            'email',
            'address',
            'country',
            'balance',
            'is_active',
        ]
