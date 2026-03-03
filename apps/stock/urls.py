from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('', views.movement_list, name='movement_list'),
    path('create/', views.create_stock_movement, name='create_movement'),
    path('ajax/detail/<int:pk>/', views.movement_ajax_detail, name='movement_ajax_detail'),
    path('movement/<int:pk>/print/', views.movement_print, name='movement_print'),
]