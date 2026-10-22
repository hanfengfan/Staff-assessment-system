from django import forms
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path, reverse

from .models import Tag, Question, ExamPaper, ExamRecord
from .question_import import import_questions_from_workbook, import_questions_from_csv


class QuestionImportForm(forms.Form):
    file = forms.FileField(label='题目文件 (.xlsx 或 .csv)')
    dry_run = forms.BooleanField(
        label='仅校验，不写入数据库（试运行）',
        required=False,
        initial=True,
    )


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
    actions = ['enable_questions', 'disable_questions']
    change_list_template = 'admin/core/question/change_list.html'

    def get_urls(self):
        urls = [
            path('import-excel/', self.admin_site.admin_view(self.import_excel), name='core_question_import_excel'),
        ]
        return urls + super().get_urls()

    def import_excel(self, request):
        if request.method == 'POST':
            form = QuestionImportForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded = form.cleaned_data['file']
                dry_run = form.cleaned_data['dry_run']
                name = uploaded.name.lower()

                try:
                    if name.endswith('.csv'):
                        result = import_questions_from_csv(uploaded, dry_run=dry_run)
                    elif name.endswith('.xlsx'):
                        result = import_questions_from_workbook(uploaded, dry_run=dry_run)
                    else:
                        messages.error(request, '不支持的文件格式，请上传 .xlsx 或 .csv 文件')
                        return redirect('..')
                except Exception as exc:
                    messages.error(request, f'导入失败: {exc}')
                    return redirect('..')

                level = messages.INFO if dry_run else messages.SUCCESS
                prefix = '[试运行] ' if dry_run else ''
                messages.add_message(request, level, f'{prefix}{result.summary}')

                for msg_level, text in result.messages[:50]:
                    messages.add_message(
                        request,
                        messages.WARNING if msg_level == 'warning' else messages.ERROR,
                        text,
                    )
                if len(result.messages) > 50:
                    messages.warning(request, f'还有 {len(result.messages) - 50} 条提示未显示，请检查源文件')

                if result.missing_tags:
                    messages.error(request, f'以下标签在数据库中不存在，相关题目已跳过关联这些标签: {sorted(result.missing_tags)}')

                return redirect('..')
        else:
            form = QuestionImportForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'title': '批量导入题目',
            'opts': self.model._meta,
        }
        return render(request, 'admin/core/question/import_excel.html', context)

    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = '题目内容'

    def enable_questions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'已启用 {updated} 道题目')
    enable_questions.short_description = '启用选中的题目'

    def disable_questions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'已禁用 {updated} 道题目')
    disable_questions.short_description = '禁用选中的题目'

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
    search_fields = ('user__job_number', 'user__name', 'title')
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