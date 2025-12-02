from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/profile/', views.user_profile_view, name='profile'),
    path('auth/register/', views.UserCreateView.as_view(), name='register'),
]