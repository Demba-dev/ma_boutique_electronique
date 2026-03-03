from django import forms
from .models import Sale, SaleItem
from django.forms import inlineformset_factory


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['client', 'amount_paid']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select select2'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount_paid'].required = False
        self.fields['amount_paid'].initial = 0
        self.fields['client'].required = True

    def clean_amount_paid(self):
        amount_paid = self.cleaned_data.get('amount_paid')
        if amount_paid is None:
            return 0
        return amount_paid


SaleItemFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    fields=('product', 'quantity', 'price'),
    extra=1,
    can_delete=True,
    widgets={
        'product': forms.Select(attrs={'class': 'form-select product-select'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': '1'}),
        'price': forms.NumberInput(attrs={'class': 'form-control price-input', 'min': '0'}),
    }
)
