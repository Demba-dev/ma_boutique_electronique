from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('create-user/', views.create_user, name='create_user'),
    path('settings/', views.settings_list, name='settings_list'),
]