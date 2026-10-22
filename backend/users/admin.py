from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import BaseUserCreationForm

from .models import User


class StaffCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ('job_number', 'name', 'position', 'station', 'zone')


@admin.register(User)
class StaffAdmin(UserAdmin):
    add_form = StaffCreationForm
    ordering = ('job_number',)
    list_display = ('job_number', 'name', 'position', 'station', 'zone', 'is_active', 'date_joined')
    list_filter = ('position', 'station', 'zone', 'is_active', 'date_joined')
    search_fields = ('job_number', 'name', 'station', 'zone')

    fieldsets = (
        (None, {'fields': ('password',)}),
        ('员工信息', {'fields': ('job_number', 'name', 'position', 'station', 'zone', 'extra')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('job_number', 'password1', 'password2'),
        }),
        ('员工信息', {'fields': ('name', 'position', 'station', 'zone')}),
    )
