from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Sale, SaleItem, SalePayment
from .forms import SaleForm, SaleItemFormSet
from django.db import transaction
from datetime import datetime,timedelta
from django.db.models import Sum, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from apps.products.models import Product
from apps.clients.models import Client



def sale_list(request):
    sales = Sale.objects.all().order_by('-created_at')

    # Calcul des statistiques
    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid = sales.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_credit = total_revenue - total_paid

    
    # Ventes d'aujourd'hui
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_sales = sales.filter(created_at__gte=today_start).count()
    
    # Pagination
    paginator = Paginator(sales, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'sales': page_obj,
        'total_revenue': total_revenue,
        'total_credit': total_credit,
        'today_sales': today_sales,
    }
    return render(request, 'sales/sale_list.html', context)


def sale_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        formset = SaleItemFormSet(request.POST, prefix='items')

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    sale = form.save(commit=False)
                    sale.created_by = request.user
                    sale.save()

                    formset.instance = sale
                    formset.save()
                    
                    # Forcer le calcul final
                    sale.update_total_amount()

                    if sale.amount_paid and sale.amount_paid > 0:
                        SalePayment.objects.create(
                            sale=sale,
                            client=sale.client,
                            amount=sale.amount_paid,
                            method='cash',
                            reference=None,
                            balance_after=sale.client.balance if sale.client else None,
                            created_by=request.user,
                        )

                    messages.success(request, "Vente enregistrée avec succès.")
                    return redirect('sales:sale_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'enregistrement : {e}")
        else:
            # Afficher les erreurs de validation détaillées (incluant le formset)
            error_msg = "Veuillez corriger les erreurs dans le formulaire."
            if form.errors:
                error_msg += f" [Vente: {form.errors.as_text()}]"
            if formset.errors:
                # Les erreurs du formset sont une liste de dictionnaires
                items_errors = [e.as_text() for e in formset.errors if e]
                if items_errors:
                    error_msg += f" [Produits: {' | '.join(items_errors)}]"
            messages.error(request, error_msg)

    else:
        form = SaleForm()
        formset = SaleItemFormSet(prefix='items')

    return render(request, 'sales/sale_form.html', {'form': form, 'formset': formset})


def sale_detail(request, pk):
    sale = get_object_or_404(
        Sale.objects.select_related('client', 'created_by')
        .prefetch_related('items__product', 'payments'),
        pk=pk
    )
    payments = sale.payments.all().order_by('-created_at')
    return render(request, 'sales/sale_detail.html', {'sale': sale, 'payments': payments})


def sale_receipt(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('client', 'created_by').prefetch_related('items__product'), pk=pk)
    return render(request, 'sales/sale_receipt.html', {'sale': sale})


def payment_receipt(request, pk):
    payment = get_object_or_404(
        SalePayment.objects.select_related('sale', 'client', 'created_by'),
        pk=pk
    )
    sale = payment.sale
    total_paid_to_payment = SalePayment.objects.filter(
        sale=sale,
        id__lte=payment.id,
    ).aggregate(total=Sum('amount'))['total'] or 0
    remaining_after = sale.total_amount - total_paid_to_payment

    context = {
        'payment': payment,
        'sale': sale,
        'total_paid_to_payment': total_paid_to_payment,
        'remaining_after': remaining_after,
    }
    return render(request, 'sales/payment_receipt.html', context)

@login_required
@require_POST
def sale_record_payment(request, pk):
    sale = get_object_or_404(Sale, pk=pk)

    try:
        amount = Decimal(request.POST.get('amount', '0'))
    except (InvalidOperation, TypeError):
        return JsonResponse({'ok': False, 'error': 'Montant invalide.'}, status=400)

    if amount <= 0:
        return JsonResponse({'ok': False, 'error': 'Le montant doit être supérieur à 0.'}, status=400)

    remaining = sale.remaining_amount
    if remaining <= 0:
        return JsonResponse({'ok': False, 'error': 'Cette vente est déjà entièrement payée.'}, status=400)

    if amount > remaining:
        return JsonResponse({'ok': False, 'error': 'Le montant dépasse le reste à payer.'}, status=400)

    method = request.POST.get('method', 'cash')
    reference = request.POST.get('reference') or None
    if method not in dict(SalePayment.METHOD_CHOICES):
        method = 'cash'

    with transaction.atomic():
        sale.amount_paid = (sale.amount_paid or 0) + amount
        sale.save(update_fields=['amount_paid'])
        sale.recalculate_client_balance()
        payment = SalePayment.objects.create(
            sale=sale,
            client=sale.client,
            amount=amount,
            method=method,
            reference=reference,
            balance_after=sale.client.balance if sale.client else None,
            created_by=request.user,
        )

    return JsonResponse({
        'ok': True,
        'amount_paid': float(sale.amount_paid),
        'remaining_amount': float(sale.remaining_amount),
        'payment_id': payment.id,
    })


@login_required
def cart_checkout(request):
    cart = request.session.get('cart', {})

    if request.method == 'POST':
        action = request.POST.get('action', 'checkout')

        # Mettre à jour les quantités depuis le formulaire
        updated_cart = {}
        for pid, qty in cart.items():
            try:
                new_qty = int(request.POST.get(f'qty_{pid}', qty))
            except (TypeError, ValueError):
                new_qty = qty
            if new_qty > 0:
                updated_cart[pid] = new_qty

        if action == 'clear':
            request.session['cart'] = {}
            request.session.modified = True
            messages.success(request, "Panier vidé.")
            return redirect('sales:cart_checkout')

        cart = updated_cart
        request.session['cart'] = cart
        request.session.modified = True

        if action == 'update':
            messages.success(request, "Panier mis à jour.")
            return redirect('sales:cart_checkout')

    product_ids = [int(pid) for pid in cart.keys()] if cart else []
    products = Product.objects.filter(id__in=product_ids)

    items = []
    total_amount = Decimal('0')
    stock_errors = []

    for product in products:
        qty = int(cart.get(str(product.id), 0))
        if qty <= 0:
            continue
        if product.stock_quantity < qty:
            stock_errors.append(f"Stock insuffisant pour {product.name} (disponible: {product.stock_quantity}).")
        subtotal = product.selling_price * qty
        total_amount += subtotal
        items.append({
            'product': product,
            'qty': qty,
            'price': product.selling_price,
            'subtotal': subtotal,
            'stock': product.stock_quantity,
        })

    if request.method == 'POST':
        if not items:
            messages.error(request, "Votre panier est vide.")
            return redirect('sales:cart_checkout')

        if stock_errors:
            for err in stock_errors:
                messages.error(request, err)
            return redirect('sales:cart_checkout')

        client_id = request.POST.get('client') or None
        if not client_id:
            messages.error(request, "Veuillez sélectionner un client.")
            return redirect('sales:cart_checkout')
        try:
            amount_paid = Decimal(request.POST.get('amount_paid', '0'))
        except (InvalidOperation, TypeError):
            amount_paid = Decimal('0')

        if amount_paid < 0:
            messages.error(request, "Le montant payé est invalide.")
            return redirect('sales:cart_checkout')

        if amount_paid > total_amount:
            messages.error(request, "Le montant payé dépasse le total.")
            return redirect('sales:cart_checkout')

        with transaction.atomic():
            sale = Sale(
                client_id=client_id,
                amount_paid=amount_paid,
                created_by=request.user,
            )
            sale.save()

            for item in items:
                SaleItem.objects.create(
                    sale=sale,
                    product=item['product'],
                    quantity=item['qty'],
                    price=item['price'],
                    subtotal=item['subtotal'],
                )

            sale.update_total_amount()
            if sale.amount_paid and sale.amount_paid > 0:
                SalePayment.objects.create(
                    sale=sale,
                    client=sale.client,
                    amount=sale.amount_paid,
                    method='cash',
                    reference=None,
                    balance_after=sale.client.balance if sale.client else None,
                    created_by=request.user,
                )

        request.session['cart'] = {}
        request.session.modified = True
        messages.success(request, "Vente enregistrée avec succès.")
        return redirect('sales:sale_list')

    clients = Client.objects.all().order_by('name')
    selected_client_id = request.POST.get('client') or request.GET.get('client')
    context = {
        'items': items,
        'total_amount': total_amount,
        'clients': clients,
        'selected_client_id': selected_client_id,
    }
    return render(request, 'sales/cart_checkout.html', context)
