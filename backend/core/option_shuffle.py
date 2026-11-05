"""选择题选项打乱。

题库里的 options / correct_answer 始终保持原始顺序和原始 key，打乱只发生在组卷时：
为每条答题记录（ExamRecord）生成一个排列 option_order，例如 ["C", "A", "D", "B"]，
表示考生看到的第 1 个位置（A）显示原选项 C 的文本，第 2 个位置（B）显示原选项 A，依此类推。

- 考生看到、提交的都是显示字母（A、B、C...），user_answer 存的也是显示字母。
- 判分时先把显示字母还原成原始 key，再与 correct_answer 比较。
- option_order 为空（历史记录、判断题、主观题、关闭了打乱的题）时一律按原顺序处理。
"""
import random
import re
import string

SHUFFLE_TYPES = ('single', 'multiple')


def make_option_order(question, rng=random):
    """组卷时调用：返回原始 key 的随机排列；不需要打乱时返回 None。"""
    if not question.shuffle_options or question.question_type not in SHUFFLE_TYPES:
        return None
    keys = [o['key'] for o in (question.options or [])]
    if len(keys) < 2:
        return None
    order = keys[:]
    rng.shuffle(order)
    return order


def _usable(question, order):
    """排列必须和当前选项的 key 一一对应；题目在组卷后被改过选项时放弃使用，按原顺序处理。"""
    if not order or not question.options:
        return None
    if sorted(order) != sorted(o['key'] for o in question.options):
        return None
    return order


def split_answer(answer):
    """把 "A,B" / ["A", "B"] 统一成大写 key 列表。"""
    if isinstance(answer, (list, tuple)):
        parts = answer
    else:
        parts = re.split(r'[,\s]+', str(answer or ''))
    return [str(p).strip().upper() for p in parts if str(p).strip()]


def shuffled_options(question, order):
    """返回按排列重排后的选项：位置字母固定为 A、B、C...，文本取自对应的原选项。"""
    order = _usable(question, order)
    if not order:
        return question.options
    text_by_key = {o['key']: o['text'] for o in question.options}
    return [{'key': string.ascii_uppercase[i], 'text': text_by_key[k]} for i, k in enumerate(order)]


def displayed_to_original(question, order, answer):
    """考生提交的显示字母 -> 原始 key 列表。无法对应的字母会变成不可能匹配的占位值。"""
    letters = split_answer(answer)
    order = _usable(question, order)
    if not order:
        return letters
    result = []
    for letter in letters:
        idx = string.ascii_uppercase.find(letter) if len(letter) == 1 else -1
        result.append(order[idx] if 0 <= idx < len(order) else '?' + letter)
    return result


def display_correct_answer(question, order):
    """正确答案（原始 key）-> 考生视角的显示字母，用于结果页。非选择题原样返回。"""
    if question.question_type not in SHUFFLE_TYPES:
        return question.correct_answer
    keys = split_answer(question.correct_answer)
    order = _usable(question, order)
    if not order:
        return ','.join(sorted(keys))
    return ','.join(sorted(string.ascii_uppercase[order.index(k)] for k in keys if k in order))


def is_choice_correct(question, order, user_answer):
    """单选、多选判分：按集合比较，与勾选顺序无关。"""
    given = set(displayed_to_original(question, order, user_answer))
    correct = set(split_answer(question.correct_answer))
    return bool(given) and given == correct


# 选项文本依赖位置或其他选项的措辞，打乱后会读不通
_POSITION_DEPENDENT = re.compile(
    r'(?<!及)以上(?:皆|均|都|全|说法|选项|答案|各|几|三|四|所有|两)'
    r'|上述'
    r'|(?:全部|都|均|皆)(?:正确|对|是|错误|不对|不正确)'
    r'|(?:^|[^A-Za-z])[A-E]\s*[和、与及,，]\s*[A-E](?:$|[^A-Za-z])'
    r'|选项\s*[A-E]|[A-E]\s*项'
    r'|以上.{0,3}(?:正确|错误|都|均)'
)


def options_depend_on_position(options):
    """导入题目时用：判断一组选项是否应关闭打乱。"""
    return any(_POSITION_DEPENDENT.search(o.get('text', '') or '') for o in (options or []))
