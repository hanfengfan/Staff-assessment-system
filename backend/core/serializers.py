from rest_framework import serializers
from .models import Tag, Question, ExamPaper, ExamRecord


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'category', 'description', 'questions_count', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_questions_count(self, obj):
        return obj.questions.filter(is_active=True).count()


class QuestionSerializer(serializers.ModelSerializer):
    """题目序列化器（不包含正确答案）"""
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'content', 'question_type', 'options', 'tags',
                 'difficulty', 'created_at')
        read_only_fields = ('id', 'created_at')


class QuestionDetailSerializer(QuestionSerializer):
    """题目详细序列化器（包含正确答案）"""
    correct_answer = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True)

    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + ('correct_answer', 'explanation')


class QuestionWithAnswerSerializer(QuestionSerializer):
    """带正确答案的题目序列化器（用于错题解析）"""
    correct_answer = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True)

    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + ('correct_answer', 'explanation')


class ExamRecordSerializer(serializers.ModelSerializer):
    """答题记录序列化器"""
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = ExamRecord
        fields = ('id', 'question', 'user_answer', 'is_correct',
                 'score_gained', 'duration', 'created_at')
        read_only_fields = ('id', 'is_correct', 'score_gained', 'created_at')


class ExamRecordWithAnswerSerializer(serializers.ModelSerializer):
    """带正确答案的答题记录序列化器（用于错题解析）"""
    question = QuestionWithAnswerSerializer(read_only=True)

    class Meta:
        model = ExamRecord
        fields = ('id', 'question', 'user_answer', 'is_correct',
                 'score_gained', 'duration', 'created_at')
        read_only_fields = ('id', 'is_correct', 'score_gained', 'created_at')


class ExamPaperListSerializer(serializers.ModelSerializer):
    """试卷列表序列化器"""
    user_name = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    # 添加分离的用户字段
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    job_number = serializers.CharField(source='user.job_number', read_only=True)

    class Meta:
        model = ExamPaper
        fields = ('id', 'user_name', 'user_id', 'username', 'job_number',
                 'title', 'status', 'total_score', 'score_obtained',
                 'generation_reason', 'question_count', 'created_at')
        read_only_fields = ('id', 'created_at', 'user_id', 'username', 'job_number')

    def get_user_name(self, obj):
        return f"{obj.user.job_number} - {obj.user.get_full_name() or obj.user.username}"

    def get_question_count(self, obj):
        return obj.exam_records.count()


class ExamPaperDetailSerializer(serializers.ModelSerializer):
    """试卷详细序列化器"""
    exam_records = ExamRecordSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()  # 添加questions字段

    class Meta:
        model = ExamPaper
        fields = ('id', 'user_name', 'title', 'status', 'total_score',
                 'score_obtained', 'generation_reason', 'time_limit',
                 'started_at', 'completed_at', 'exam_records', 'questions', 'created_at')
        read_only_fields = ('id', 'created_at', 'started_at', 'completed_at')

    def get_questions(self, obj):
        """获取试卷题目数据"""
        questions_data = []
        for record in obj.exam_records.select_related('question').prefetch_related('question__tags').all():
            question = record.question
            questions_data.append({
                'id': question.id,
                'content': question.content,
                'question_type': question.question_type,
                'options': question.options,
                'difficulty': question.difficulty,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in question.tags.all()]
            })
        return questions_data

    def get_user_name(self, obj):
        return f"{obj.user.job_number} - {obj.user.get_full_name() or obj.user.username}"


class ExamGenerationSerializer(serializers.Serializer):
    """生成试卷请求序列化器"""
    reason = serializers.ChoiceField(
        choices=ExamPaper.GenerationReason.choices,
        default=ExamPaper.GenerationReason.DAILY_PRACTICE
    )
    question_count = serializers.IntegerField(
        min_value=5,
        max_value=50,
        default=15,
        help_text="题目数量，建议10-20题"
    )


class ExamPaperResultSerializer(serializers.ModelSerializer):
    """考试结果序列化器（包含正确答案，用于错题解析）"""
    exam_records = ExamRecordWithAnswerSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()  # 添加考试用时字段
    question_count = serializers.SerializerMethodField()  # 添加题目数量字段

    class Meta:
        model = ExamPaper
        fields = ('id', 'user_name', 'title', 'status', 'total_score',
                 'score_obtained', 'generation_reason', 'time_limit', 'duration',
                 'started_at', 'completed_at', 'exam_records', 'question_count', 'created_at')
        read_only_fields = ('id', 'created_at', 'started_at', 'completed_at')

    def get_user_name(self, obj):
        return f"{obj.user.job_number} - {obj.user.get_full_name() or obj.user.username}"

    def get_duration(self, obj):
        """计算考试用时（秒）"""
        if obj.started_at and obj.completed_at:
            return int((obj.completed_at - obj.started_at).total_seconds())
        return 0

    def get_question_count(self, obj):
        """获取题目数量"""
        return obj.exam_records.count()


class ExamSubmissionSerializer(serializers.Serializer):
    """试卷提交序列化器"""
    answers = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        help_text="用户答案字典，格式：{question_id: user_answer}"
    )