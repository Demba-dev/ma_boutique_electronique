from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Count
from django.db.models.functions import TruncDate
from django.conf import settings

from apps.accounts.froms import UserCreateForm, ShopSettingsForm
from apps.core.models import ShopSettings
from django.db.utils import OperationalError
from apps.sales.models import Sale, SaleItem
from apps.products.models import Product
from apps.clients.models import Client
from apps.stock.models import StockMovement
import json

# Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('accounts:home')
        else:
            messages.error(request, 'Nom d’utilisateur ou mot de passe incorrect.')
    return render(request, 'accounts/login.html')


# Logout
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


# home
@login_required
def home(request):
    user = request.user
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_end = month_start
    prev_month_start = (month_start - timezone.timedelta(days=1)).replace(day=1)

    context = {'user': user}

    if user.role == 'admin':
        revenue_month = Sale.objects.filter(created_at__gte=month_start).aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_prev = Sale.objects.filter(created_at__gte=prev_month_start, created_at__lt=prev_month_end).aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_change = ((revenue_month - revenue_prev) / revenue_prev * 100) if revenue_prev else None

        products_in_stock = Product.objects.filter(stock_quantity__gt=0).count()
        out_of_stock = Product.objects.filter(stock_quantity=0).count()

        active_clients = Client.objects.filter(is_active=True).count()
        new_clients = Client.objects.filter(created_at__gte=month_start).count()

        profit_expr = ExpressionWrapper(
            (F('price') - F('product__purchase_price')) * F('quantity'),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )
        profit_month = SaleItem.objects.filter(sale__created_at__gte=month_start).aggregate(total=Sum(profit_expr))['total'] or 0
        profit_prev = SaleItem.objects.filter(sale__created_at__gte=prev_month_start, sale__created_at__lt=prev_month_end).aggregate(total=Sum(profit_expr))['total'] or 0
        profit_change = ((profit_month - profit_prev) / profit_prev * 100) if profit_prev else None

        # Ventes des 7 derniers jours
        start_date = (now - timezone.timedelta(days=6)).date()
        sales_by_day = (
            Sale.objects.filter(created_at__date__gte=start_date)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Sum('total_amount'))
            .order_by('day')
        )
        sales_map = {row['day']: float(row['total'] or 0) for row in sales_by_day}
        sales_labels = []
        sales_values = []
        for i in range(7):
            d = start_date + timezone.timedelta(days=i)
            sales_labels.append(d.strftime('%d/%m'))
            sales_values.append(sales_map.get(d, 0))

        # Répartition des ventes par catégorie
        category_sales = (
            SaleItem.objects.select_related('product__category')
            .values('product__category__name')
            .annotate(total=Sum('subtotal'))
            .order_by('-total')
        )
        category_labels = [row['product__category__name'] or 'Sans catégorie' for row in category_sales]
        category_values = [float(row['total'] or 0) for row in category_sales]

        recent_sales = Sale.objects.select_related('client', 'created_by').order_by('-created_at')[:5]
        recent_stock = StockMovement.objects.select_related('product', 'created_by').order_by('-created_at')[:5]

        context.update({
            'revenue_month': revenue_month,
            'revenue_change': revenue_change,
            'products_in_stock': products_in_stock,
            'out_of_stock': out_of_stock,
            'active_clients': active_clients,
            'new_clients': new_clients,
            'profit_month': profit_month,
            'profit_change': profit_change,
            'sales_chart_labels': json.dumps(sales_labels),
            'sales_chart_values': json.dumps(sales_values),
            'category_chart_labels': json.dumps(category_labels),
            'category_chart_values': json.dumps(category_values),
            'recent_sales': recent_sales,
            'recent_stock': recent_stock,
        })

    elif user.role == 'manager':
        stock_value_expr = ExpressionWrapper(
            F('purchase_price') * F('stock_quantity'),
            output_field=DecimalField(max_digits=16, decimal_places=2)
        )
        stock_value = Product.objects.aggregate(total=Sum(stock_value_expr))['total'] or 0
        low_stock_count = Product.objects.filter(stock_quantity__lte=F('low_stock_threshold')).count()
        incoming_week = StockMovement.objects.filter(type='IN', created_at__gte=now - timezone.timedelta(days=7)).count()
        low_stock_products = Product.objects.filter(stock_quantity__lte=F('low_stock_threshold')).order_by('stock_quantity')[:5]
        recent_movements = StockMovement.objects.select_related('product').order_by('-created_at')[:5]

        context.update({
            'stock_value': stock_value,
            'low_stock_count': low_stock_count,
            'incoming_week': incoming_week,
            'low_stock_products': low_stock_products,
            'recent_movements': recent_movements,
        })

    else:
        sales_today = Sale.objects.filter(created_at__gte=today_start, created_by=user)
        sales_today_count = sales_today.count()
        sales_today_amount = sales_today.aggregate(total=Sum('total_amount'))['total'] or 0

        sales_month = Sale.objects.filter(created_at__gte=month_start, created_by=user)
        sales_month_amount = sales_month.aggregate(total=Sum('total_amount'))['total'] or 0

        target = getattr(settings, 'SELLER_MONTH_TARGET', 2000000)
        progress = (sales_month_amount / target * 100) if target else 0
        progress = min(progress, 100)

        recent_sales = Sale.objects.filter(created_by=user).select_related('client').order_by('-created_at')[:5]

        context.update({
            'sales_today_count': sales_today_count,
            'sales_today_amount': sales_today_amount,
            'sales_month_amount': sales_month_amount,
            'sales_month_target': target,
            'sales_month_progress': progress,
            'recent_sales': recent_sales,
        })

    return render(request, 'accounts/dashboard.html', context)


@login_required
def create_user(request):
    if request.user.role != 'admin':
        return redirect('accounts:home')  # seulement admin

    if request.method == 'POST':
        form = UserCreateForm(request.POST, allowed_roles=['manager', 'seller'])
        if form.is_valid():
            form.save()
            return redirect('accounts:settings_list') # Rediriger vers settings
    else:
        form = UserCreateForm(allowed_roles=['manager', 'seller'])

    return render(request, 'accounts/create_user.html', {'form': form})


from apps.accounts.models import CustomUser

@login_required
def settings_list(request):
    user = request.user
    users = None
    if user.role == 'admin':
        users = CustomUser.objects.all().order_by('-created_at')

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    profit_expr = ExpressionWrapper(
        (F('price') - F('product__purchase_price')) * F('quantity'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    daily_net_profit = SaleItem.objects.filter(
        sale__created_at__gte=today_start
    ).aggregate(total=Sum(profit_expr))['total'] or 0

    try:
        shop_settings = ShopSettings.get_solo()
    except OperationalError:
        shop_settings = None

    if request.method == 'POST' and request.POST.get('form_type') == 'shop_settings':
        if user.role != 'admin':
            messages.error(request, "Accès refusé.")
            return redirect('accounts:settings_list')
        shop_form = ShopSettingsForm(request.POST, request.FILES, instance=shop_settings)
        if shop_form.is_valid():
            obj = shop_form.save(commit=False)
            obj.updated_by = user
            obj.save()
            messages.success(request, "Paramètres de la boutique enregistrés.")
            return redirect('accounts:settings_list')
    else:
        shop_form = ShopSettingsForm(instance=shop_settings)

    context = {
        'user_profile': user,
        'users': users,
        'roles': CustomUser.ROLE_CHOICES,
        'shop_form': shop_form,
        'daily_net_profit': daily_net_profit,
    }
    return render(request, 'accounts/settings_list.html', context)
