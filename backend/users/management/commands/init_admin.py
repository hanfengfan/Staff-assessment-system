import os

from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = '创建管理员用户'

    def handle(self, *args, **options):
        if not User.objects.filter(job_number='ADMIN001').exists():
            password = os.environ.get('ADMIN_INIT_PASSWORD') or get_random_string(12)
            User.objects.create_superuser(
                job_number='ADMIN001',
                password=password,
                position='系统管理员',
                name='管理员',
            )
            self.stdout.write(self.style.SUCCESS('管理员用户创建成功'))
            self.stdout.write('  工号: ADMIN001')
            self.stdout.write(f'  密码: {password}')
        else:
            self.stdout.write(self.style.WARNING('管理员用户已存在'))