from django import forms
from django.forms import inlineformset_factory
from .models import Purchase, PurchaseItem


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'amount_paid']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount_paid'].required = False
        self.fields['amount_paid'].initial = 0
        self.fields['supplier'].required = True

    def clean_amount_paid(self):
        amount_paid = self.cleaned_data.get('amount_paid')
        if amount_paid is None:
            return 0
        return amount_paid


PurchaseItemFormSet = inlineformset_factory(
    Purchase,
    PurchaseItem,
    fields=('product', 'quantity', 'unit_cost'),
    extra=1,
    can_delete=True
)
