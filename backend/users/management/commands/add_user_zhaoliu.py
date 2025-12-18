from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = '添加普通用户：zhaoliu（ST004，行车值班员，XX站）'

    def handle(self, *args, **options):
        username = 'zhaoliu'
        job_number = 'ST004'
        position = '行车值班员'
        department = 'XX站'
        password = 'password123'  # 默认密码，可以后续修改

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'用户 {username} 已存在'))
            return

        if User.objects.filter(job_number=job_number).exists():
            self.stdout.write(self.style.WARNING(f'工号 {job_number} 已存在'))
            return

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                job_number=job_number,
                position=position,
                department=department,
                first_name='赵',
                last_name='六',
                email='zhaoliu@railway.com'
            )

            self.stdout.write(self.style.SUCCESS('用户创建成功'))
            self.stdout.write(f'  用户名: {username}')
            self.stdout.write(f'  密码: {password}')
            self.stdout.write(f'  工号: {job_number}')
            self.stdout.write(f'  职位: {position}')
            self.stdout.write(f'  部门: {department}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'创建用户失败: {str(e)}'))