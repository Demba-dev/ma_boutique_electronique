from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Category, Product
from django.db.models import F
from .forms import CategoryForm, ProductForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Count
from apps.accounts.decorators import admin_required, role_required


# -------------------------
# Categories
# -------------------------
@login_required
def category_list(request):
    categories = Category.objects.annotate(
        products_count=Count('products')
    ).order_by('name')
    
    # Statistiques
    total_products = Product.objects.count()
    
    # Pagination
    paginator = Paginator(categories, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categories': page_obj,
        'total_products': total_products,
    }
    return render(request, 'products/category_list.html', context)

@login_required
@role_required(['admin', 'manager'])
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('products:category_list')
    else:
        form = CategoryForm()
    return render(request, 'products/category_form.html', {'form': form})

@login_required
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    products = category.products.all().select_related('category').order_by('name')
    low_stock_count = products.filter(stock_quantity__lte=F('low_stock_threshold')).count()
    in_stock_count = products.filter(stock_quantity__gt=0).count()

    context = {
        'category': category,
        'products': products,
        'total_products': products.count(),
        'low_stock_count': low_stock_count,
        'in_stock_count': in_stock_count,
    }
    return render(request, 'products/category_detail.html', context)

@login_required
@admin_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('products:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'products/category_form.html', {'form': form, 'category': category})

@login_required
@admin_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('products:category_list')
    return render(request, 'products/category_confirm_delete.html', {'category': category})

# -------------------------
# Products
# -------------------------
@login_required
def product_list(request):
    products = Product.objects.all().select_related('category', 'supplier')
    categories = Category.objects.all()
    low_stock_products = products.filter(stock_quantity__lte=F('low_stock_threshold'))

    context = {
        'products': products,
        'categories': categories,
        'low_stock_products': low_stock_products,
        'in_stock_count': products.filter(stock_quantity__gt=0).count(),
        'low_stock_count': low_stock_products.count(),
    }
    return render(request, 'products/product_list.html', context)

@login_required
@role_required(['admin', 'manager'])
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.updated_by = request.user
            product.save()
            return redirect('products:product_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    selling_price = product.selling_price or 0
    purchase_price = product.purchase_price or 0
    margin = selling_price - purchase_price
    context = {
        'product': product,
        'margin': margin,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
@admin_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)
            updated_product.updated_by = request.user
            updated_product.save()
            return redirect('products:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form, 'product': product})


@login_required
@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('products:product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})


@login_required
@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity <= 0:
        return JsonResponse({'ok': False, 'error': 'Quantité invalide.'}, status=400)

    cart = request.session.get('cart', {})
    key = str(product.id)
    cart[key] = cart.get(key, 0) + quantity
    request.session['cart'] = cart
    request.session.modified = True

    total_qty = sum(cart.values())
    return JsonResponse({'ok': True, 'total_qty': total_qty})


@login_required
def cart_summary(request):
    cart = request.session.get('cart', {})
    product_ids = [int(pid) for pid in cart.keys()] if cart else []
    products = Product.objects.filter(id__in=product_ids).only('id', 'name', 'selling_price')

    items = []
    total_qty = 0
    total_amount = 0
    for product in products:
        qty = cart.get(str(product.id), 0)
        subtotal = product.selling_price * qty
        total_qty += qty
        total_amount += subtotal
        items.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.selling_price),
            'qty': qty,
            'subtotal': float(subtotal),
        })

    return JsonResponse({
        'ok': True,
        'total_qty': total_qty,
        'total_amount': float(total_amount),
        'items': items,
    })
