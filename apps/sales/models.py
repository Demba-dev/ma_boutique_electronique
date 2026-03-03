from django.db import models
from django.conf import settings
from apps.products.models import Product
from apps.clients.models import Client
from apps.stock.models import StockMovement
from django.core.exceptions import ValidationError
from django.db.models import Sum


class Sale(models.Model):
    invoice_number = models.CharField(max_length=20, unique=True, editable=False, null=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Générer un numéro de facture simple (ex: FAC-20231027-001)
            import datetime
            today = datetime.date.today()
            date_part = today.strftime('%Y%m%d')
            # Chercher la dernière vente de la journée pour incrémenter le compteur
            last_sale = Sale.objects.filter(invoice_number__contains=f"FAC-{date_part}").order_by('-id').first()
            if last_sale and last_sale.invoice_number:
                try:
                    last_num = int(last_sale.invoice_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.invoice_number = f"FAC-{date_part}-{new_num:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vente {self.invoice_number} - {self.client.name if self.client else 'Client inconnu'}"

    @property
    def remaining_amount(self):
        return self.total_amount - self.amount_paid

    def update_total_amount(self):
        # Calculer le total réel depuis la base de données de manière plus directe
        from django.db.models import Sum
        total_data = SaleItem.objects.filter(sale_id=self.pk).aggregate(total=Sum('subtotal'))
        total = total_data['total'] or 0
        
        # Mettre à jour directement en base
        Sale.objects.filter(pk=self.pk).update(total_amount=total)
        self.total_amount = total
        
        # Recalculer la balance du client
        if self.client:
            self.recalculate_client_balance()
        
        return total

    def recalculate_client_balance(self):
        if not self.client_id:
            return
        # Somme de toutes les ventes et tous les paiements du client
        totals = Sale.objects.filter(client_id=self.client_id).aggregate(
            total=Sum('total_amount'),
            paid=Sum('amount_paid'),
        )
        total_sales = totals['total'] or 0
        total_paid = totals['paid'] or 0
        # La balance représente ce que le client doit
        self.client.balance = total_sales - total_paid
        self.client.save(update_fields=['balance'])


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Vérifier stock
        if is_new and self.product.stock_quantity < self.quantity:
            raise ValidationError(f"Stock insuffisant pour {self.product.name}")

        # Calcul du subtotal
        self.subtotal = self.quantity * self.price
        super().save(*args, **kwargs)

        # Création mouvement stock
        if is_new:
            StockMovement.objects.create(
                product=self.product,
                type='OUT',
                quantity=self.quantity,
                reference=f"Vente #{self.sale.id}",
                created_by=self.sale.created_by
            )

        # Mettre à jour le total de la vente
        self.sale.update_total_amount()

        # Balance client recalculée via Sale.update_total_amount()


class SalePayment(models.Model):
    METHOD_CHOICES = (
        ('cash', 'Espèces'),
        ('mobile', 'Mobile Money'),
        ('card', 'Carte bancaire'),
        ('bank', 'Virement'),
    )

    sale = models.ForeignKey(Sale, related_name='payments', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    reference = models.CharField(max_length=100, blank=True, null=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.amount} FCFA - Vente {self.sale_id}"
