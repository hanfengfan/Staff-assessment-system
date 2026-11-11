from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import Question, Tag, ExamPaper, ExamRecord, ExamConfig
from .serializers import (
    QuestionSerializer, QuestionDetailSerializer,
    ExamPaperListSerializer, ExamPaperDetailSerializer, ExamPaperResultSerializer,
    TagSerializer
)
from .services import ExamGenerationService, ExamScoringService
from .option_shuffle import shuffled_options
from .tag_filter import visible_tags
from .exam_builder import ComposeError


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

    except ComposeError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
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

        # 试卷所有者：线路、岗位级别、职位类标签只保留与其本人相同的
        exam_user = exam_paper.user

        for record in exam_records:
            question = record.question
            print(f"处理题目: {question.id}, 类型: {question.question_type}")

            filtered_tags = visible_tags(question.tags.all(), exam_user)

            questions_data.append({
                'id': question.id,  # 使用id而不是question_id以保持一致性
                'content': question.content,
                'question_type': question.question_type,
                'options': shuffled_options(question, record.option_order),
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


def _config_payload(config):
    if config is None:
        return {'configured': False, 'bank_subjects': [], 'category_weights': {},
                'total_count': 10, 'type_counts': {}, 'difficulty_ratio': {}}
    return {
        'configured': True,
        'bank_subjects': config.bank_subjects,
        'category_weights': config.category_weights,
        'total_count': config.total_count,
        'type_counts': config.type_counts,
        'difficulty_ratio': config.difficulty_ratio,
        'updated_at': config.updated_at,
    }


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def exam_config_options(request):
    """组卷规则的可选项：各题库专业下的一级目录，以及各题型、难度的题量（仅启用的题）。"""
    rows = (Question.objects.filter(is_active=True).exclude(bank_subject='')
            .values('bank_subject', 'category_l1', 'question_type', 'difficulty')
            .annotate(n=Count('id')))
    subjects = {}
    for r in rows:
        s = subjects.setdefault(r['bank_subject'], {
            'name': r['bank_subject'], 'total': 0, 'categories': {}, 'types': {}, 'levels': {}})
        s['total'] += r['n']
        s['categories'][r['category_l1']] = s['categories'].get(r['category_l1'], 0) + r['n']
        s['types'][r['question_type']] = s['types'].get(r['question_type'], 0) + r['n']
        s['levels'][r['difficulty']] = s['levels'].get(r['difficulty'], 0) + r['n']
    for s in subjects.values():
        s['categories'] = [{'name': k, 'count': v} for k, v in sorted(s['categories'].items())]
    return Response(sorted(subjects.values(), key=lambda s: s['name']))


def _validate_config(data):
    """校验管理员提交的规则，返回 (清洗后的数据, 错误信息)。"""
    known = set(Question.objects.filter(is_active=True).exclude(bank_subject='')
                .values_list('bank_subject', flat=True))
    subjects = data.get('bank_subjects') or []
    if not isinstance(subjects, list) or not subjects:
        return None, '请至少选择一个题库专业'
    if any(s not in known for s in subjects):
        return None, '所选题库专业不存在或没有启用的题目'

    type_counts = {}
    for t in ('single', 'multiple', 'true_false', 'subjective'):
        try:
            n = int((data.get('type_counts') or {}).get(t, 0) or 0)
        except (TypeError, ValueError):
            return None, '题型数量必须是整数'
        if n < 0:
            return None, '题型数量不能为负数'
        if n:
            type_counts[t] = n
    total = sum(type_counts.values())
    if total == 0:
        return None, '请至少为一种题型设置数量'
    if int(data.get('total_count') or 0) != total:
        return None, f'总题数必须等于各题型数量之和（当前各题型合计 {total} 题）'

    ratio = {}
    for lv in ('易', '中', '难'):
        try:
            v = float((data.get('difficulty_ratio') or {}).get(lv, 0) or 0)
        except (TypeError, ValueError):
            return None, '难度比例必须是数字'
        if v < 0:
            return None, '难度比例不能为负数'
        ratio[lv] = v
    if sum(ratio.values()) <= 0:
        return None, '难度比例至少有一项大于 0'

    cats = set(Question.objects.filter(is_active=True, bank_subject__in=subjects)
               .values_list('category_l1', flat=True))
    weights = {}
    for name, w in (data.get('category_weights') or {}).items():
        try:
            w = float(w or 0)
        except (TypeError, ValueError):
            return None, f'目录“{name}”的权重必须是数字'
        if w < 0:
            return None, f'目录“{name}”的权重不能为负数'
        if w > 0:
            if name not in cats:
                return None, f'一级目录“{name}”不在所选题库专业中'
            weights[name] = w
    return {'bank_subjects': subjects, 'category_weights': weights, 'total_count': total,
            'type_counts': type_counts, 'difficulty_ratio': ratio}, None


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAdminUser])
def exam_config(request):
    """读取 / 保存全局组卷规则（仅管理员）。"""
    if request.method == 'GET':
        return Response(_config_payload(ExamConfig.load()))
    cleaned, error = _validate_config(request.data)
    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    config, _ = ExamConfig.objects.update_or_create(
        pk=1, defaults={**cleaned, 'updated_by': request.user})
    return Response(_config_payload(config))