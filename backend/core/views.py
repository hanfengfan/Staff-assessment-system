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
from .services import ExamGenerationService


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
    """生成智能试卷"""
    try:
        # 获取前端参数
        reason = request.data.get('reason', 'daily_practice')
        question_count = request.data.get('question_count', None)

        # 调用服务生成试卷
        service = ExamGenerationService()
        exam_paper = service.generate_exam(
            user_id=request.user.id,
            reason=reason,
            question_count=question_count
        )

        return Response({
            'id': exam_paper.id,
            'title': exam_paper.title,
            'time_limit': exam_paper.time_limit,
            'question_count': exam_paper.exam_records.count(),
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

        # 检查试卷状态
        if exam_paper.status != ExamPaper.Status.NOT_STARTED:
            return Response({
                'error': '试卷已经开始或已提交'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 更新试卷状态和开始时间
        exam_paper.status = ExamPaper.Status.IN_PROGRESS
        exam_paper.started_at = timezone.now()
        exam_paper.save()

        # 获取试卷题目信息（不含答案）
        exam_records = exam_paper.exam_records.select_related('question').prefetch_related('question__tags')
        questions_data = []

        print(f"实际获取的答题记录数量: {exam_records.count()}")

        for record in exam_records:
            question = record.question
            print(f"处理题目: {question.id}, 类型: {question.question_type}")
            questions_data.append({
                'id': question.id,  # 使用id而不是question_id以保持一致性
                'content': question.content,
                'question_type': question.question_type,
                'options': question.options,
                'difficulty': question.difficulty,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in question.tags.all()]
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
        exam_paper = ExamPaper.objects.get(id=paper_id, user=request.user)

        # 检查试卷状态
        if exam_paper.status != ExamPaper.Status.IN_PROGRESS:
            return Response({
                'error': '试卷未开始或已提交'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 获取提交的答案
        answers = request.data.get('answers', {})
        if not answers:
            return Response({
                'error': '未提供答案'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 计算分数
        exam_records = exam_paper.exam_records.all()
        question_count = exam_records.count()

        # 每题平均分
        score_per_question = exam_paper.total_score / question_count if question_count > 0 else 0

        correct_count = 0
        for record in exam_records:
            question = record.question
            answer = answers.get(str(question.id))

            # 设置答案
            record.user_answer = answer

            # 判断答案是否正确
            is_correct = str(answer) == str(question.correct_answer)
            record.is_correct = is_correct

            # 更新该题得分
            record.score_gained = score_per_question if is_correct else 0

            if is_correct:
                correct_count += 1

            record.save()

        # 计算总分
        obtained_score = correct_count * score_per_question

        # 更新试卷状态和分数
        exam_paper.status = ExamPaper.Status.COMPLETED
        exam_paper.completed_at = timezone.now()
        exam_paper.score_obtained = obtained_score
        exam_paper.save()

        # 计算准确率
        accuracy = (correct_count / question_count * 100) if question_count > 0 else 0

        return Response({
            'id': exam_paper.id,
            'status': exam_paper.get_status_display(),
            'total_score': exam_paper.total_score,
            'score_obtained': obtained_score,
            'accuracy': round(accuracy, 2),
            'completed_at': exam_paper.completed_at
        }, status=status.HTTP_200_OK)

    except ExamPaper.DoesNotExist:
        return Response({
            'error': '试卷不存在'
        }, status=status.HTTP_404_NOT_FOUND)


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