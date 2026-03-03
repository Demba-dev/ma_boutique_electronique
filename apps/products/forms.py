from django import forms
from .models import Product, Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'supplier', 'name', 'brand', 'description',
            'purchase_price', 'selling_price', 'min_selling_price',
            'stock_quantity', 'low_stock_threshold', 'unit',
            'has_imei', 'imei', 'image'
        ]
