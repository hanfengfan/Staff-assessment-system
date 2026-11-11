"""组卷：按管理员设定的规则抽题。

流程：
1. 候选池 = 规则里的题库专业下所有启用的题；普通员工再按其岗位级别标签筛一遍。
2. 按各题型数量逐题型抽取；每个题型内部再按难度分层比例分配。
3. 有一级目录权重时，优先从权重高的目录里抽，不够再从整个题库专业补。
"""
import random

from .models import Question, Tag

TYPE_ORDER = ['single', 'multiple', 'true_false', 'subjective']
LEVELS = ['易', '中', '难']


class ComposeError(Exception):
    """规则缺失或候选题不足时抛出，消息可直接展示给用户。"""


def candidate_pool(config, user=None):
    """候选题。普通员工先按所属线路、再按岗位级别筛，只保留同时带有这两个标签的题。"""
    qs = Question.objects.filter(is_active=True, bank_subject__in=config.bank_subjects)
    if user is not None and not user.is_staff:
        checks = (
            ('所属线路', user.line, Tag.Category.LINE),
            ('岗位级别', user.grade, Tag.Category.GRADE),
        )
        for label, value, category in checks:
            if not value:
                raise ComposeError(f'您还没有设置{label}，请联系管理员在人员管理中设置')
            tag = Tag.objects.filter(name=value, category=category).first()
            if tag is None:
                raise ComposeError(f'{label}“{value}”没有对应的题目标签，请联系管理员')
            qs = qs.filter(tags=tag)
        if not qs.exists():
            raise ComposeError(
                f'所选题库专业中没有适用于“{user.line}·{user.grade}”的题目，请联系管理员调整组卷规则')
    return qs


def split_by_ratio(total, ratio):
    """把 total 按比例分给各难度，返回 {难度: 数量}，数量之和恒等于 total。"""
    weights = {k: float(ratio.get(k, 0) or 0) for k in LEVELS}
    s = sum(weights.values())
    if total <= 0 or s <= 0:
        return {}
    raw = {k: total * w / s for k, w in weights.items()}
    got = {k: int(v) for k, v in raw.items()}
    # 把取整丢掉的名额按小数部分从大到小补回
    for k in sorted(raw, key=lambda k: raw[k] - got[k], reverse=True)[: total - sum(got.values())]:
        got[k] += 1
    return {k: n for k, n in got.items() if n > 0}


def draw(items, n, weights, rng):
    """从 items [(id, 一级目录)] 里抽 n 个 id。

    有权重时：权重大于 0 的目录按权重从高到低分档，先抽最高档，不够再抽下一档，
    所有权重目录都抽完仍不够，再从剩下的题（含未设权重的目录）里随机补。
    """
    if n <= 0 or not items:
        return []
    chosen, remaining = [], list(items)
    for w in sorted({v for v in weights.values() if v > 0}, reverse=True):
        if len(chosen) >= n:
            break
        tier = [it for it in remaining if weights.get(it[1], 0) == w]
        picked = rng.sample(tier, min(n - len(chosen), len(tier)))
        chosen += picked
        taken = {it[0] for it in picked}
        remaining = [it for it in remaining if it[0] not in taken]
    if len(chosen) < n and remaining:
        chosen += rng.sample(remaining, min(n - len(chosen), len(remaining)))
    return [it[0] for it in chosen]


def _draw_type(rows, count, config, rng):
    """单个题型：先按难度分层抽，层内不够的名额再从该题型剩余题里补。"""
    weights = config.category_weights or {}
    by_level = {lv: [(i, c) for i, c, d in rows if d == lv] for lv in LEVELS}
    picked, used = [], set()
    for lv, k in split_by_ratio(count, config.difficulty_ratio or {}).items():
        ids = draw(by_level[lv], k, weights, rng)
        picked += ids
        used.update(ids)
    rest = [(i, c) for i, c, _ in rows if i not in used]
    return picked + draw(rest, count - len(picked), weights, rng)


def compose_exam(config, user=None, rng=random):
    """按规则抽题。返回 (题目列表, 提示列表)。完全抽不到题时抛 ComposeError。"""
    pool = candidate_pool(config, user)
    wanted = {t: int(config.type_counts.get(t, 0) or 0) for t in TYPE_ORDER}
    wanted = {t: n for t, n in wanted.items() if n > 0}
    if not wanted:
        raise ComposeError('组卷规则里没有设置任何题型的数量')
    ids, notes = [], []
    for t in TYPE_ORDER:
        if t not in wanted:
            continue
        rows = list(pool.filter(question_type=t).values_list('id', 'category_l1', 'difficulty'))
        got = _draw_type(rows, wanted[t], config, rng)
        if len(got) < wanted[t]:
            notes.append(f'{t} 题型只抽到 {len(got)}/{wanted[t]} 道')
        ids += got
    # 某题型不够时，从候选池里其他没抽过的题补满总题数
    target = sum(wanted.values())
    if len(ids) < target:
        rest = [(i, c) for i, c in pool.exclude(id__in=ids).values_list('id', 'category_l1')]
        ids += draw(rest, target - len(ids), config.category_weights or {}, rng)
    if not ids:
        raise ComposeError('候选题库里没有符合条件的题目，请联系管理员调整组卷规则或题库')
    if len(ids) < target:
        notes.append(f'题库题量不足，实际只组了 {len(ids)}/{target} 题')
    order = {i: n for n, i in enumerate(ids)}
    questions = sorted(Question.objects.filter(id__in=ids), key=lambda q: order[q.id])
    return questions, notes
