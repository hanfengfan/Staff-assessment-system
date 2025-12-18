from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from core.models import ExamPaper, Tag
from .models import CapabilityProfile, TrainingMaterial
from .serializers import (
    CapabilityProfileSerializer, RadarChartDataSerializer,
    TrendChartDataSerializer, TrainingMaterialSerializer,
    UserCapabilitySummarySerializer
)
from core.serializers import TagSerializer


class CapabilityProfileListView(generics.ListAPIView):
    """用户能力画像列表"""
    serializer_class = CapabilityProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只返回当前用户的能力画像
        return CapabilityProfile.objects.filter(user=self.request.user).select_related('tag')


class TrainingMaterialListView(generics.ListAPIView):
    """培训资料列表"""
    queryset = TrainingMaterial.objects.filter(is_active=True)
    serializer_class = TrainingMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 管理员可以看到所有资料，普通用户只能看到自己的
        if self.request.user.is_staff:
            return super().get_queryset()
        else:
            # 普通用户只能看到公开的资料或自己的资料
            return super().get_queryset().filter(
                Q(is_public=True) | Q(creator=self.request.user)
            )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def radar_chart_data(request):
    """获取用户能力雷达图数据"""
    # 检查是否为管理员查看其他用户
    target_user_id = request.GET.get('user_id')

    if target_user_id:
        # 管理员权限检查
        if not request.user.is_staff:
            return Response({
                'error': '无权限查看其他用户数据'
            }, status=status.HTTP_403_FORBIDDEN)

        # 管理员查看指定用户
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({
                'error': '用户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        # 普通用户查看自己的数据
        user = request.user

    # 获取用户的能力画像数据（排除role标签）
    profiles = CapabilityProfile.objects.filter(
        user=user
    ).select_related('tag').exclude(
        tag__category='role'  # 排除role标签
    )

    # 如果用户没有能力画像数据，为所有能力标签创建默认值
    if not profiles.exists():
        # 获取所有非role类型的活跃标签
        all_tags = Tag.objects.exclude(category='role')
        data = [
            {'tag': tag.name, 'score': 50.0}  # 默认中等水平
            for tag in all_tags
        ]
    else:
        data = [
            {'tag': profile.tag.name, 'score': profile.mastery_level}
            for profile in profiles
        ]

    serializer = RadarChartDataSerializer(data, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def capability_summary(request):
    """获取用户能力总结"""
    # 检查是否为管理员查看其他用户
    target_user_id = request.GET.get('user_id')

    if target_user_id:
        # 管理员权限检查
        if not request.user.is_staff:
            return Response({
                'error': '无权限查看其他用户数据'
            }, status=status.HTTP_403_FORBIDDEN)

        # 管理员查看指定用户
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({
                'error': '用户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        # 普通用户查看自己的数据
        user = request.user

    # 计算总体平均分（排除role标签）
    profiles = CapabilityProfile.objects.filter(
        user=user
    ).exclude(tag__category='role')  # 排除role标签

    if profiles.exists():
        overall_score = profiles.aggregate(avg_score=Avg('mastery_level'))['avg_score']
    else:
        overall_score = 50.0

    # 获取弱项和强项标签（排除role标签）
    weak_threshold = 60.0
    strong_threshold = 80.0

    weak_profiles = profiles.filter(mastery_level__lt=weak_threshold)
    strong_profiles = profiles.filter(mastery_level__gte=strong_threshold)

    weak_tags = [profile.tag.name for profile in weak_profiles]
    strong_tags = [profile.tag.name for profile in strong_profiles]

    # 统计考试次数和最近准确率
    total_exams = ExamPaper.objects.filter(user=user).count()

    recent_papers = ExamPaper.objects.filter(
        user=user,
        status=ExamPaper.Status.COMPLETED,
        completed_at__gte=timezone.now() - timedelta(days=30)
    )

    recent_accuracy = 0.0
    if recent_papers.exists():
        total_score = sum(paper.score_obtained or 0 for paper in recent_papers)
        max_score = sum(paper.total_score for paper in recent_papers)
        if max_score > 0:
            recent_accuracy = (total_score / max_score) * 100

    summary_data = {
        'user_id': user.id,
        'username': user.username,
        'job_number': user.job_number,
        'overall_score': round(overall_score, 2),
        'weak_tags': weak_tags,
        'strong_tags': strong_tags,
        'total_exams': total_exams,
        'recent_accuracy': round(recent_accuracy, 2)
    }

    serializer = UserCapabilitySummarySerializer(summary_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def trend_data(request):
    """获取能力变化趋势数据"""
    # 检查是否为管理员查看其他用户
    target_user_id = request.GET.get('user_id')
    days = int(request.GET.get('days', 30))  # 默认30天

    if target_user_id:
        # 管理员权限检查
        if not request.user.is_staff:
            return Response({
                'error': '无权限查看其他用户数据'
            }, status=status.HTTP_403_FORBIDDEN)

        # 管理员查看指定用户
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({
                'error': '用户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        # 普通用户查看自己的数据
        user = request.user

    # 获取指定天数内的已完成考试
    cutoff_date = timezone.now() - timedelta(days=days)
    completed_papers = ExamPaper.objects.filter(
        user=user,
        status=ExamPaper.Status.COMPLETED,
        completed_at__gte=cutoff_date
    ).prefetch_related('exam_records__question__tags')

    trend_data = []

    # 按日期分组统计数据
    date_scores = {}
    for paper in completed_papers:
        date_key = paper.completed_at.date()

        # 统计各标签在该次考试中的表现（排除role标签）
        tag_scores = {}
        for record in paper.exam_records.all():
            for tag in record.question.tags.all():
                # 排除role标签
                if tag.category == 'role':
                    continue

                if tag not in tag_scores:
                    tag_scores[tag] = {'correct': 0, 'total': 0}

                tag_scores[tag]['total'] += 1
                if record.is_correct:
                    tag_scores[tag]['correct'] += 1

        # 计算各标签的准确率
        for tag, score_data in tag_scores.items():
            accuracy = (score_data['correct'] / score_data['total']) * 100

            if date_key not in date_scores:
                date_scores[date_key] = {}

            date_scores[date_key][tag.name] = accuracy

    # 转换为趋势数据格式
    for date, tag_scores in date_scores.items():
        for tag_name, score in tag_scores.items():
            trend_data.append({
                'date': date,
                'tag_name': tag_name,
                'score': round(score, 2)
            })

    serializer = TrendChartDataSerializer(trend_data, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def create_training_material(request):
    """创建培训资料（管理员专用）"""
    # 设置创建者为当前用户
    serializer = TrainingMaterialSerializer(data=request.data)
    if serializer.is_valid():
        material = serializer.save(creator=request.user)
        return Response({
            'message': '培训资料创建成功',
            'material_id': material.id
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def weak_tag_recommendations(request):
    """获取弱项标签的学习建议"""
    user = request.user

    # 获取用户的弱项标签（排除role标签）
    weak_threshold = 60.0
    weak_profiles = CapabilityProfile.objects.filter(
        user=user,
        mastery_level__lt=weak_threshold
    ).exclude(
        tag__category='role'  # 排除role标签
    ).select_related('tag').order_by('mastery_level')

    recommendations = []

    for profile in weak_profiles:
        # 查找相关的培训资料
        materials = TrainingMaterial.objects.filter(
            tags=profile.tag,
            is_active=True
        ).count()

        recommendations.append({
            'tag_name': profile.tag.name,
            'tag_category': profile.tag.category,
            'current_level': profile.mastery_level,
            'available_materials': materials,
            'priority': '高' if profile.mastery_level < 40 else '中'
        })

    # 按掌握度从低到高排序
    recommendations.sort(key=lambda x: x['current_level'])

    return Response({
        'weak_tags': recommendations,
        'total_count': len(recommendations)
    })


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def user_list(request):
    """获取用户列表（管理员专用）"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 排除超级管理员，只返回普通用户
    users = User.objects.filter(is_staff=False).order_by('job_number')

    user_data = [
        {
            'id': user.id,
            'username': user.username,
            'job_number': user.job_number,
            'is_active': user.is_active,
            'date_joined': user.date_joined,
            'last_login': user.last_login
        }
        for user in users
    ]

    return Response(user_data)