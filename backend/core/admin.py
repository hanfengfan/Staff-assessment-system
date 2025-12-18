from django.contrib import admin
from .models import Tag, Question, ExamPaper, ExamRecord


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name',)
    ordering = ('category', 'name')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('content_short', 'question_type', 'difficulty', 'is_active', 'created_at')
    list_filter = ('question_type', 'difficulty', 'is_active', 'tags', 'created_at')
    search_fields = ('content', 'explanation')
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at')

    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = '题目内容'

    fieldsets = (
        ('基本信息', {
            'fields': ('content', 'question_type', 'difficulty', 'is_active')
        }),
        ('答案设置', {
            'fields': ('options', 'correct_answer', 'explanation'),
            'description': '注意：主观题的options字段可以为空，或在其中填写答题提示'
        }),
        ('标签', {
            'fields': ('tags',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'options':
            kwargs['help_text'] = '客观题：JSON格式的选项列表，如[{"key": "A", "text": "选项A"}]；主观题：可留空或填写答题提示'
        if db_field.name == 'correct_answer':
            kwargs['help_text'] = '客观题：正确答案；主观题：参考答案或评分标准'
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class ExamRecordInline(admin.TabularInline):
    model = ExamRecord
    extra = 0
    readonly_fields = ('is_correct', 'score_gained', 'duration')
    fields = ('question', 'user_answer', 'is_correct', 'score_gained', 'duration')


@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'status', 'score_obtained', 'generation_reason', 'created_at')
    list_filter = ('status', 'generation_reason', 'created_at')
    search_fields = ('user__job_number', 'user__username', 'title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ExamRecordInline]


@admin.register(ExamRecord)
class ExamRecordAdmin(admin.ModelAdmin):
    list_display = ('paper', 'question_short', 'user_answer', 'is_correct', 'score_gained', 'duration')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('paper__user__job_number', 'question__content')

    def question_short(self, obj):
        return obj.question.content[:30] + '...' if len(obj.question.content) > 30 else obj.question.content
    question_short.short_description = '题目内容'