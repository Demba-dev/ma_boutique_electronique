from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'balance', 'address', 'created_at')
    search_fields = ('name', 'phone')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

