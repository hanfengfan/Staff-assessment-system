"""题库 Excel 导入（客运中心各专业题库格式）。

按表头名读列，不依赖列位置。列与数据库的对应关系：

    题库专业/测评专业/一二三级目录/试题分数/知识点 -> Question 同名列
    试题标题/试题题型/试题选择项/正确答案/难易度/解析 -> content/question_type/options/correct_answer/difficulty/explanation
    理论 实操 | 基础 提升 | 3号线 11号线 | 8 个等级列   -> 单元格有 √ 就给该题挂上同名标签
    序号、对应教材章节                                  -> 不导入

用法见 core/management/commands/import_question_bank.py。
"""
import json
import re

import openpyxl
from django.db import transaction

from .models import Question, Tag
from .option_shuffle import options_depend_on_position

REQUIRED_COLUMNS = ['试题标题', '试题题型', '试题选择项', '正确答案', '难易度']

QTYPE_MAP = {
    '单项选择题': Question.QuestionType.SINGLE,
    '多项选择题': Question.QuestionType.MULTIPLE,
    '判断题': Question.QuestionType.TRUE_FALSE,
}

# 列名 -> 标签分类。列里有 √ 就挂上与列名同名的标签。
TAG_COLUMNS = {
    '理论': Tag.Category.FORM, '实操': Tag.Category.FORM,
    '基础': Tag.Category.DEPTH, '提升': Tag.Category.DEPTH,
    '3号线': Tag.Category.LINE, '11号线': Tag.Category.LINE,
    '站务员初级': Tag.Category.GRADE, '站务员中级': Tag.Category.GRADE, '站务员高级': Tag.Category.GRADE,
    '值班员初级': Tag.Category.GRADE, '值班员中级': Tag.Category.GRADE, '值班员高级': Tag.Category.GRADE,
    '值班员技师': Tag.Category.GRADE, '值班员高级技师': Tag.Category.GRADE,
}

MARKS = {'√', '✓', '✔', '是', 'Y', 'y', '1', 'TRUE', 'true', 'True'}
TRUE_WORDS = {'正确', '对', '√', 'T', 'TRUE', 'True', 'true'}
FALSE_WORDS = {'错误', '错', '×', 'F', 'FALSE', 'False', 'false'}

# 连续这么多行完全为空就认为数据结束（有的文件工作表被撑到一百多万行）
BLANK_ROWS_TO_STOP = 100

_OPT_SPLIT = re.compile(r'\s*\|\s*(?=[A-Za-z]\s*[\.．、])')
_OPT_ITEM = re.compile(r'^([A-Za-z])\s*[\.．、]\s*(.*)$', re.S)


def clean(value):
    """去掉 Excel 导出残留的 _x000D_ 和回车，首尾空白。"""
    if value is None:
        return ''
    return str(value).replace('_x000D_', '').replace('\r', '').strip()


def is_marked(value):
    return clean(value) in MARKS


def parse_options(raw):
    """'A.xxx\\n|B.yyy' -> [{'key': 'A', 'text': 'xxx'}, ...]；格式不对返回 None。"""
    opts = []
    for part in _OPT_SPLIT.split(clean(raw)):
        m = _OPT_ITEM.match(part.strip())
        if not m or not m.group(2).strip():
            return None
        opts.append({'key': m.group(1).upper(), 'text': m.group(2).strip()})
    return opts or None


def parse_answer_letters(raw):
    return [p.upper() for p in re.split(r'[|,，、\s]+', clean(raw)) if p]


def parse_true_false(raw_options, raw_answer):
    """判断题答案统一成 'True' / 'False'；识别不了返回 None。"""
    answer = clean(raw_answer)
    if answer in TRUE_WORDS:
        return 'True'
    if answer in FALSE_WORDS:
        return 'False'
    # 另一种写法：选项 "A.对|B.错"，答案填 A / B
    opts = parse_options(raw_options)
    if opts:
        text = {o['key']: o['text'] for o in opts}.get(answer.upper())
        if text in TRUE_WORDS:
            return 'True'
        if text in FALSE_WORDS:
            return 'False'
    return None


