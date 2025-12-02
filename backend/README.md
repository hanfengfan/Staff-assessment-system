# 轨道交通站务人员AI智能考核系统 - 后端

## 项目概述

这是一个基于Django REST Framework开发的智能考核系统后端，用于轨道交通站务人员的在线考核和能力评估。

## 技术栈

- **后端框架**: Django 4.x + Django REST Framework
- **数据库**: SQLite 3 (开发环境)
- **认证**: Token Authentication
- **其他**: CORS支持, JSON字段支持

## 项目结构

```
backend/
├── config/                 # Django项目配置
│   ├── settings.py        # 主要设置文件
│   ├── urls.py           # 根URL配置
│   └── wsgi.py           # WSGI配置
├── users/                # 用户管理应用
│   ├── models.py         # 扩展用户模型
│   ├── serializers.py    # 用户相关序列化器
│   ├── views.py          # 认证和用户管理视图
│   └── urls.py           # 用户相关URL
├── core/                 # 题库和考核核心应用
│   ├── models.py         # 题目、试卷、答题记录模型
│   ├── services.py       # 智能组卷和评分服务
│   ├── serializers.py    # 核心业务序列化器
│   ├── views.py          # 题目和考试相关视图
│   └── urls.py           # 核心业务URL
├── analysis/             # 能力分析应用
│   ├── models.py         # 能力画像、培训资料模型
│   ├── serializers.py    # 分析相关序列化器
│   ├── views.py          # 能力分析视图
│   └── urls.py           # 分析相关URL
├── manage.py             # Django管理脚本
├── requirements.txt      # Python依赖
└── db.sqlite3          # SQLite数据库文件
```

## 核心功能

### 1. 用户管理
- 扩展Django用户模型，支持工号、岗位、部门等字段
- Token认证机制
- 用户登录/登出功能

### 2. 题库管理
- 支持单选题、多选题、判断题
- 标签化分类管理
- JSON格式选项存储
- 题目难度设置

### 3. 智能组卷算法
- **弱项强化 (50%)**: 基于用户能力画像，优先选择掌握度<60的标签题目
- **基础巩固 (30%)**: 随机选择其他标签题目
- **新题探索 (20%)**: 选择用户从未做过的题目
- 自动排除用户最近24小时内做过的题目

### 4. 考试功能
- 试卷生成、开始、提交完整流程
- 自动评分机制
- 答题记录详细统计

### 5. 能力画像
- 动态评估用户在各标签下的能力水平
- 加权移动平均算法更新能力值
- 支持雷达图数据展示
- 能力趋势分析

## API接口

### 认证相关
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/logout/` - 用户登出
- `GET /api/auth/profile/` - 获取用户信息

### 考试相关
- `POST /api/exam/generate/` - 生成智能试卷
- `GET /api/exam/{id}/` - 获取试卷详情
- `POST /api/exam/{id}/start/` - 开始考试
- `POST /api/exam/{id}/submit/` - 提交试卷
- `GET /api/exam/` - 获取试卷列表

### 能力分析
- `GET /api/analysis/radar/` - 获取雷达图数据
- `GET /api/analysis/summary/` - 获取能力总结
- `GET /api/analysis/trend/` - 获取能力趋势
- `GET /api/analysis/recommendations/` - 获取学习建议

## 快速开始

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化
```bash
# 执行数据库迁移
python manage.py migrate

# 创建管理员用户
python manage.py init_admin

# 初始化示例数据
python manage.py init_sample_data
```

### 3. 启动服务
```bash
python manage.py runserver
```

### 4. 访问管理界面
- 管理员界面: http://127.0.0.1:8000/admin/
- API文档: http://127.0.0.1:8000/api/

## 默认账号

| 用户名 | 密码 | 工号 | 角色 |
|--------|------|------|------|
| admin | admin123 | ADMIN001 | 系统管理员 |
| zhangsan | password123 | ST001 | 值班站长 |
| lisi | password123 | ST002 | 站务员 |
| wangwu | password123 | ST003 | 客运值班员 |

## 核心算法说明

### 智能组卷策略
1. 分析用户能力画像，识别掌握度低于60分的弱项标签
2. 按比例分配题目：弱项强化50%、基础巩固30%、新题探索20%
3. 排除用户最近24小时内已经做过的题目
4. 随机抽题并创建试卷和答题记录

### 能力画像更新
使用加权移动平均算法：
```
新分数 = (旧分数 × 0.7) + (本次准确率 × 100 × 0.3)
```
- 权重0.7保证历史表现的稳定性
- 权重0.3体现近期表现的重要性

## 配置说明

在 `config/settings.py` 中的 `ASSESSMENT_SETTINGS` 可以配置：

```python
ASSESSMENT_SETTINGS = {
    'CAPABILITY_UPDATE_WEIGHT_OLD': 0.7,      # 旧分数权重
    'CAPABILITY_UPDATE_WEIGHT_NEW': 0.3,      # 新分数权重
    'DEFAULT_EXAM_QUESTION_COUNT': 15,        # 默认题目数量
    'WEAK_TAG_RATIO': 0.5,                    # 弱项题目比例
    'RANDOM_RATIO': 0.3,                      # 随机题目比例
    'NEW_QUESTION_RATIO': 0.2,                 # 新题比例
    'WEAK_CAPABILITY_THRESHOLD': 60,           # 弱项阈值
    'EXCLUDE_RECENT_HOURS': 24,                # 排除最近答题的小时数
}
```

## 部署说明

1. 确保所有依赖已安装
2. 配置生产环境数据库（PostgreSQL或MySQL）
3. 设置环境变量 `DJANGO_SETTINGS_MODULE=config.production`
4. 执行数据库迁移
5. 收集静态文件：`python manage.py collectstatic`
6. 使用WSGI服务器（如Gunicorn）部署

## 扩展功能

系统预留了以下扩展接口：
- 培训资料管理模块
- 考核数据统计和报表
- 多语言支持
- 移动端API适配
- 消息通知系统

## 技术特点

- **模块化设计**: 清晰的应用分层，便于维护和扩展
- **智能算法**: 基于用户表现的个性化组卷
- **RESTful API**: 标准化接口设计，便于前端集成
- **数据安全**: 完善的权限控制和数据验证
- **高性能**: 数据库查询优化，支持并发访问