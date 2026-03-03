from django.db import models
from django.conf import settings


class ShopSettings(models.Model):
    CURRENCY_CHOICES = (
        ('FCFA', 'FCFA (Franc CFA)'),
        ('EUR', 'EUR (Euro)'),
        ('USD', 'USD (Dollar US)'),
    )

    name = models.CharField(max_length=200, default='Diaby Electronic')
    logo = models.ImageField(upload_to='shop/', blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='FCFA')
    ninea = models.CharField(max_length=50, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_shop_settings'
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
