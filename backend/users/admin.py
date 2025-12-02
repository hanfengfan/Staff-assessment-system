from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('job_number', 'username', 'position', 'department', 'is_active', 'date_joined')
    list_filter = ('position', 'department', 'is_active', 'date_joined')
    search_fields = ('job_number', 'username', 'department')

    fieldsets = UserAdmin.fieldsets + (
        ('员工信息', {
            'fields': ('job_number', 'position', 'department'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('员工信息', {
            'fields': ('job_number', 'position', 'department'),
        }),
    )