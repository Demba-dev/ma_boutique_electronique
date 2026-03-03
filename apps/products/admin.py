from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'supplier', 'brand', 'purchase_price', 
        'selling_price', 'stock_quantity', 'low_stock_threshold', 
        'has_imei', 'created_at'
    )
    list_filter = ('category', 'supplier', 'brand', 'has_imei')
    search_fields = ('name', 'brand', 'imei')
