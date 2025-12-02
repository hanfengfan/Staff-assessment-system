from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from core.serializers import TagSerializer

from .models import Question, ExamPaper, ExamRecord
from .serializers import (
    QuestionSerializer, QuestionDetailSerializer,
    ExamPaperListSerializer, ExamPaperDetailSerializer,
    ExamGenerationSerializer, ExamSubmissionSerializer
)
from .services import ExamGenerationService, ExamScoringService


class QuestionListView(generics.ListAPIView):
    """题目列表视图"""
    queryset = Question.objects.filter(is_active=True)
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['content']
    ordering_fields = ['created_at', 'difficulty']
    ordering = ['-created_at']


class QuestionDetailView(generics.RetrieveAPIView):
    """题目详情视图（管理员专用，包含答案）"""
    queryset = Question.objects.all()
    serializer_class = QuestionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]


class ExamPaperListView(generics.ListAPIView):
    """试卷列表视图"""
    serializer_class = ExamPaperListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['user__job_number', 'user__username', 'title']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']

    def get_queryset(self):
        # 普通用户只能看到自己的试卷，管理员可以看到所有试卷
        user = self.request.user
        if user.is_staff:
            return ExamPaper.objects.all()
        else:
            return ExamPaper.objects.filter(user=user)


class ExamPaperDetailView(generics.RetrieveAPIView):
    """试卷详情视图"""
    serializer_class = ExamPaperDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ExamPaper.objects.all()
        else:
            return ExamPaper.objects.filter(user=user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_exam(request):
    """生成智能试卷"""
    serializer = ExamGenerationSerializer(data=request.data)

    if serializer.is_valid():
        reason = serializer.validated_data['reason']
        question_count = serializer.validated_data['question_count']

        try:
            service = ExamGenerationService()
            exam_paper = service.generate_exam(
                user_id=request.user.id,
                reason=reason,
                question_count=question_count
            )

            # 获取题目数据
            questions_data = []
            for record in exam_paper.exam_records.all():
                questions_data.append({
                    'id': record.question.id,
                    'content': record.question.content,
                    'question_type': record.question.question_type,
                    'options': record.question.options,
                    'difficulty': record.question.difficulty,
                    'tags': [{'id': tag.id, 'name': tag.name} for tag in record.question.tags.all()]
                })

            return Response({
                'paper_id': exam_paper.id,
                'title': exam_paper.title,
                'question_count': exam_paper.exam_records.count(),
                'time_limit': exam_paper.time_limit,
                'questions': questions_data,
                'message': '试卷生成成功'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': f'试卷生成失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_exam(request, paper_id):
    """提交试卷"""
    try:
        exam_paper = ExamPaper.objects.get(id=paper_id)

        # 权限检查：用户只能提交自己的试卷
        if not request.user.is_staff and exam_paper.user != request.user:
            return Response({
                'error': '无权限提交此试卷'
            }, status=status.HTTP_403_FORBIDDEN)

        # 检查试卷状态
        if exam_paper.status != ExamPaper.Status.NOT_STARTED and exam_paper.status != ExamPaper.Status.IN_PROGRESS:
            return Response({
                'error': '试卷已经提交或无法提交'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ExamSubmissionSerializer(data=request.data)

        if serializer.is_valid():
            answers = serializer.validated_data['answers']

            try:
                service = ExamScoringService()
                result = service.submit_exam(paper_id, answers)

                return Response({
                    'message': '试卷提交成功',
                    'result': result
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({
                    'error': f'试卷评分失败: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)

    except ExamPaper.DoesNotExist:
        return Response({
            'error': '试卷不存在'
        }, status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_exam(request, paper_id):
    """开始考试"""
    try:
        exam_paper = ExamPaper.objects.get(id=paper_id)

        # 权限检查
        if not request.user.is_staff and exam_paper.user != request.user:
            return Response({
                'error': '无权限开始此试卷'
            }, status=status.HTTP_403_FORBIDDEN)

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

        for record in exam_records:
            question = record.question
            questions_data.append({
                'record_id': record.id,
                'question_id': question.id,
                'content': question.content,
                'question_type': question.question_type,
                'options': question.options,
                'difficulty': question.difficulty,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in question.tags.all()]
            })

        return Response({
            'message': '考试开始',
            'paper_info': {
                'paper_id': exam_paper.id,
                'title': exam_paper.title,
                'time_limit': exam_paper.time_limit,
                'started_at': exam_paper.started_at,
                'question_count': len(questions_data)
            },
            'questions': questions_data
        }, status=status.HTTP_200_OK)

    except ExamPaper.DoesNotExist:
        return Response({
            'error': '试卷不存在'
        }, status=status.HTTP_404_NOT_FOUND)