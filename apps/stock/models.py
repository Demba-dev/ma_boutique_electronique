from django.db import models
from django.conf import settings
from apps.products.models import Product


class StockMovement(models.Model):

    MOVEMENT_TYPES = (
        ('IN', 'Entrée'),
        ('OUT', 'Sortie'),
        ('ADJUSTMENT', 'Ajustement'),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )

    type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.PositiveIntegerField()
    reference = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        # Seulement lors de la création
        if not self.pk:

            if self.type == 'IN':
                self.product.stock_quantity += self.quantity

            elif self.type == 'OUT':
                if self.product.stock_quantity < self.quantity:
                    raise ValueError("Stock insuffisant.")
                self.product.stock_quantity -= self.quantity

            elif self.type == 'ADJUSTMENT':
                self.product.stock_quantity = self.quantity

            self.product.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.type} - {self.quantity}"