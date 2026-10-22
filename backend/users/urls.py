from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'users'

router = DefaultRouter()
router.register('staff', views.StaffViewSet, basename='staff')

urlpatterns = [
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/profile/', views.user_profile_view, name='profile'),
    path('staff/dimensions/', views.staff_dimensions, name='staff-dimensions'),
    path('', include(router.urls)),
]
