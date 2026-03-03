from django.urls import path
from . import views


app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('create/', views.client_create, name='client_create'),
    path('quick-create/', views.client_quick_create, name='client_quick_create'),
    path('<int:pk>/update/', views.client_update, name='client_update'),
    path('<int:pk>/', views.client_detail, name='client_detail'),
    path('<int:pk>/delete/', views.client_delete, name='client_delete'),
]