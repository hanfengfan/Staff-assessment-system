"""考生视角下题目标签的可见范围。

标签分类里有三类是"属于某个人"的：职位类（role）、适用线路（line）、适用等级（grade）。
一道题往往同时挂着多条线路、多个级别的标签，考生只应该看到和自己相同的那一个，
否则 3 号线的员工会在题目上看到"11号线""值班员技师"这类与自己无关的标签。
其余分类（能力类、考核形式、难度层次等）对所有人可见。管理员看到全部标签。
"""
from .models import Tag

# 标签分类 -> 员工上对应的字段
PERSONAL_CATEGORIES = {
    Tag.Category.ROLE.value: "position",
    Tag.Category.LINE.value: "line",
    Tag.Category.GRADE.value: "grade",
}


def sees_everything(user):
    return bool(user.is_staff or user.position == '系统管理员')


def visible_tags(tags, user):
    """tags: Tag 可迭代；user: 考生（试卷所有者）。返回 [{'id', 'name'}]。"""
    show_all = sees_everything(user)
    result = []
    for tag in tags:
        field = PERSONAL_CATEGORIES.get(tag.category)
        if field is None or show_all or tag.name == getattr(user, field, ''):
            result.append({'id': tag.id, 'name': tag.name})
    return result
