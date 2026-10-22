from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""

    class Meta:
        model = User
        fields = ('id', 'job_number', 'name', 'position', 'station', 'zone',
                 'is_staff', 'date_joined', 'last_login')
        read_only_fields = fields


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
            # 登录字段(USERNAME_FIELD)就是工号
            user = authenticate(username=job_number, password=password)

            if not user:
                raise serializers.ValidationError('工号或密码错误')

            if not user.is_active:
                raise serializers.ValidationError('用户账号已被禁用')

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('工号和密码都是必填项')


class StaffSerializer(serializers.ModelSerializer):
    """管理员维护员工信息用。登录用户名固定等于工号。"""
    password = serializers.CharField(write_only=True, required=False, allow_blank=False,
                                     min_length=6, max_length=128, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'name', 'job_number', 'position', 'station', 'zone',
                  'extra', 'is_active', 'password', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')

    def validate_extra(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('扩展信息必须是键值对象')
        return value

    def validate(self, attrs):
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': '新增员工必须设置初始密码'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(
            password=password, **validated_data
        )

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
