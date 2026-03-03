from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Max, F
from django.db.models.functions import Coalesce
from .models import Client
from .forms import ClientForm
from apps.sales.models import Sale, SalePayment
from django.utils import timezone
from apps.accounts.decorators import admin_required


from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def client_quick_create(request):
    name = request.POST.get('name')
    phone = request.POST.get('phone')
    
    if not name or not phone:
        return JsonResponse({'success': False, 'error': 'Nom et téléphone requis'}, status=400)
    
    try:
        # Vérifier si le téléphone existe déjà
        if Client.objects.filter(phone=phone).exists():
            return JsonResponse({'success': False, 'error': 'Un client avec ce numéro existe déjà'}, status=400)
            
        client = Client.objects.create(
            name=name,
            phone=phone,
            created_by=request.user,
            updated_by=request.user
        )
        return JsonResponse({
            'success': True,
            'id': client.id,
            'name': client.name,
            'phone': client.phone,
            'balance': float(client.balance)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

from django.db import models

@login_required
def client_list(request):
    clients = Client.objects.annotate(
        purchases_count=Count('sale', distinct=True),
        total_spent=Coalesce(Sum('sale__total_amount'), 0, output_field=models.DecimalField()),
        last_purchase=Max('sale__created_at'),
    ).order_by('-created_at')

    active_count = clients.filter(is_active=True).count()
    vip_count = clients.filter(client_type='vip').count()
    total_balance = clients.aggregate(total=Sum('balance'))['total'] or 0

    context = {
        'clients': clients,
        'active_count': active_count,
        'vip_count': vip_count,
        'total_balance': total_balance,
    }
    return render(request, 'clients/client_list.html', context)


@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.updated_by = request.user
            client.save()
            messages.success(request, "Client ajouté avec succès.")
            return redirect('clients:client_list')
    else:
        form = ClientForm()

    return render(request, 'clients/client_form.html', {'form': form})


@login_required
@admin_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            client.updated_by = request.user
            client.save()
            messages.success(request, "Client modifié avec succès.")
            return redirect('clients:client_list')
    else:
        form = ClientForm(instance=client)

    return render(request, 'clients/client_form.html', {'form': form})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    sales_qs = Sale.objects.filter(client=client).select_related('created_by').prefetch_related('items').order_by('-created_at')

    total_purchases = sales_qs.count()
    total_spent = sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    avg_basket = total_spent / total_purchases if total_purchases else 0
    last_purchase = sales_qs.first()
    days_since_last_purchase = (timezone.now() - last_purchase.created_at).days if last_purchase else None

    recent_sales = sales_qs.annotate(items_count=Count('items')).order_by('-created_at')[:10]
    recent_payments = SalePayment.objects.filter(client=client).select_related('sale').order_by('-created_at')[:10]
    unpaid_sales = sales_qs.filter(total_amount__gt=F('amount_paid')).order_by('-created_at')

    context = {
        'client': client,
        'total_purchases': total_purchases,
        'total_spent': total_spent,
        'avg_basket': avg_basket,
        'last_purchase': last_purchase,
        'days_since_last_purchase': days_since_last_purchase,
        'recent_sales': recent_sales,
        'recent_payments': recent_payments,
        'unpaid_sales': unpaid_sales,
        'has_unpaid_sales': unpaid_sales.exists(),
    }
    return render(request, 'clients/client_detail.html', context)


@login_required
@admin_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        client.delete()
        messages.success(request, "Client supprimé.")
        return redirect('clients:client_list')

    return render(request, 'clients/client_confirm_delete.html', {'client': client})
