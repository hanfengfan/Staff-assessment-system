from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView
from .models import User
from .serializers import LoginSerializer, UserSerializer, UserCreateSerializer


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """用户登录接口"""
    serializer = LoginSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """用户登出接口"""
    try:
        # 删除用户的token
        request.user.auth_token.delete()
        return Response({'message': '登出成功'}, status=status.HTTP_200_OK)
    except:
        return Response({'message': '登出失败'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_view(request):
    """获取用户信息接口"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class UserCreateView(CreateAPIView):
    """用户注册接口"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]