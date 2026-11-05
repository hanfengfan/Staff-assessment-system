from django.core.management.base import BaseCommand, CommandError

from core.bank_import import import_question_bank

SHOW_LIMIT = 60


class Command(BaseCommand):
    help = (
        '导入客运中心题库 Excel（按表头名读列）。默认只试运行：校验并输出报告，不写库；'
        '确认无误后加 --commit 才会正式导入。'
    )

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', help='一个或多个 .xlsx 文件路径')
        parser.add_argument('--commit', action='store_true', help='正式写入数据库（默认只试运行）')
        parser.add_argument('--bank-subject', default='', help='表中没有"题库专业"列时用它指定')

    def handle(self, *args, **options):
        dry_run = not options['commit']
        self.stdout.write(self.style.WARNING('【试运行】不会写入数据库') if dry_run
                          else self.style.SUCCESS('【正式导入】'))
        for path in options['files']:
            self.stdout.write(f'\n=== {path}')
            try:
                result = import_question_bank(
                    path, dry_run=dry_run, default_bank_subject=options['bank_subject'])
            except FileNotFoundError:
                raise CommandError(f'找不到文件: {path}')
            except ValueError as exc:
                raise CommandError(f'{path}: {exc}')
            self.report(result)
        if dry_run:
            self.stdout.write(self.style.WARNING('\n以上为试运行结果，确认无误后加 --commit 正式导入。'))

    def report(self, result):
        self.stdout.write(self.style.SUCCESS(result.summary))
        if result.tags_created:
            self.stdout.write('新建标签: ' + '、'.join(result.tags_created))
        errors = [t for lvl, t in result.messages if lvl == 'error']
        warnings = [t for lvl, t in result.messages if lvl == 'warning']
        self.block('被跳过的无效数据', errors, self.style.ERROR)
        self.block('提示', warnings, self.style.WARNING)
        self.block('需要人工复核（已导入）', result.review, self.style.NOTICE)

    def block(self, title, lines, style):
        if not lines:
            return
        self.stdout.write(style(f'\n{title}（{len(lines)}）:'))
        for line in lines[:SHOW_LIMIT]:
            self.stdout.write(f'  - {line}')
        if len(lines) > SHOW_LIMIT:
            self.stdout.write(f'  ... 还有 {len(lines) - SHOW_LIMIT} 条未显示')
