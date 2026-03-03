from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.purchase_list, name='purchase_list'),
    path('create/', views.purchase_create, name='purchase_create'),
    path('<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('<int:pk>/receipt/', views.purchase_receipt, name='purchase_receipt'),
    path('<int:pk>/payment/', views.purchase_record_payment, name='purchase_record_payment'),
    path('payments/<int:pk>/receipt/', views.purchase_payment_receipt, name='payment_receipt'),
]
