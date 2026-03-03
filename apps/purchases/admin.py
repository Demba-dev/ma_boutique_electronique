from django.contrib import admin
from .models import Purchase, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('reference', 'supplier', 'total_amount', 'amount_paid', 'created_at')
    list_filter = ('supplier', 'created_at')
    search_fields = ('reference',)
    inlines = [PurchaseItemInline]