class ImportResult:
    def __init__(self):
        self.created = 0
        self.by_type = {}
        self.skipped_dup_in_file = 0
        self.skipped_dup_in_db = 0
        self.skipped_invalid = 0
        self.tags_created = []
        self.tag_links = 0
        self.messages = []   # (level, text)，level: 'warning' | 'error'
        self.review = []     # 需要人工复核但已导入的题

    def warn(self, text):
        self.messages.append(('warning', text))

    def error(self, text):
        self.messages.append(('error', text))

    @property
    def summary(self):
        types = '、'.join(f'{k} {v}' for k, v in self.by_type.items()) or '无'
        return (
            f'导入 {self.created} 题（{types}）；'
            f'文件内重复跳过 {self.skipped_dup_in_file}；'
            f'库中已存在跳过 {self.skipped_dup_in_db}；'
            f'无效跳过 {self.skipped_invalid}；'
            f'新建标签 {len(self.tags_created)} 个，挂标签 {self.tag_links} 次'
        )


def read_sheet(path):
    """读第一个工作表，返回 (表头列表, [(Excel行号, 行数据)])。

    用只读模式，并在连续多行全空后停止：有的文件工作表范围被撑到一百多万行。
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        it = wb.worksheets[0].iter_rows(values_only=True)
        header = next(it, None)
        if header is None:
            raise ValueError('文件是空的')
        header = [clean(h) for h in header]
        rows, blank = [], 0
        for excel_row, row in enumerate(it, start=2):
            if all(clean(c) == '' for c in row):
                blank += 1
                if blank >= BLANK_ROWS_TO_STOP:
                    break
                continue
            blank = 0
            rows.append((excel_row, row))
        return header, rows
    finally:
        wb.close()


class _Importer:
    def __init__(self, col, tag_cols, default_bank_subject, result):
        self.col = col
        self.tag_cols = tag_cols
        self.default_bank_subject = default_bank_subject
        self.result = result
        self.tag_cache = {}
        self.seen = {}              # 题干 -> (第一次出现的行描述, 指纹集合)
        self.multi_all_options = 0
        # 只和导入开始前就存在的题比对；本次导入中新建的题由文件内去重处理
        self.max_existing_id = Question.objects.order_by('-id').values_list('id', flat=True).first() or 0

    def cell(self, row, name):
        i = self.col.get(name)
        return row[i] if i is not None and i < len(row) else None

    def text(self, row, name):
        return clean(self.cell(row, name))

    def get_tag(self, name, category):
        tag = self.tag_cache.get(name)
        if tag is None:
            tag = Tag.objects.filter(name=name).first()
            if tag is None:
                tag = Tag.objects.create(name=name, category=category)
                self.result.tags_created.append(name)
            elif tag.category != category:
                self.result.warn(f'标签"{name}"已存在，但分类是 {tag.category}（期望 {category}），沿用已有标签')
            self.tag_cache[name] = tag
        return tag

    def skip_invalid(self, where, reason):
        self.result.skipped_invalid += 1
        self.result.error(f'{where}: {reason}，已跳过')

    def import_row(self, excel_row, row):
        r = self.result
        seq = self.text(row, '序号')
        where = f'第{excel_row}行' + (f'(序号{seq})' if seq else '')

        content = self.text(row, '试题标题')
        if not content:
            return self.skip_invalid(where, '试题标题为空')
        qtype = QTYPE_MAP.get(self.text(row, '试题题型'))
        if qtype is None:
            return self.skip_invalid(where, f'未知题型"{self.text(row, "试题题型")}"')

        # --- 选项与答案 ---
        raw_options, raw_answer = self.cell(row, '试题选择项'), self.cell(row, '正确答案')
        if qtype == Question.QuestionType.TRUE_FALSE:
            correct = parse_true_false(raw_options, raw_answer)
            if correct is None:
                return self.skip_invalid(where, f'判断题答案无法识别"{clean(raw_answer)}"')
            options = [{'key': 'True', 'text': '正确'}, {'key': 'False', 'text': '错误'}]
        else:
            options = parse_options(raw_options)
            if not options or len(options) < 2:
                return self.skip_invalid(where, '选项无法解析或不足两个')
            keys = [o['key'] for o in options]
            if len(set(keys)) != len(keys):
                return self.skip_invalid(where, f'选项字母重复 {keys}')
            letters = sorted(set(parse_answer_letters(raw_answer)))
            if not letters:
                return self.skip_invalid(where, '正确答案为空')
            outside = [a for a in letters if a not in keys]
            if outside:
                return self.skip_invalid(where, f'答案{letters}超出选项范围{keys}（可能缺少选项，请检查原表）')
            if qtype == Question.QuestionType.SINGLE and len(letters) != 1:
                return self.skip_invalid(where, f'单选题答案应只有一个，实际为{letters}')
            correct = ','.join(letters)
            if qtype == Question.QuestionType.MULTIPLE:
                if len(letters) == 1:
                    r.review.append(f'{where}: 多选题只有一个正确答案 {letters[0]}')
                if len(letters) == len(keys):
                    self.multi_all_options += 1
            if options_depend_on_position(options):
                r.review.append(f'{where}: 选项可能依赖位置或其他选项（如"以上皆是"），请确认是否需要关闭"允许打乱选项"')

        # --- 去重：题干 + 选项 + 答案都相同才算重复 ---
        fingerprint = json.dumps([options, correct], ensure_ascii=False, sort_keys=True)
        prev = self.seen.get(content)
        if prev and fingerprint in prev[1]:
            r.skipped_dup_in_file += 1
            r.warn(f'{where}: 与{prev[0]}题干、选项、答案均相同，已跳过')
            return
        if prev:
            r.review.append(f'{where}: 题干与{prev[0]}相同，但选项或答案不同，两道都已保留')
            prev[1].add(fingerprint)
        else:
            self.seen[content] = (where, {fingerprint})
        same_content = list(Question.objects.filter(content=content, id__lte=self.max_existing_id))
        if any(q.options == options and q.correct_answer == correct for q in same_content):
            r.skipped_dup_in_db += 1
            r.warn(f'{where}: 库中已有相同的题，已跳过')
            return
        if same_content:
            r.review.append(f'{where}: 题干与库中第{same_content[0].id}题相同，但选项或答案不同，已导入')

        # --- 难易度、分数 ---
        level = self.text(row, '难易度')
        if level not in Question.Difficulty.values:
            r.warn(f'{where}: 难易度"{level}"无法识别，按"中"处理')
            level = Question.Difficulty.MEDIUM
        score = None
        raw_score = self.text(row, '试题分数')
        if raw_score:
            try:
                score = float(raw_score)
            except ValueError:
                r.warn(f'{where}: 试题分数"{raw_score}"不是数字，已留空')

        question = Question.objects.create(
            content=content,
            question_type=qtype,
            options=options,
            correct_answer=correct,
            difficulty=level,
            explanation=self.text(row, '解析'),
            bank_subject=self.text(row, '题库专业') or self.default_bank_subject,
            assessment_subject=self.text(row, '测评专业'),
            category_l1=self.text(row, '一级目录'),
            category_l2=self.text(row, '二级目录'),
            category_l3=self.text(row, '三级目录'),
            score=score,
            knowledge_point=self.text(row, '知识点'),
            is_active=True,
        )
        tags = [self.get_tag(name, TAG_COLUMNS[name]) for name in self.tag_cols
                if is_marked(self.cell(row, name))]
        question.tags.set(tags)
        r.tag_links += len(tags)
        if not tags:
            r.review.append(f'{where}: 理论/实操、等级等列都没有 √，未挂任何标签')
        r.created += 1
        label = question.get_question_type_display()
        r.by_type[label] = r.by_type.get(label, 0) + 1


def import_question_bank(path, dry_run=False, default_bank_subject=''):
    """导入一份题库 Excel，返回 ImportResult。

    整个文件在一个事务里：出现意外异常整体回滚；dry_run=True 时走完全部流程再回滚，
    因此报告里的数量与正式导入一致。
    """
    result = ImportResult()
    header, rows = read_sheet(path)
    col = {}
    for i, h in enumerate(header):
        if h and h not in col:
            col[h] = i
    missing = [c for c in REQUIRED_COLUMNS if c not in col]
    if missing:
        raise ValueError(f'缺少必需的列: {", ".join(missing)}')
    if '题库专业' not in col and not default_bank_subject:
        raise ValueError('表中没有"题库专业"列，请用 --bank-subject 指定')
    tag_cols = [c for c in TAG_COLUMNS if c in col]
    for c in TAG_COLUMNS:
        if c not in col:
            result.warn(f'表中没有"{c}"列，该标签不会被挂载')

    importer = _Importer(col, tag_cols, default_bank_subject, result)
    with transaction.atomic():
        for excel_row, row in rows:
            importer.import_row(excel_row, row)
        if importer.multi_all_options:
            result.review.append(
                f'共 {importer.multi_all_options} 道多选题的正确答案是全部选项，考生全选即可得分，请确认是否符合题库本意')
        if dry_run:
            transaction.set_rollback(True)
    return result
