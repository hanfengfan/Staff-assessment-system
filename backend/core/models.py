from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseTimestampedModel(models.Model):
    """带时间戳的基础抽象模型"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True


class Tag(BaseTimestampedModel):
    """标签模型，用于题目的多维度标注"""
    class Category(models.TextChoices):
        # 职位类：决定哪些人能抽到这道题
        ROLE = 'role', '职位类'
        # 能力类：参与能力画像、弱项选题
        POSITION = 'position', '专业能力类'
        EMERGENCY = 'emergency', '专业能力类'
        COMPREHENSIVE = 'comprehensive', '专业能力类'
        # 属性类：只用于统计筛选和分组，不参与能力画像和选题
        FORM = 'form', '考核形式'        # 理论 / 实操
        DEPTH = 'depth', '难度层次'      # 基础 / 提升
        LINE = 'line', '适用线路'        # 3号线 / 11号线
        GRADE = 'grade', '适用等级'      # 站务员初级 ... 值班员高级技师

    # 参与能力画像、弱项选题的标签分类。新增属性类分类不要加到这里。
    ABILITY_CATEGORIES = ('position', 'emergency', 'comprehensive')

    name = models.CharField(max_length=50, unique=True, verbose_name='标签名称')
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.POSITION,
        verbose_name='标签分类'
    )

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        db_table = 'tags'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.get_category_display()}: {self.name}"


class Question(BaseTimestampedModel):
    """题目模型"""
    class QuestionType(models.TextChoices):
        SINGLE = 'single', '单选题'
        MULTIPLE = 'multiple', '多选题'
        TRUE_FALSE = 'true_false', '判断题'
        SUBJECTIVE = 'subjective', '主观题'

    class Difficulty(models.TextChoices):
        EASY = '易', '易'
        MEDIUM = '中', '中'
        HARD = '难', '难'

    content = models.TextField(verbose_name='题目题干')
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.SINGLE,
        verbose_name='题目类型'
    )
    options = models.JSONField(
        verbose_name='选项列表',
        help_text='JSON格式，示例: [{"key": "A", "text": "选项内容"}]，主观题可为空或填写答题提示',
        null=True,
        blank=True
    )
    correct_answer = models.TextField(
        verbose_name='正确答案/参考答案',
        help_text='单选题填字母，多选题用逗号分隔，判断题填True/False，主观题填写参考答案或评分标准'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='questions',
        verbose_name='关联标签'
    )
    difficulty = models.CharField(
        max_length=2,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
        db_index=True,
        verbose_name='难易度',
        help_text='易 / 中 / 难，与题库 Excel 一致'
    )
    explanation = models.TextField(blank=True, verbose_name='答案解析')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    # 题库来源与分类，用于统计分析（普通列，可直接 GROUP BY）
    bank_subject = models.CharField(
        max_length=50, blank=True, default='', db_index=True,
        verbose_name='题库专业', help_text='题库文件所属专业，如：客运专业'
    )
    assessment_subject = models.CharField(
        max_length=50, blank=True, default='', db_index=True,
        verbose_name='测评专业', help_text='如：城轨值班员'
    )
    category_l1 = models.CharField(max_length=100, blank=True, default='', db_index=True, verbose_name='一级目录')
    category_l2 = models.CharField(max_length=100, blank=True, default='', db_index=True, verbose_name='二级目录')
    category_l3 = models.CharField(max_length=100, blank=True, default='', db_index=True, verbose_name='三级目录')
    score = models.FloatField(
        null=True, blank=True, verbose_name='试题分数',
        help_text='题库原始分值，仅记录，当前组卷仍按总分100平均分配'
    )
    knowledge_point = models.CharField(max_length=50, blank=True, default='', db_index=True, verbose_name='知识点')
    shuffle_options = models.BooleanField(
        default=True, verbose_name='允许打乱选项',
        help_text='仅对单选、多选生效。选项含"以上皆是""C和D"等依赖位置的措辞时应关闭'
    )

    class Meta:
        verbose_name = '题目'
        verbose_name_plural = '题目'
        db_table = 'questions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_question_type_display()}: {self.content[:50]}..."


class ExamPaper(BaseTimestampedModel):
    """考试试卷模型"""
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', '未开始'
        IN_PROGRESS = 'in_progress', '进行中'
        COMPLETED = 'completed', '已完成'

    class GenerationReason(models.TextChoices):
        DAILY_PRACTICE = 'daily_practice', '日常练习'
        ERROR_REVIEW = 'error_review', '错题回顾'
        MANDATORY_ASSESSMENT = 'mandatory_assessment', '强制考核'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='exam_papers',
        verbose_name='考生'
    )
    title = models.CharField(max_length=200, default='智能考核试卷', verbose_name='试卷标题')
    total_score = models.FloatField(default=100.0, verbose_name='试卷总分')
    score_obtained = models.FloatField(null=True, blank=True, verbose_name='实际得分')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
        verbose_name='试卷状态'
    )
    generation_reason = models.CharField(
        max_length=30,
        choices=GenerationReason.choices,
        default=GenerationReason.DAILY_PRACTICE,
        verbose_name='生成原因'
    )
    time_limit = models.PositiveIntegerField(default=1800, verbose_name='考试时限（秒）')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '考试试卷'
        verbose_name_plural = '考试试卷'
        db_table = 'exam_papers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.job_number} - {self.title} ({self.get_status_display()})"


class ExamRecord(BaseTimestampedModel):
    """答题记录模型"""
    paper = models.ForeignKey(
        ExamPaper,
        on_delete=models.CASCADE,
        related_name='exam_records',
        verbose_name='归属试卷'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='exam_records',
        verbose_name='对应题目'
    )
    user_answer = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='用户答案'
    )
    is_correct = models.BooleanField(null=True, blank=True, verbose_name='是否正确')
    score_gained = models.FloatField(default=0.0, verbose_name='得分')
    ai_score = models.FloatField(null=True, blank=True, verbose_name='AI评分(0-100)')
    duration = models.PositiveIntegerField(default=0, verbose_name='答题耗时（秒）')
    option_order = models.JSONField(
        null=True, blank=True, verbose_name='选项显示顺序',
        help_text='组卷时生成，如 ["C","A","D","B"] 表示第1个位置显示原选项C。为空表示按原顺序'
    )

    class Meta:
        verbose_name = '答题记录'
        verbose_name_plural = '答题记录'
        db_table = 'exam_records'
        unique_together = ['paper', 'question']
        ordering = ['paper', 'id']

    def __str__(self):
        return f"{self.paper.user.job_number} - 题目{self.question.id} - ({'正确' if self.is_correct else '错误'})"