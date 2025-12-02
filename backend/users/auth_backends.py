from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class JobNumberBackend(ModelBackend):
    """
    自定义认证后端，支持使用工号或用户名登录
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 尝试使用工号或用户名查找用户
            user = User.objects.get(
                Q(job_number=username) | Q(username=username)
            )
            if user.check_password(password) and user.is_active:
                return user
        except User.DoesNotExist:
            return None
        return None