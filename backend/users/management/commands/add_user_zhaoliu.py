from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

User = get_user_model()


class Command(BaseCommand):
    help = '添加普通用户：zhaoliu（ST004，行车值班员，XX站）'

    def handle(self, *args, **options):
        job_number = 'ST004'
        position = '行车值班员'
        station = 'XX站'
        password = get_random_string(12)

        if User.objects.filter(job_number=job_number).exists():
            self.stdout.write(self.style.WARNING(f'工号 {job_number} 已存在'))
            return

        try:
            user = User.objects.create_user(
                job_number=job_number,
                password=password,
                position=position,
                station=station,
                name='赵六',
            )

            self.stdout.write(self.style.SUCCESS('用户创建成功'))
            self.stdout.write(f'  工号: {job_number}')
            self.stdout.write(f'  密码: {password}')
            self.stdout.write(f'  职位: {position}')
            self.stdout.write(f'  车站: {station}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'创建用户失败: {str(e)}'))