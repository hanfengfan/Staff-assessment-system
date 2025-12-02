from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """扩展的用户模型，基于Django的AbstractUser"""
    job_number = models.CharField(max_length=20, unique=True, verbose_name='工号', help_text='登录凭证')
    position = models.CharField(max_length=50, verbose_name='岗位', help_text='如：值班站长、站务员')
    department = models.CharField(max_length=100, verbose_name='所属车站/部门')

    # 继承的AbstractUser已包含以下字段，无需重复定义：
    # username, first_name, last_name, email, password, is_active, is_staff, etc.

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'users'

    def __str__(self):
        return f"{self.job_number} - {self.get_full_name() or self.username}"