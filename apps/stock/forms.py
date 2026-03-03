from django import forms
from .models import StockMovement


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['product', 'type', 'quantity', 'reference', 'notes']