from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""

    class Meta:
        model = User
        fields = ('id', 'job_number', 'username', 'first_name', 'last_name',
                 'position', 'department', 'email', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    job_number = serializers.CharField(max_length=20, write_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)
    user = UserSerializer(read_only=True)

    def validate(self, attrs):
        job_number = attrs.get('job_number')
        password = attrs.get('password')

        if job_number and password:
            # 使用 job_number 作为 username 进行认证
            user = authenticate(username=job_number, password=password)

            if not user:
                raise serializers.ValidationError('工号或密码错误')

            if not user.is_active:
                raise serializers.ValidationError('用户账号已被禁用')

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('工号和密码都是必填项')


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""
    password = serializers.CharField(max_length=128, write_only=True)
    password_confirm = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ('job_number', 'username', 'password', 'password_confirm',
                 'first_name', 'last_name', 'position', 'department', 'email')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("两次输入的密码不一致")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user