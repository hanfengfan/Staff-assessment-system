"""员工标签维度。统计分析按岗位/车站/站区分组或筛选时，统一从这里取维度。

用法示例（后续统计接口）：
    qs = apply_dimension_filters(ExamPaper.objects.all(), request.query_params, prefix='user__')
    rows = group_by_dimension(qs, request.query_params['group_by'], prefix='user__')
新增维度只需在 DIMENSIONS 里加一项（字段必须是 User 上的字段）。
"""
from django.db.models import Count, F

from .models import User

DIMENSIONS = {
    'position': '岗位',
    'station': '所属车站',
    'zone': '所属站区',
}


def dimension_options():
    """每个维度当前有哪些取值及人数，仅统计普通员工。"""
    staff = User.objects.filter(is_staff=False)
    result = []
    for key, label in DIMENSIONS.items():
        rows = (staff.exclude(**{key: ''})
                .values(key).annotate(count=Count('id')).order_by(key))
        result.append({
            'key': key,
            'label': label,
            'options': [{'value': r[key], 'count': r['count']} for r in rows],
        })
    return result


def apply_dimension_filters(queryset, params, prefix=''):
    """按 params 中出现的维度参数过滤；prefix 为到 User 的关联路径，如 'user__'。"""
    for key in DIMENSIONS:
        value = params.get(key)
        if value:
            queryset = queryset.filter(**{f'{prefix}{key}': value})
    return queryset


def group_by_dimension(queryset, dimension, prefix=''):
    """按某个维度分组计数，返回 [{'dimension_value': ..., 'count': ...}]。"""
    if dimension not in DIMENSIONS:
        raise ValueError(f'未知维度: {dimension}')
    return list(queryset.values(dimension_value=F(prefix + dimension))
                .annotate(count=Count('id')).order_by('dimension_value'))

