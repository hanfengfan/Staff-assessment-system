"""
从 Excel 文件批量导入题目，字段: 序号,题型,题目,选项A,选项B,选项C,选项D,答案,标签

用法:
  python manage.py import_questions_excel /path/to/file.xlsx --dry-run   # 先试运行，不写库
  python manage.py import_questions_excel /path/to/file.xlsx             # 正式导入
"""
from django.core.management.base import BaseCommand, CommandError
from core.question_import import import_questions_from_workbook


class Command(BaseCommand):
    help = '从 Excel 批量导入题目及其标签关联'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Excel 文件路径')
        parser.add_argument('--dry-run', action='store_true', help='只校验并打印结果，不写入数据库')

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        try:
            result = import_questions_from_workbook(file_path, dry_run=dry_run)
        except FileNotFoundError:
            raise CommandError(f'找不到文件: {file_path}')

        for level, text in result.messages:
            style = self.style.ERROR if level == 'error' else self.style.WARNING
            self.stdout.write(style(text))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{"[试运行] " if dry_run else ""}处理完成: {result.summary}'
        ))
        if result.missing_tags:
            self.stdout.write(self.style.ERROR(
                f'警告: 以下标签在数据库中不存在，相关题目已跳过关联这些标签: {sorted(result.missing_tags)}'
            ))
