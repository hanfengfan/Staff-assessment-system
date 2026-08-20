"""
从 Excel 文件批量导入题目，字段: 序号,题型,题目,选项A,选项B,选项C,选项D,答案,标签

用法:
  python manage.py import_questions_excel /path/to/file.xlsx --dry-run   # 先试运行，不写库
  python manage.py import_questions_excel /path/to/file.xlsx             # 正式导入
"""
import openpyxl
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Tag, Question

QTYPE_MAP = {
    '单选': Question.QuestionType.SINGLE,
    '多选': Question.QuestionType.MULTIPLE,
    '判断题': Question.QuestionType.TRUE_FALSE,
}

OPTION_KEYS = ['A', 'B', 'C', 'D']

# 已知的原始数据笔误修正：第116题答案 'AR' 应为多选 'AB'（选项无 R，用户已确认）
ANSWER_OVERRIDES = {
    116: 'AB',
}


class Command(BaseCommand):
    help = '从 Excel 批量导入题目及其标签关联'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Excel 文件路径')
        parser.add_argument('--dry-run', action='store_true', help='只校验并打印结果，不写入数据库')

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        except FileNotFoundError:
            raise CommandError(f'找不到文件: {file_path}')

        ws = wb.worksheets[0]
        rows = list(ws.iter_rows(values_only=True))[1:]

        seen_contents = set()
        created_count = 0
        skipped_dup_in_file = 0
        skipped_existing_in_db = 0
        skipped_invalid = 0
        missing_tags = set()

        with transaction.atomic():
            for row in rows:
                seq, qtype_cn, content, opt_a, opt_b, opt_c, opt_d, answer, tags_cn = row[:9]

                if not content or not str(content).strip():
                    skipped_invalid += 1
                    self.stdout.write(self.style.WARNING(f'第{seq}行: 题目内容为空，跳过'))
                    continue
                content = str(content).strip()

                if content in seen_contents:
                    skipped_dup_in_file += 1
                    self.stdout.write(self.style.WARNING(f'第{seq}行: 文件内重复题目，跳过 -> {content[:30]}...'))
                    continue
                seen_contents.add(content)

                if Question.objects.filter(content=content).exists():
                    skipped_existing_in_db += 1
                    self.stdout.write(self.style.WARNING(f'第{seq}行: 数据库中已存在同内容题目，跳过 -> {content[:30]}...'))
                    continue

                qtype = QTYPE_MAP.get(str(qtype_cn).strip())
                if qtype is None:
                    skipped_invalid += 1
                    self.stdout.write(self.style.ERROR(f'第{seq}行: 未知题型 "{qtype_cn}"，跳过'))
                    continue

                raw_answer = ANSWER_OVERRIDES.get(seq, answer)
                raw_answer = str(raw_answer).strip() if raw_answer is not None else ''

                if qtype == Question.QuestionType.TRUE_FALSE:
                    options = [{"key": "True", "text": "正确"}, {"key": "False", "text": "错误"}]
                    if raw_answer == '正确':
                        correct_answer = 'True'
                    elif raw_answer == '错误':
                        correct_answer = 'False'
                    else:
                        skipped_invalid += 1
                        self.stdout.write(self.style.ERROR(f'第{seq}行: 判断题答案无法识别 "{raw_answer}"，跳过'))
                        continue
                else:
                    options = []
                    for key, text in zip(OPTION_KEYS, [opt_a, opt_b, opt_c, opt_d]):
                        if text is not None and str(text).strip():
                            options.append({"key": key, "text": str(text).strip()})

                    valid_keys = {o['key'] for o in options}
                    answer_letters = [c for c in raw_answer if c.strip()]
                    if not answer_letters or any(c not in valid_keys for c in answer_letters):
                        skipped_invalid += 1
                        self.stdout.write(self.style.ERROR(
                            f'第{seq}行: 答案 "{raw_answer}" 超出选项范围 {sorted(valid_keys)}，跳过'
                        ))
                        continue

                    if qtype == Question.QuestionType.SINGLE:
                        correct_answer = answer_letters[0]
                    else:
                        correct_answer = ','.join(answer_letters)

                tag_names = [t.strip() for t in str(tags_cn or '').split('、') if t.strip()]
                tag_objs = []
                for name in tag_names:
                    tag = Tag.objects.filter(name=name).first()
                    if tag is None:
                        missing_tags.add(name)
                    else:
                        tag_objs.append(tag)

                if dry_run:
                    created_count += 1
                    continue

                question = Question.objects.create(
                    content=content,
                    question_type=qtype,
                    options=options,
                    correct_answer=correct_answer,
                    difficulty=3,
                    is_active=True,
                )
                question.tags.set(tag_objs)
                created_count += 1

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{"[试运行] " if dry_run else ""}处理完成: 将{"会" if dry_run else ""}导入 {created_count} 条，'
            f'文件内重复跳过 {skipped_dup_in_file} 条，数据库已存在跳过 {skipped_existing_in_db} 条，'
            f'无效数据跳过 {skipped_invalid} 条'
        ))
        if missing_tags:
            self.stdout.write(self.style.ERROR(
                f'警告: 以下标签在数据库中不存在，相关题目已跳过关联这些标签: {sorted(missing_tags)}'
            ))
