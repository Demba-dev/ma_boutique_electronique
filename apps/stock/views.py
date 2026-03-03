from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.stock.models import StockMovement
from .forms import StockMovementForm
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
import random

def _generate_movement_reference():
    while True:
        now = timezone.now()
        date_part = now.strftime('%Y%m%d%H%M%S')
        random_part = f"{random.randint(0, 999):03d}"
        ref = f"MVT-{date_part}-{random_part}"
        if not StockMovement.objects.filter(reference=ref).exists():
            return ref

@login_required
def movement_print(request, pk):
    movement = get_object_or_404(StockMovement.objects.select_related('product', 'created_by'), pk=pk)
    return render(request, 'stock/movement_print.html', {'movement': movement})

@login_required
def movement_ajax_detail(request, pk):
    movement = get_object_or_404(StockMovement.objects.select_related('product', 'created_by'), pk=pk)
    return render(request, 'stock/includes/movement_detail_modal.html', {'movement': movement})

@login_required
def movement_list(request):
    movements = StockMovement.objects.all().select_related(
        'product', 'created_by'
    ).order_by('-created_at')


      # Statistiques
    total_in = movements.filter(type='IN').aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_out = movements.filter(type='OUT').aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_adjust = movements.filter(type='ADJUSTMENT').count()
    
    # Pagination
    paginator = Paginator(movements, 20)  # 20 mouvements par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'movements': page_obj,
        'total_in': total_in,
        'total_out': total_out,
        'total_adjust': total_adjust,
    }
    return render(request, 'stock/movement_list.html', context)

def create_stock_movement(request):

    if request.method == 'POST':
        form = StockMovementForm(request.POST)

        if form.is_valid():
            movement = form.save(commit=False)
            if not movement.reference:
                movement.reference = _generate_movement_reference()
            movement.created_by = request.user
            movement.save()

            messages.success(request, "Mouvement de stock enregistré avec succès.")
            return redirect('stock:movement_list')
    else:
        form = StockMovementForm(initial={'reference': _generate_movement_reference()})

    return render(request, 'stock/create_movement.html', {'form': form})
