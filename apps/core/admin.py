from django.contrib import admin
from .models import ShopSettings


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'phone', 'email', 'updated_at')

# Register your models here.
