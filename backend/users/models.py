from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    """以工号为登录标识的用户管理器（模型已不含 email 字段）。"""

    def _create_user(self, job_number, password, **extra_fields):
        if not job_number:
            raise ValueError('必须提供工号')
        user = self.model(job_number=job_number, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, job_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(job_number, password, **extra_fields)

    def create_superuser(self, job_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields['is_staff'] is not True:
            raise ValueError('超级管理员必须 is_staff=True')
        if extra_fields['is_superuser'] is not True:
            raise ValueError('超级管理员必须 is_superuser=True')
        return self._create_user(job_number, password, **extra_fields)


class User(AbstractUser):
    """员工账号。账号只能由管理员创建和维护，只能用工号+密码登录。"""
    username = None
    email = None
    first_name = None
    last_name = None
    USERNAME_FIELD = 'job_number'
    REQUIRED_FIELDS = ['position']

    objects = UserManager()

    name = models.CharField(max_length=50, blank=True, default='', verbose_name='姓名')
    job_number = models.CharField(max_length=20, unique=True, verbose_name='工号', help_text='登录凭证')
    position = models.CharField(max_length=50, verbose_name='岗位', help_text='如：值班站长、站务员')
    station = models.CharField(max_length=100, blank=True, default='', verbose_name='所属车站')
    zone = models.CharField(max_length=100, blank=True, default='', verbose_name='所属站区')
    extra = models.JSONField(default=dict, blank=True, verbose_name='扩展信息',
                             help_text='预留的扩展字段，如入职日期、证书等')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'users'

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __str__(self):
        return f"{self.job_number} - {self.name}" if self.name else self.job_number
