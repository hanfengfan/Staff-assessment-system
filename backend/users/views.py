from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .dimensions import apply_dimension_filters, dimension_options
from .models import User
from .serializers import LoginSerializer, StaffSerializer, UserSerializer


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


class StaffPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200


class StaffViewSet(viewsets.ModelViewSet):
    """员工增删查改，仅管理员可用。管理员账号（is_staff）不在此处管理。

    列表支持 ?search=姓名/工号 与 ?position= ?station= ?zone= ?is_active= 筛选。
    """
    serializer_class = StaffSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StaffPagination

    def get_queryset(self):
        qs = User.objects.filter(is_staff=False).order_by('job_number')
        params = self.request.query_params
        search = params.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(job_number__icontains=search))
        qs = apply_dimension_filters(qs, params)
        is_active = params.get('is_active')
        if is_active in ('true', 'false'):
            qs = qs.filter(is_active=(is_active == 'true'))
        return qs

    def perform_update(self, serializer):
        user = serializer.save()
        # 停用或改密后，旧登录态立即失效
        if not user.is_active or 'password' in serializer.validated_data:
            Token.objects.filter(user=user).delete()


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def staff_dimensions(request):
    """岗位/车站/站区各维度的可选值及人数，供筛选与后续统计分析使用。"""
    return Response(dimension_options())
