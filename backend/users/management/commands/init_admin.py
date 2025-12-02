from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = '创建管理员用户'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@railway.com',
                password='admin123',
                job_number='ADMIN001',
                position='系统管理员',
                department='技术部',
                first_name='管理',
                last_name='员'
            )
            self.stdout.write(self.style.SUCCESS('管理员用户创建成功'))
            self.stdout.write('  用户名: admin')
            self.stdout.write('  密码: admin123')
            self.stdout.write('  工号: ADMIN001')
        else:
            self.stdout.write(self.style.WARNING('管理员用户已存在'))