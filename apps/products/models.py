from django.db import models
from apps.suppliers.models import Supplier

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=150)
    brand = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    min_selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Prix minimum autorisé")
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    unit = models.CharField(max_length=20, default='Pièce', help_text="Ex: Pièce, Carton, Lot")
    has_imei = models.BooleanField(default=False)
    imei = models.CharField(max_length=50, blank=True, null=True, unique=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, related_name='products_created')
    updated_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, related_name='products_updated')

    def __str__(self):
        return self.name
