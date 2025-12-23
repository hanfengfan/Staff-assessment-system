from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import Question, Tag, ExamPaper, ExamRecord
from .serializers import (
    QuestionSerializer, QuestionDetailSerializer,
    ExamPaperListSerializer, ExamPaperDetailSerializer, ExamPaperResultSerializer,
    TagSerializer
)
from .services import ExamGenerationService, ExamScoringService


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页器"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class QuestionListView(generics.ListCreateAPIView):
    """题目列表视图"""
    queryset = Question.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return QuestionSerializer
        return QuestionDetailSerializer


class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """题目详情视图"""
    queryset = Question.objects.all()
    serializer_class = QuestionDetailSerializer


class ExamPaperPagination(PageNumberPagination):
    """试卷分页器"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ExamPaperListView(generics.ListCreateAPIView):
    """试卷列表视图"""
    serializer_class = ExamPaperListSerializer
    pagination_class = ExamPaperPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """根据用户权限返回不同的试卷列表"""
        if self.request.user.is_staff:
            # 管理员可以看到所有试卷，支持按用户筛选
            queryset = ExamPaper.objects.all()
            user_id = self.request.GET.get('user_id')
            if user_id:
                queryset = queryset.filter(user_id=user_id)
        else:
            # 普通用户只能看到自己的试卷
            queryset = ExamPaper.objects.filter(user=self.request.user)

        # 支持状态筛选
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.select_related('user').prefetch_related('exam_records__question')


class ExamPaperDetailView(generics.RetrieveUpdateDestroyAPIView):
    """试卷详情视图"""
    serializer_class = ExamPaperDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """根据用户权限返回不同试卷"""
        if self.request.user.is_staff:
            # 管理员可以看到所有试卷
            return ExamPaper.objects.all()
        else:
            # 普通用户只能看到自己的试卷
            return ExamPaper.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """根据试卷状态选择不同的序列化器"""
        instance = self.get_object()
        # 如果是已完成状态，使用带答案的序列化器
        if instance.status == ExamPaper.Status.COMPLETED:
            return ExamPaperResultSerializer
        # 其他状态使用默认序列化器（不包含答案）
        return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        """重写retrieve方法以返回题目数据"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_exam(request):
    """生成智能试卷（题目数量由后端配置控制）"""
    try:
        # 获取前端参数
        reason = request.data.get('reason', 'daily_practice')

        # 调用服务生成试卷，题目数量使用后端配置
        service = ExamGenerationService()
        exam_paper = service.generate_exam(
            user_id=request.user.id,
            reason=reason
            # 不再接受 question_count 参数，完全使用后端配置
        )

        actual_question_count = exam_paper.exam_records.count()

        return Response({
            'id': exam_paper.id,
            'title': exam_paper.title,
            'time_limit': exam_paper.time_limit,
            'question_count': actual_question_count,
            'total_score': exam_paper.total_score,
            'status': exam_paper.get_status_display()
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'生成试卷失败: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_exam(request, paper_id):
    """开始考试"""
    try:
        exam_paper = ExamPaper.objects.get(id=paper_id, user=request.user)

        # 如果试卷是“已完成”状态，依然报错
        if exam_paper.status == ExamPaper.Status.COMPLETED:
            return Response({
                'error': '试卷已提交，无法再次开始'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # 如果是“未开始”，则更新状态；如果是“进行中”，则直接放行（视为重入）
        if exam_paper.status == ExamPaper.Status.NOT_STARTED:
            exam_paper.status = ExamPaper.Status.IN_PROGRESS
            exam_paper.started_at = timezone.now()
            exam_paper.save()

        # 获取试卷题目信息（不含答案）
        exam_records = exam_paper.exam_records.select_related('question').prefetch_related('question__tags')
        questions_data = []

        print(f"实际获取的答题记录数量: {exam_records.count()}")

        # 获取试卷用户的职位信息，用于过滤role标签
        user_position = exam_paper.user.position
        is_admin = user_position == '系统管理员'

        for record in exam_records:
            question = record.question
            print(f"处理题目: {question.id}, 类型: {question.question_type}")

            # 过滤标签：对于非管理员，只显示相关的role标签
            filtered_tags = []
            for tag in question.tags.all():
                if tag.category != 'role':
                    # 非role标签直接显示
                    filtered_tags.append({'id': tag.id, 'name': tag.name})
                elif is_admin:
                    # 管理员可以看到所有role标签
                    filtered_tags.append({'id': tag.id, 'name': tag.name})
                else:
                    # 非管理员用户，只显示与自己职位相关的role标签
                    if tag.name == user_position:
                        filtered_tags.append({'id': tag.id, 'name': tag.name})

            questions_data.append({
                'id': question.id,  # 使用id而不是question_id以保持一致性
                'content': question.content,
                'question_type': question.question_type,
                'options': question.options,
                'difficulty': question.difficulty,
                'tags': filtered_tags
            })

        print(f"准备返回的题目数量: {len(questions_data)}")

        return Response({
            'id': exam_paper.id,
            'title': exam_paper.title,
            'status': exam_paper.get_status_display(),
            'time_limit': exam_paper.time_limit,
            'started_at': exam_paper.started_at,
            'question_count': len(questions_data),
            'questions': questions_data
        }, status=status.HTTP_200_OK)

    except ExamPaper.DoesNotExist:
        return Response({
            'error': '试卷不存在'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_exam(request, paper_id):
    """提交考试"""
    try:
        # 检查试卷是否存在且属于当前用户
        exam_paper = ExamPaper.objects.get(id=paper_id, user=request.user)

        # 获取提交的答案
        answers = request.data.get('answers', {})
        if not answers:
            return Response({
                'error': '未提供答案'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 使用ExamScoringService进行评分
        scoring_service = ExamScoringService()

        # 调用服务层的submit_exam方法
        result = scoring_service.submit_exam(paper_id, answers)

        # 获取更新后的试卷信息
        updated_paper = ExamPaper.objects.get(id=paper_id)

        # 组合返回数据，保持与前端期望的格式一致
        response_data = {
            'id': updated_paper.id,
            'status': updated_paper.get_status_display(),
            'total_score': updated_paper.total_score,
            'score_obtained': result.get('total_score', 0),
            'accuracy': round(result.get('accuracy', 0), 2),
            'completed_at': updated_paper.completed_at,
            'tag_performance': result.get('tag_performance', [])
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except ExamPaper.DoesNotExist:
        return Response({
            'error': '试卷不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # 捕获其他可能的异常
        return Response({
            'error': f'提交试卷时发生错误: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAdminUser])
def delete_exam(request, paper_id):
    """删除试卷（管理员专用）"""
    try:
        exam_paper = ExamPaper.objects.get(id=paper_id)
        exam_paper.delete()
        return Response({
            'message': '试卷删除成功'
        }, status=status.HTTP_200_OK)

    except ExamPaper.DoesNotExist:
        return Response({
            'error': '试卷不存在'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def exam_stats(request):
    """获取考试统计数据（管理员专用）"""
    User = get_user_model()

    # 基础统计数据
    total_users = User.objects.filter(is_staff=False).count()
    active_users = User.objects.filter(
        is_staff=False,
        last_login__gte=timezone.now() - timedelta(days=30)
    ).count()

    total_exams = ExamPaper.objects.all().count()
    completed_exams = ExamPaper.objects.filter(status=ExamPaper.Status.COMPLETED).count()

    # 平均分数统计
    avg_score = 0
    if completed_exams > 0:
        scores = ExamPaper.objects.filter(
            status=ExamPaper.Status.COMPLETED,
            score_obtained__isnull=False
        ).aggregate(avg_score=Avg('score_obtained'))
        avg_score = round(scores['avg_score'] or 0, 2)

    # 最近7天的考试统计
    recent_date = timezone.now() - timedelta(days=7)
    recent_exams = ExamPaper.objects.filter(created_at__gte=recent_date).count()

    stats_data = {
        'total_users': total_users,
        'active_users': active_users,
        'total_exams': total_exams,
        'completed_exams': completed_exams,
        'avg_score': avg_score,
        'recent_exams': recent_exams
    }

    return Response(stats_data, status=status.HTTP_200_OK)