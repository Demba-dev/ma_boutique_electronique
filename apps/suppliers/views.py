from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Supplier
from .forms import SupplierForm
from django.db.models import Sum, Count, F
from django.utils import timezone
from apps.purchases.models import Purchase, PurchasePayment
from apps.accounts.decorators import admin_required

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all().annotate(
        products_count=Count('products', distinct=True)
    )

     # Statistiques
    active_count = suppliers.filter(is_active=True).count()
    total_balance = suppliers.aggregate(total=Sum('balance'))['total'] or 0
    countries = suppliers.exclude(country='').values_list('country', flat=True).distinct()
    
    # Calculer le pourcentage de balance pour chaque fournisseur (exemple)
    max_balance = suppliers.aggregate(max=Sum('balance'))['max'] or 1
    for supplier in suppliers:
        if max_balance > 0:
            supplier.balance_percentage = (supplier.balance / max_balance) * 100
        else:
            supplier.balance_percentage = 0

    context = {
        'suppliers': suppliers,
        'active_count': active_count,
        'total_balance': total_balance,
        'countries': countries,
        'countries_count': countries.count(),
    }


    return render(request, 'suppliers/supplier_list.html', context)


@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('suppliers:supplier_list')
    else:
        form = SupplierForm()

    return render(request, 'suppliers/supplier_form.html', {'form': form})


@login_required
@admin_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('suppliers:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'supplier': supplier})

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    purchases_qs = Purchase.objects.filter(supplier=supplier).select_related('created_by').order_by('-created_at')

    purchases_count = purchases_qs.count()
    total_purchases = purchases_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid = purchases_qs.aggregate(total=Sum('amount_paid'))['total'] or 0
    paid_percentage = (total_paid / total_purchases * 100) if total_purchases else 0

    last_purchase = purchases_qs.first()
    last_purchase_date = last_purchase.created_at.strftime("%d/%m/%Y") if last_purchase else "-"
    days_since_last_purchase = (timezone.now() - last_purchase.created_at).days if last_purchase else "-"

    recent_purchases = purchases_qs[:10]
    recent_payments = PurchasePayment.objects.filter(supplier=supplier).select_related('purchase').order_by('-created_at')[:10]
    unpaid_purchases = purchases_qs.filter(total_amount__gt=F('amount_paid')).order_by('-created_at')

    context = {
        'supplier': supplier,
        'purchases_count': purchases_count,
        'total_purchases': total_purchases,
        'total_paid': total_paid,
        'paid_percentage': paid_percentage,
        'last_purchase_date': last_purchase_date,
        'days_since_last_purchase': days_since_last_purchase,
        'recent_purchases': recent_purchases,
        'recent_payments': recent_payments,
        'unpaid_purchases': unpaid_purchases,
    }
    return render(request, 'suppliers/supplier_detail.html', context)



@login_required
@admin_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        return redirect('suppliers:supplier_list')
    return render(request, 'suppliers/supplier_confirm_delete.html', {'supplier': supplier})
