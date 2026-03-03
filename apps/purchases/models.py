from django.db import models
from django.conf import settings
from apps.products.models import Product
from apps.suppliers.models import Supplier
from apps.stock.models import StockMovement
from django.db.models import Sum
from django.core.exceptions import ValidationError


class Purchase(models.Model):
    reference = models.CharField(max_length=20, unique=True, editable=False, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='purchases')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            import datetime
            today = datetime.date.today()
            date_part = today.strftime('%Y%m%d')
            last_purchase = Purchase.objects.filter(reference__contains=f"ACH-{date_part}").order_by('-id').first()
            if last_purchase and last_purchase.reference:
                try:
                    last_num = int(last_purchase.reference.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.reference = f"ACH-{date_part}-{new_num:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Achat {self.reference}"

    @property
    def remaining_amount(self):
        return self.total_amount - self.amount_paid

    @property
    def payment_percentage(self):
        if not self.total_amount:
            return 0
        return (self.amount_paid / self.total_amount) * 100

    def update_total_amount(self):
        total_data = PurchaseItem.objects.filter(purchase_id=self.pk).aggregate(total=Sum('subtotal'))
        total = total_data['total'] or 0
        Purchase.objects.filter(pk=self.pk).update(total_amount=total)
        self.total_amount = total
        if self.supplier:
            self.recalculate_supplier_balance()
        return total

    def recalculate_supplier_balance(self):
        if not self.supplier_id:
            return
        totals = Purchase.objects.filter(supplier_id=self.supplier_id).aggregate(
            total=Sum('total_amount'),
            paid=Sum('amount_paid'),
        )
        total_purchases = totals['total'] or 0
        total_paid = totals['paid'] or 0
        self.supplier.balance = total_purchases - total_paid
        self.supplier.save(update_fields=['balance'])


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if self.quantity <= 0:
            raise ValidationError("La quantité doit être positive.")

        self.subtotal = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

        if is_new:
            StockMovement.objects.create(
                product=self.product,
                type='IN',
                quantity=self.quantity,
                reference=f"Achat {self.purchase.reference}",
                created_by=self.purchase.created_by
            )

        self.purchase.update_total_amount()


class PurchasePayment(models.Model):
    METHOD_CHOICES = (
        ('cash', 'Espèces'),
        ('bank', 'Virement bancaire'),
        ('check', 'Chèque'),
        ('mobile', 'Mobile Money'),
    )

    purchase = models.ForeignKey(Purchase, related_name='payments', on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    reference = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement achat {self.amount} FCFA - {self.purchase_id}"
