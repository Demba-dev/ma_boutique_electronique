from django.db import models
from django.conf import settings


class Client(models.Model):
    CLIENT_TYPES = (
        ('regular', 'Client régulier'),
        ('vip', 'VIP'),
        ('wholesale', 'Grossiste'),
        ('new', 'Nouveau client'),
    )

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    balance = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=0, default=100000)
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES, default='regular')
    loyalty_level = models.IntegerField(default=0)  # 0 to 5
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clients_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clients_updated'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name