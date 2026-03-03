from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('create/', views.sale_create, name='sale_create'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/receipt/', views.sale_receipt, name='sale_receipt'),
    path('<int:pk>/payment/', views.sale_record_payment, name='sale_record_payment'),
    path('payments/<int:pk>/receipt/', views.payment_receipt, name='payment_receipt'),
]
