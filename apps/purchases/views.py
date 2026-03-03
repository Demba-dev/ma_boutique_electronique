from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation
from datetime import date

from .models import Purchase, PurchasePayment
from .forms import PurchaseForm, PurchaseItemFormSet


@login_required
def purchase_list(request):
    purchases = Purchase.objects.select_related('supplier', 'created_by').order_by('-created_at')
    total_amount = purchases.aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid = purchases.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_due = total_amount - total_paid


    paginator = Paginator(purchases, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'purchases': page_obj,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_due,
    
    }
    return render(request, 'purchases/purchase_list.html', context)


@login_required
def purchase_create(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        formset = PurchaseItemFormSet(request.POST, prefix='items')

        if form.is_valid() and formset.is_valid():
            # Valider qu'au moins un produit est saisi
            items_data = [
                f.cleaned_data for f in formset
                if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('product')
            ]
            if not items_data:
                messages.error(request, "Ajoutez au moins un produit à l'achat.")
                return render(request, 'purchases/purchase_form.html', {'form': form, 'formset': formset})

            expected_total = sum((item['quantity'] * item['unit_cost']) for item in items_data)
            amount_paid = form.cleaned_data.get('amount_paid') or 0
            if amount_paid > expected_total:
                messages.error(request, "Le montant payé dépasse le total de l'achat.")
                return render(request, 'purchases/purchase_form.html', {'form': form, 'formset': formset})

            try:
                with transaction.atomic():
                    purchase = form.save(commit=False)
                    purchase.created_by = request.user
                    purchase.save()

                    formset.instance = purchase
                    formset.save()

                    purchase.update_total_amount()

                    if purchase.amount_paid and purchase.amount_paid > 0:
                        purchase.recalculate_supplier_balance()
                        PurchasePayment.objects.create(
                            purchase=purchase,
                            supplier=purchase.supplier,
                            amount=purchase.amount_paid,
                            method='cash',
                            reference=None,
                            payment_date=None,
                            notes='',
                            balance_after=purchase.supplier.balance if purchase.supplier else None,
                            created_by=request.user,
                        )

                    messages.success(request, "Achat enregistré avec succès.")
                    return redirect('purchases:purchase_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'enregistrement : {e}")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = PurchaseForm()
        formset = PurchaseItemFormSet(prefix='items')

    return render(request, 'purchases/purchase_form.html', {'form': form, 'formset': formset})


@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(
        Purchase.objects.select_related('supplier', 'created_by').prefetch_related('items__product', 'payments'),
        pk=pk
    )
    payments = purchase.payments.all().order_by('-created_at')
    return render(request, 'purchases/purchase_detail.html', {'purchase': purchase, 'payments': payments})


@login_required
def purchase_receipt(request, pk):
    purchase = get_object_or_404(
        Purchase.objects.select_related('supplier', 'created_by').prefetch_related('items__product'),
        pk=pk
    )
    return render(request, 'purchases/purchase_receipt.html', {'purchase': purchase})


@login_required
@require_POST
def purchase_record_payment(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)

    try:
        amount = Decimal(request.POST.get('amount', '0'))
    except (InvalidOperation, TypeError):
        return JsonResponse({'ok': False, 'error': 'Montant invalide.'}, status=400)

    if amount <= 0:
        return JsonResponse({'ok': False, 'error': 'Le montant doit être supérieur à 0.'}, status=400)

    remaining = purchase.remaining_amount
    if remaining <= 0:
        return JsonResponse({'ok': False, 'error': 'Cet achat est déjà entièrement payé.'}, status=400)

    if amount > remaining:
        return JsonResponse({'ok': False, 'error': 'Le montant dépasse le reste à payer.'}, status=400)

    method = request.POST.get('method', 'cash')
    reference = request.POST.get('reference') or None
    notes = request.POST.get('notes') or ''
    payment_date_str = request.POST.get('payment_date') or None
    payment_date = None
    if payment_date_str:
        try:
            payment_date = date.fromisoformat(payment_date_str)
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'Date de paiement invalide.'}, status=400)

    if method not in dict(PurchasePayment.METHOD_CHOICES):
        method = 'cash'

    with transaction.atomic():
        purchase.amount_paid = (purchase.amount_paid or 0) + amount
        purchase.save(update_fields=['amount_paid'])
        purchase.recalculate_supplier_balance()
        payment = PurchasePayment.objects.create(
            purchase=purchase,
            supplier=purchase.supplier,
            amount=amount,
            method=method,
            reference=reference,
            payment_date=payment_date,
            notes=notes,
            balance_after=purchase.supplier.balance if purchase.supplier else None,
            created_by=request.user,
        )

    return JsonResponse({
        'ok': True,
        'amount_paid': float(purchase.amount_paid),
        'remaining_amount': float(purchase.remaining_amount),
        'payment_id': payment.id,
    })


@login_required
def purchase_payment_receipt(request, pk):
    payment = get_object_or_404(
        PurchasePayment.objects.select_related('purchase', 'supplier', 'created_by'),
        pk=pk
    )
    purchase = payment.purchase
    total_paid_to_payment = PurchasePayment.objects.filter(
        purchase=purchase,
        id__lte=payment.id,
    ).aggregate(total=Sum('amount'))['total'] or 0
    remaining_after = purchase.total_amount - total_paid_to_payment
    context = {
        'payment': payment,
        'purchase': purchase,
        'total_paid_to_payment': total_paid_to_payment,
        'remaining_after': remaining_after,
    }
    return render(request, 'purchases/purchase_payment_receipt.html', context)
