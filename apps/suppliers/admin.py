from django.contrib import admin
from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'company_name',
        'phone',
        'email',
        'country',
        'balance',
        'is_active',
        'created_at',
        'updated_at',
    )
    list_filter = ('is_active', 'country')
    search_fields = ('name', 'company_name', 'phone', 'email')
