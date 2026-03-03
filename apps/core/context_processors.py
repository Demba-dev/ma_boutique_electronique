from django.utils import timezone
from django.db.models import F
from apps.products.models import Product
from django.db.utils import OperationalError
from apps.core.models import ShopSettings


def sidebar_stats(request):
    low_stock_count = Product.objects.filter(
        stock_quantity__lte=F('low_stock_threshold')
    ).count()
    return {
        'low_stock_count': low_stock_count,
        'current_time': timezone.localtime(),
    }


def shop_settings(request):
    try:
        settings_obj = ShopSettings.get_solo()
    except OperationalError:
        settings_obj = None
    return {'shop_settings': settings_obj}
